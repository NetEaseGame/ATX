#-*- encoding: utf-8 -*-

import bisect
import cv2
import os
import pickle
import Queue
import sys
import threading
import time
import traceback
import json

from collections import namedtuple

class BaseRecorder(object):

    monitor_period = 3 # seconds

    def __init__(self, device=None, workdir=".", realtime_analyze=False):
        self.device = None
        self.device_info = {}
        self.running = False
        self.setup_workdir(workdir)

        if device is not None:
            self.attach(device)
        self.realtime_analyze = realtime_analyze

        self.thread = None
        self.frames = []  # for backup
        self.last_frame_time = None
        self.case_draft = []  # for analyze draft
        self.input_queue = Queue.Queue()
        self.input_index = 0

        # find addons from base classes
        self.addons = {}
        for cls in self.__class__.__bases__:
            name = getattr(cls, '_%s__addon_name' % (cls.__name__,), None)
            if name is not None:
                gfun = getattr(self, 'get_%s' % (name,))
                sfun = getattr(self, 'save_%s' % (name,))
                lfun = getattr(self, 'load_%s' % (name,))
                self.addons[name] = (gfun, sfun, lfun)

    def setup_workdir(self, workdir):
        # setup direcoties
        self.workdir = workdir

        self.casedir = os.path.join(workdir, 'case')
        if not os.path.exists(self.casedir):
            os.makedirs(self.casedir)

        self.framedir = os.path.join(workdir, 'frames')
        if not os.path.exists(self.framedir):
            os.makedirs(self.framedir)

    def update_device_info(self):
        if self.device is None:
            return
        # TODO: define general device info
        w, h = self.device.display
        self.device_info = {"width":w, "height":h}

    def start(self):
        '''start running in background.'''
        self.update_device_info()
        self.get_device_status(0) # start addons.
        self.hook()
        self.thread = threading.Thread(target=self._run)
        self.thread.start()
        self.running = True

    def stop(self):
        self.unhook()
        self.running = False
        self.thread.join()

    def get_device_status(self, t):
        '''get device status at a given time t (within self.monitor_period)'''
        data = {}
        for name, (func, _, _) in self.addons.iteritems():
            data[name] = func(t)
        return data

    def _run(self):
        while True:
            try:
                time.sleep(0.1)
                frame = self.input_queue.get_nowait()
                self.handle_frame(frame)
            except Queue.Empty:
                if not self.running:
                    break
            except:
                traceback.print_exc()
                self.running = False

        # save meta info for backup & draft.
        if not self.realtime_analyze:
            self.analyze_all()
        self.save()
        print 'recorder stopped.'
        sys.exit()

    def input_event(self, event):
        '''should be called when user input events happens (from hook)'''
        if not self.running or self.device is None:
            return
        # print 'input_event', event.time
        status = self.get_device_status(event.time)
        self.input_queue.put((self.input_index, event, status))
        self.input_index += 1

    def handle_frame(self, frame):
        # print 'handle frame'
        idx, event, status = frame
        meta = {'index':idx}
        meta['event'] = self.serialize_event(event)
        if self.last_frame_time is None:
            meta['waittime'] = 0
        else:
            meta['waittime'] = event.time - self.last_frame_time
        self.last_frame_time = event.time

        # save frames.
        # print 'saving...'
        eventpath = os.path.join(self.framedir, '%d-event.pkl' % idx)
        pickle.dump(event, file(eventpath, 'w'))
        meta['status'] = {}
        for name, obj in status.iteritems():
            func = self.addons[name][1]
            data = func(obj, self.framedir, idx)
            meta['status'][name] = data

        # analyze
        if self.realtime_analyze:
            self.analyze_frame(idx, event, status)
        self.frames.append(meta)

    def serialize_event(self, event):
        return {}

    def analyze_frame(self, idx, event, status):
        '''analyze status and generate draft config'''
        # Example:
        #
        # d = {
        #     'action' : 'click',
        #     'args' : (100, 100),
        #     },
        # }
        # self.case_draft.append(d)
        pass

    def process_draft(self, d):
        '''generate code from draft'''
        raise NotImplementedError()

    def analyze_all(self):
        print 'total frames:', len(self.frames)
        print 'analying, please wait'
        for meta in self.frames:
            idx = meta['index']
            event = pickle.load(file(os.path.join(self.framedir, '%d-event.pkl' % idx)))
            status = meta['status']
            status = {}
            for name, data in meta['status'].iteritems():
                if data is None:
                    status[name] = None
                    continue
                func = self.addons[name][2]
                status[name] = func(self.framedir, data)
            self.analyze_frame(idx, event, status)
            print '\b.',
        print '\nDone'

    @classmethod
    def analyze_frames(cls, workdir):
        '''generate draft from recorded frames'''
        record = cls(None, workdir)
        obj = {}
        with open(os.path.join(workdir, 'frames', 'frames.json')) as f:
            obj = json.load(f)
        record.device_info = obj['device']
        record.frames = obj['frames']
        record.analyze_all()
        record.save()

    @classmethod
    def process_casefile(cls, workdir):
        '''generate code from case.json'''
        record = cls(None, workdir)
        obj = {}
        with open(os.path.join(workdir, 'frames', 'frames.json')) as f:
            obj = json.load(f)
        record.device_info = obj['device']
        record.frames = obj['frames']

        casedir = os.path.join(workdir, 'case')
        with open(os.path.join(casedir, 'case.json')) as f:
            record.case_draft = json.load(f)

        # remove old files
        for f in os.listdir(casedir):
            if f != 'case.json':
                os.remove(os.path.join(casedir, f))

        record.generate_script()

    def save(self):
        # save frames info, do not overwrite.
        filepath = os.path.join(self.framedir, 'frames.json')
        obj = {
            'ctime' : time.ctime(),
            'device' : self.device_info,
            'frames' : self.frames,
        }
        with open(filepath, 'w') as f:
            json.dump(obj, f, indent=2)

        # save draft info
        filepath = os.path.join(self.framedir, 'draft.json')
        with open(filepath, 'w') as f:
            json.dump(self.case_draft, f, indent=2)
        # make a copy at casedir
        filepath = os.path.join(self.casedir, 'case.json')
        with open(filepath, 'w') as f:
            json.dump(self.case_draft, f, indent=2)

        # generate_script
        self.generate_script()

    def generate_script(self):
        # save draft pyscript
        print 'Generating script...'
        filepath = os.path.join(self.casedir, 'script.py')
        content = [
            '#-*- encoding: utf-8 -*-', '# Generated by recorder.',
            '',
            'import time',
            '',
            'def test(d):',
        ]
        for row in self.case_draft:
            script = self.process_draft(row).encode('utf-8', 'ignore')
            for line in script.split('\n'):
                content.append(' '*4 + line)
        content.extend([
            '',
            'if __name__ == "__main__":',
            '   import atx',
            '   d = atx.connect()',
            '   test(d)',
        ])
        with open(filepath, 'w') as f:
            f.write('\n'.join(content))
        print 'Save script to', filepath

    def attach(self, device):
        '''Attach to device, if current device is not None, should
        detach from it first. '''
        raise NotImplementedError()

    def detach(self):
        '''Detach from current device.'''
        raise NotImplementedError()

    def hook(self):
        '''Hook user input.'''
        raise NotImplementedError()

    def unhook(self):
        '''Unhook user input.'''
        raise NotImplementedError()

__CaptureRecord = namedtuple('__CaptureRecord', ('ctime', 'image'))

class CaptureRecord(__CaptureRecord):
    def __eq__(self, other):
        return self[0] == other[0]
    def __ne__(self, other):
        return not self == other
    def __gt__(self, other):
        return self[0] > other[0]
    def __ge__(self, other):
        return not self<other
    def __lt__(self, other):
        return self[0] < other[0]
    def __le__(self, other):
        return not other<self

class ScreenAddon(object):
    __addon_name = 'screen'

    __capture_cache = []
    __capture_interval = 0.1
    __capture_lock = None
    __capture_thread = None

    def get_screen(self, t):
        if self.__capture_thread is None:
            self.__start()
        with self.__capture_lock:
            idx = bisect.bisect(self.__capture_cache, (t, None))
            if idx != 0:
                return self.__capture_cache[idx-1][1]

    def save_screen(self, screen, dirpath, idx):
        if screen is None:
            return
        filename = '%d.png' % idx
        filepath = os.path.join(dirpath, filename)
        cv2.imwrite(filepath, screen)
        return filename

    def load_screen(self, dirpath, filename):
        filepath = os.path.join(dirpath, filename)
        try:
            return cv2.imread(filepath)
        except:
            return

    def __start(self):
        print 'start', self.__addon_name
        if self.__capture_lock is None:
            self.__capture_lock = threading.Lock()
        if self.__capture_thread is not None:
            self.__capture_thread._Thread_stop() # using __stop private method, not good
        self.__capture_thread = t = threading.Thread(target=self.__capture)
        t.setDaemon(True)
        t.start()

    def __capture(self):
        capture_maxnum = int(self.monitor_period/self.__capture_interval)
        while True:
            self.__capture_lock.acquire()
            try:
                time.sleep(self.__capture_interval)
                if not self.running or self.device is None:
                    continue
                # tic = time.time()
                img = self.device.screenshot_cv2()
                # print '--capturing.. cost', time.time() - tic
                self.__capture_cache.append(CaptureRecord(time.time(), img))
                self.__capture_cache = self.__capture_cache[-capture_maxnum:]
            finally:
                self.__capture_lock.release()

class UixmlAddon(object):
    __addon_name = 'uixml'

    __uidump_cache = []
    __uidump_interval = 0.1
    __uidump_lock = None
    __uidump_thread = None

    def get_uixml(self, t):
        if self.__uidump_thread is None:
            self.__start()
        with self.__uidump_lock:
            idx = bisect.bisect(self.__uidump_cache, (t, ''))
            if idx != 0:
                return self.__uidump_cache[idx-1][1]

    def save_uixml(self, uixml, dirpath, idx):
        if uixml is None:
            return
        filename = '%d-uidump.xml' % idx
        filepath = os.path.join(dirpath, filename)
        with open(filepath, 'w') as f:
            f.write(uixml)
        return filename

    def load_uixml(self, dirpath, filename):
        filepath = os.path.join(dirpath, filename)
        try:
            return open(filepath).read()
        except IOError:
            return u''

    def __start(self):
        print 'start', self.__addon_name
        if self.__uidump_lock is None:
            self.__uidump_lock = threading.Lock()
        if self.__uidump_thread is not None:
            self.__uidump_thread._Thread_stop() # using __stop private method, not good
        self.__uidump_thread = t = threading.Thread(target=self.__dump)
        t.setDaemon(True)
        t.start()

    def __dump(self):
        uidump_maxnum = int(self.monitor_period/self.__uidump_interval)
        while True:
            self.__uidump_lock.acquire()
            try:
                time.sleep(self.__uidump_interval)
                if not self.running or self.device is None:
                    continue
                # tic = time.time()
                xmldata = self.device.dumpui()
                xmldata = xmldata.encode('utf-8')
                # print 'dumping ui.. cost', time.time() - tic
                self.__uidump_cache.append((time.time(), xmldata))
                self.__uidump_cache = self.__uidump_cache[-uidump_maxnum:]
            finally:
                self.__uidump_lock.release()


if __name__ == '__main__':

    class TestRecorder(BaseRecorder, ScreenAddon, UixmlAddon):
        def attach(self, device):
            self.device = device
        def detach(self): pass
        def hook(self): pass
        def unhook(self): pass

    class DummyDevice(object):
        def screenshot_cv2(self):
            return None

        def dumpui(self):
            return u'uixml'

    class DummyEvent(object):
        def __init__(self):
            self.time = time.time()

    r = TestRecorder(DummyDevice(), 'testcase')
    r.start()

    count = 10
    while count > 0:
        try:
            time.sleep(1)
            e = DummyEvent()
            r.input_event(e)
        except:
            break
        count -= 1

    r.stop()
