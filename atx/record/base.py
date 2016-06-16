#-*- encoding: utf-8 -*-

import os
import cv2
import time
import Queue
import pickle
import bisect
import shutil
import threading
from collections import namedtuple

from atx.imutils import diff_rect

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

class BaseRecorder(object):

    # default_radius = 180
    # capture_interval = 0.1
    # capture_maxnum = 30 # watch out your memory!

    def __init__(self, device=None, workdir="."):
        self.device = None
        self.running = False

        if device is not None:
            # test
            device.screenshot_cv2()
            device.dumpui()
            self.attach(device)

        self.capture_interval = 0.1
        self.capture_maxnum = 30
        self.capture_lock = threading.Lock()
        self.capture_cache = []
        t = threading.Thread(target=self.async_capture)
        t.setDaemon(True)
        t.start()

        self.uidump_interval = 0.1
        self.uidump_maxnum = 30
        self.uidump_lock = threading.Lock()
        self.uidump_cache = []
        t = threading.Thread(target=self.async_uidump)
        t.setDaemon(True)
        t.start()

        self.action_index = 0
        self.actions = Queue.Queue()

        self.draftdir = os.path.join(workdir, 'draft')
        if os.path.exists(self.draftdir):
            shutil.rmtree(self.draftdir)
        os.makedirs(self.draftdir)
        self.backupdir = os.path.join(workdir, 'backup')
        if os.path.exists(self.backupdir):
            shutil.rmtree(self.backupdir)
        os.makedirs(self.backupdir)

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

    def run(self):
        '''Start watching inputs & device screen.'''
        self.hook()
        self.running = True
        self._run()
        self.unhook()
        print 'Over and out.'

    def _run(self):
        while True:
            try:
                time.sleep(0.01)
                idx, event, img, uixml = self.actions.get_nowait()

                # back up
                eventpath = os.path.join(self.backupdir, '%d-event.pkl' % idx)
                pickle.dump(event, file(eventpath, 'w'))
                print 1111, type(img), type(uixml)
                if img is not None:
                    imgpath = os.path.join(self.backupdir, '%d-pre.png' % idx)
                    cv2.imwrite(imgpath, img)
                if uixml is not None:
                    uipath = os.path.join(self.backupdir, '%d-pre-uidump.xml' % idx)
                    with open(uipath, 'w') as f:
                        f.write(uixml.encode('utf8'))

                # analyze
                self.analyze(idx, event, img, uixml)

            except Queue.Empty:
                if not self.running:
                    break
            except KeyboardInterrupt:
                self.running = False

    def analyze(self, idx, event, img, uixml):
        '''should be overridden'''
        pass

    def async_capture(self):
        while True:
            self.capture_lock.acquire()
            try:
                time.sleep(self.capture_interval)
                if not self.running or self.device is None:
                    continue
                tic = time.time()
                img = self.device.screenshot_cv2()
                print '--capturing.. cost', time.time() - tic
                self.capture_cache.append(CaptureRecord(time.time(), img))

                while len(self.capture_cache) > self.capture_maxnum:
                    _, img = self.capture_cache.pop(0)

            finally:
                self.capture_lock.release()

    def async_uidump(self):
        while True:
            self.uidump_lock.acquire()
            try:
                time.sleep(self.uidump_interval)
                if not self.running or self.device is None:
                    continue
                tic = time.time()
                xmldata = self.device.dumpui()
                print 'dumping ui.. cost', time.time() - tic
                self.uidump_cache.append((time.time(), xmldata))

                while len(self.uidump_cache) > self.uidump_maxnum:
                    self.uidump_cache.pop(0)

            finally:
                self.uidump_lock.release()

    def on_input_event(self, event):
        '''should be called when user input events happens (from hooks)'''
        if not self.running or self.device is None:
            return
        print 'on_input_event', event.time
        img = self.get_capture(event.time)
        uixml = self.get_uixml(event.time)
        self.action_index += 1
        self.actions.put((self.action_index, event, img, uixml))

    def get_capture(self, t):
        with self.capture_lock:
            idx = bisect.bisect(self.capture_cache, (t, None))
            if idx != 0:
                return self.capture_cache[idx-1][1]

    def get_uixml(self, t):
        with self.uidump_lock:
            idx = bisect.bisect(self.uidump_cache, (t, ''))
            if idx != 0:
                return self.uidump_cache[idx-1][1]