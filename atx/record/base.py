#-*- encoding: utf-8 -*-
#
# BaseRecorder class
# >>> class Recorder(BaseRecorder, xxx): 
# ...     ........
# >>> rec = Recorder()
# >>> rec.attach(SomeDevice())
# >>> rec.set_workdir("~/workdir/record")
# >>> def callback(info):
# ...     print info # dict
# >>> rec.on_process_event_done(callback)
# >>> rec.start(threaded=True)
# >>> rec.stop()

import bisect
import cv2
import os
import pickle
import Queue
import shutil
import threading
import time
import traceback

from collections import namedtuple

class BaseRecorder(object):

    monitor_period = 3 # seconds

    def __init__(self, device=None, workdir="."):
        self.device = None
        self.running = False
        if device is not None:
            self.attach(device)
        self.setup_workdir(workdir)

        self.thread = None
        self.frames = []
        self.input_queue = Queue.Queue()
        self.input_index = 0

        # find addons from base classes
        self.addons = {}
        for cls in self.__class__.__bases__:
            name = getattr(cls, '_%s__addon_name' % (cls.__name__,), None)
            if name is not None:
                gfun = getattr(self, 'get_%s' % (name,))
                sfun = getattr(self, 'save_%s' % (name,))
                self.addons[name] = (gfun, sfun)

    def setup_workdir(self, workdir):
        # setup direcoties
        self.workdir = workdir
        self.draftdir = os.path.join(workdir, 'draft')
        if os.path.exists(self.draftdir):
            shutil.rmtree(self.draftdir)
        os.makedirs(self.draftdir)
        self.backupdir = os.path.join(workdir, 'backup')
        if os.path.exists(self.backupdir):
            shutil.rmtree(self.backupdir)
        os.makedirs(self.backupdir)

    def start(self, threaded=False):
        # start addons.
        self.get_device_status(0)

        self.running = True
        self.hook()
        if threaded:
            self.thread = threading.Thread(target=self._run)
            self.thread.start()
        else:
            self.thread = None
            self._run()
            self.unhook()

    def stop(self):
        self.running = False
        if self.thread:
            self.thread.join()
            self.unhook()

    def get_device_status(self, t):
        '''get device status at a given time t (within self.monitor_period)'''
        data = {}
        for name, (func, _) in self.addons.iteritems():
            data[name] = func(t)
            print name, data[name]
        return data

    def _run(self):
        while True:
            try:
                time.sleep(0.001)
                idx, event, status = self.input_queue.get_nowait()
                # back up
                self.backup_frame(idx, event, status)
                # analyze
                self.analyze(idx, event, status)
            except Queue.Empty:
                if not self.running:
                    break
            except KeyboardInterrupt:
                self.running = False
            except:
                traceback.print_exc()

    def input_event(self, event):
        '''should be called when user input events happens (from hook)'''
        if not self.running or self.device is None:
            return
        print 'input_event', event.time
        status = self.get_device_status(event.time)
        self.input_index += 1
        self.input_queue.put((self.input_index, event, status))

    def backup_frame(self, idx, event, status):
        data = {'index':idx}
        data['event'] = {}
        eventpath = os.path.join(self.backupdir, '%d-event.pkl' % idx)
        pickle.dump(event, file(eventpath, 'w'))
        
        data['status'] = {}
        for name, obj in status.iteritems():
            func = self.addons[name][1]
            filename = func(obj, self.backupdir, idx)
            data['status'][name] = filename

        self.frames.append(data)

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
        filename = '%d.png' % idx
        filepath = os.path.join(dirpath, filename)
        cv2.imwrite(filepath, screen)
        return filename

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
                tic = time.time()
                img = self.device.screenshot_cv2()
                print '--capturing.. cost', time.time() - tic
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
        filename = '%d-uidump.xml' % idx
        filepath = os.path.join(dirpath, filename)
        with open(filepath, 'w') as f:
            f.write(uixml.encode('utf8'))
        return filename

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
                tic = time.time()
                xmldata = self.device.dumpui()
                print 'dumping ui.. cost', time.time() - tic
                self.__uidump_cache.append((time.time(), xmldata))
                self.__uidump_cache = self.__uidump_cache[-uidump_maxnum:]
            finally:
                self.__uidump_lock.release()


if __name__ == '__main__':

    class TestRecorder(BaseRecorder, ScreenAddon, UixmlAddon):
        def attach(self, device): pass
        def detach(self): pass
        def hook(self): pass
        def unhook(self): pass

    r = TestRecorder()
    r.start()