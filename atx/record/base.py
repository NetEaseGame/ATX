#-*- encoding: utf-8 -*-

import os
import cv2
import time
import bisect
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

__Step = namedtuple('Step', ('index', 'ctime', 'image', 'action', 'args'))
class Step(__Step):
    def to_script(self, timeout, indent=4):
        res = []
        # res.append('if d.exists("%s-target.png", %s):' % (self.index, ceil(timeout)))
        # res.append('%sw.on("%s-action.png", %s).click()' % (' '*indent, self.index, self.args))
        res.append('')

        return '\n'.join(res)

class BaseRecorder(object):

    default_radius = 180
    capture_interval = 0.1
    capture_maxnum = 30 # watch out your memory!
    look_ahead_num = 3 # diff with later screens to find target object 

    def __init__(self, device=None):
        self.steps = []
        self.device = None
        if device is not None:
            self.attach(device)

        self.running = False
        
        self.steps_lock = threading.Lock()
        self.step_index = 0
        self.last_step = None

        self.capture_lock = threading.Lock()
        self.capture_cache = []
        self.capture_tmpdir = os.path.join(os.getcwd(), 'screenshots', time.strftime("%Y%m%d"))
        if not os.path.exists(self.capture_tmpdir):
            os.makedirs(self.capture_tmpdir)

        t = threading.Thread(target=self.async_capture)
        t.setDaemon(True)
        t.start()

    def attach(self, device):
        '''Attach to device, if current device is not None, should
        detach from it first. '''
        raise NotImplementedError()

    def detach(self):
        '''Detach from current device.'''
        raise NotImplementedError()

    def run(self):
        '''Start watching inputs & device screen.'''
        self.hook()
        with self.capture_lock:
            self.running = True

    def hook(self):
        raise NotImplementedError()

    def stop(self):
        '''Stop record.'''
        with self.capture_lock:
            self.running = False
        self.unhook()
        # for test, dump steps when stop
        self.dump()

    def unhook(self):
        raise NotImplementedError()

    def next_index(self):
        with self.steps_lock:
            self.step_index += 1
            return self.step_index

    def on_click(self, position):
        '''Handle touch event.'''
        t = threading.Thread(target=self.__async_handle_touch, args=(position, ))
        t.setDaemon(True)
        t.start()

    on_touch = on_click

    def __async_handle_touch(self, position):
        t = time.time()
        # add a little delay, so we can check the screen after the touch
        time.sleep(self.capture_interval*(self.look_ahead_num+1))
        self.capture_lock.acquire()
        try:
            # trace back a few moments, find a untouched image
            # we're sure all  item[0] won't be same
            idx = bisect.bisect(self.capture_cache, (t, None))
            if idx == 0 or idx == len(self.capture_cache):
                print "no captured screens yet", idx
                return
            # just use two for now. 
            before, after = self.capture_cache[idx-1], self.capture_cache[idx:idx+self.look_ahead_num]
        finally:
            self.capture_lock.release()

        idx = self.next_index()
        t0, img0 = before
        for t1, img1 in after:
            rect = diff_rect(img0, img1, position)
            if rect is not None:
                print idx, "click at", position, 'found rect', rect
                break
        if rect is None:
            rect = self.__get_default_rect(img0.shape[:2], position)
            print idx, "click at", position, 'use default rect', rect

        x0, y0, x1, y1 = rect
        subimg = img0[y0:y1, x0:x1, :]
        filepath = os.path.join(self.capture_tmpdir, "%d-action.png" % idx)
        cv2.imwrite(filepath, subimg)
        # filepath = os.path.join(self.capture_tmpdir, "%d-2.png" % idx)
        # cv2.imwrite(filepath, img1)

        step = Step(idx, t, img0, 'touch', position)
        self.__pack_last_step(step)

    def __pack_last_step(self, step):
        # find target for last step and pack it.
        if not self.last_step:
            self.last_step = step
            return

        last_step = self.last_step
        rect = diff_rect(last_step.image, step.image)
        if rect is None:
            h, w = step.image.shape[:2]
            if step.action == 'touch':
                position = step.args
            else:
                position = w/2, h/2
            rect = self.__get_default_rect((h, w), position)

        x0, y0, x1, y1 = rect
        subimg = step.image[y0:y1, x0:x1, :]
        filepath = os.path.join(self.capture_tmpdir, "%d-target.png" % step.index)
        cv2.imwrite(filepath, subimg)

        timeout = step.ctime - last_step.ctime
        script = last_step.to_script(timeout)
        # save last step
        with self.steps_lock:
            self.steps.append(script)
        self.last_step = step

    def __get_default_rect(self, size, position):
        h, w = size
        x, y = position
        r = self.default_radius
        return (max(x-r,0), max(y-r,0), min(x+r,w), min(y+r,h))

    def on_double_click(self, position):
        '''Handle double click event'''
        print 'on_double_click'

    def on_drag(self, start, end, speed=1):
        '''Handle drag event.'''
        print 'on_drag'

    on_pan = on_drag

    def on_swipe(self, direction, percent=1, speed=1):
        '''Handle swipe event.
        Args:
            direction: up/down/left/right
            percent: swipe speed, 1 - 100
        '''
        print 'on_swipe', direction

    def on_pinch(self, in_or_out, percent=1, speed=1):
        '''Handle pinch event'''

    def on_key(self, key, flags=None):
        '''Handle key(down->up) event.'''
        print 'on_key', key

    def dump(self, filepath=None):
        '''Generate python scripts.'''
        filepath = os.path.join(self.capture_tmpdir, 'steps.py')
        with open(filepath, 'w') as f:
            with self.steps_lock:
                f.write('\n'.join(self.steps))

    def async_capture(self):
        '''Keep capturing device screen. Should run in background
        as a thread.'''
        while True:
            self.capture_lock.acquire()
            try:
                time.sleep(self.capture_interval)
                if not self.running or self.device is None:
                    continue
                img = self.device.screenshot_cv2()
                self.capture_cache.append(CaptureRecord(time.time(), img))

                # TODO: change capture_cache to a loop list
                while len(self.capture_cache) > self.capture_maxnum:
                    _, img = self.capture_cache.pop(0)

            finally:
                self.capture_lock.release()
