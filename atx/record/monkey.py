#-*- encoding: utf-8 -*-
# I'm Shakespeare!

import os
import re
import time
import warnings
import traceback
from random import randint

class Reporter(object):

    def prepare(self, device, package=None, pids=None):
        '''called before loop. initialize device related stuff.'''
        raise NotImplementedError()

    def collect(self):
        '''called every run. collect logs.'''
        raise NotImplementedError()

    def dump(self):
        '''called after loop. dump logs.'''
        raise NotImplementedError()

class AdbLineReporter(Reporter):

    name = 'shell'
    filter_by = None

    def __init__(self):
        self.buffer = []
        # cache grep condition
        self.package = None
        self.pids = None
        self.grep = None
        self.prepared = False

    def prepare(self, device, package=None, pids=None):
        self.device = device
        self.package = package
        self.pids = pids
        if self.filter_by == 'package' and package is not None:
            self.grep = re.compile('%s' % package) # there may be dot in package name but that's ok. 
        elif self.filter_by == 'pids' and pids is not None:
            self.grep = re.compile('|'.join([str(p) for p in pids]))
        self.prepared = True

    def collect(self):
        if not self.prepared:
            return
        cmd = self.command()
        lines = self.device.adb_shell(cmd).split('\n')
        # print cmd, len(lines), lines[0]
        for line in lines:
            line = line.strip()
            if not line:
                continue
            if self.grep is not None and self.grep.search(line) is None:
                continue
            self.process_line(line)
            self.buffer.append(line)

    def process_line(self, line):
        pass

    def dump(self):
        if not self.buffer:
            print 'nothing to dump'
            return
        filename =  '%s_%s.log' % (self.name, time.strftime('%m%d_%H%M%S'))
        if self.package is not None:
            filename = '%s_%s' % (self.package, filename)
        print 'dump report to', filename
        with open(filename, 'w') as f:
            f.write('\n'.join(self.buffer))

class LogcatReporter(AdbLineReporter):

    name = 'logcat'
    timefmt = '%m-%d %H:%M:%S.0'
    timepat = re.compile('\d\d-\d\d\s+\d\d:\d\d:\d\d\.\d+')
    filter_by = 'pids'

    def __init__(self):
        super(LogcatReporter, self).__init__()
        self.timestr = time.strftime(self.timefmt, time.localtime())

    def prepare(self, device, package=None, pids=None):
        super(LogcatReporter, self).prepare(device, package, pids)
        self.device.adb_shell('logcat -c')

    def command(self):
        return "logcat -t '%s' -v time" % self.timestr

    def process_line(self, line):
        m = self.timepat.search(line)
        if m:
            self.timestr = m.group()
        # TODO
        # the last digits should be increased by 1,
        # or there will be some duplicated lines.

# TODO: clean anr/traces.txt on non-root devices.
class AnrTraceReporter(AdbLineReporter):
    name = 'anr'

    def command(self):
        return 'cat /data/anr/traces.txt'

_default_reporters = (LogcatReporter,)

class Monkey(object):

    actions = ('touch', 'swipe', 'pinchin', 'pinchout', 'drag', 'home', 'menu', 'back')
    delay = 0.2

    def __init__(self, probs):
        total = sum(probs.values())
        self.weights = []
        accum = 0
        for i in range(len(self.actions)):
            a = self.actions[i]
            w = probs.pop(a, 0)
            self.weights.append(int(accum*10000./total))
            accum += w
        self.weights.append(int(accum*10000./total))
        if probs:
            warnings.warn('Unsupported actions: %s' % probs.keys())

        self.device = None
        self.reporters = [r() for r in _default_reporters]

    def run(self, device, package=None, maxruns=100):
        self.device = device
        pids = None
        if package is not None:
            self.device.start_app(package)
            time.sleep(1)
            pids = self.device.get_package_pids(package)

        for reporter in self.reporters:
            reporter.prepare(device, package, pids)

        count = 0
        while count < maxruns:
            try:
                time.sleep(self.delay)
                self.next_action()
                for reporter in self.reporters:
                    reporter.collect()
            except KeyboardInterrupt:
                break
            except:
                traceback.print_exc()
            count += 1

        for reporter in self.reporters:
            reporter.dump()

    def next_action(self):
        r = randint(1, 10000)
        for i in range(len(self.actions)-1):
            if r <= self.weights[i+1]:
                break
        a = self.actions[i]
        print a

        if a == 'touch':
            pos = self.get_touch_point()
            if not pos:
                return
            x, y = pos
            self.device.touch(x, y)
        elif a == 'swipe':
            poses = self.get_swipe_points()
            if not poses:
                return
            x1, y1, x2, y2 = poses
            self.device.swipe(x1, y1, x2, y2)
        else:
            print 'unknown action', a

    def get_touch_point(self):
        w, h = self.device.display
        x, y = randint(1, w), randint(1, h)
        return x, y

    def get_swipe_points(self):
        w, h = self.device.display
        x1, y1, x2, y2 = randint(1, w), randint(1, h), randint(1, w), randint(1, h)
        return x1, y1, x2, y2

def is_similar(img1, img2):
    if img1.shape != img2.shape:
        return False
    diff = cv2.absdiff(img1, img2)
    return True

class StupidMonkey(Monkey):
    '''find touchables through hard work'''

    movestep = 10 #pixels

    def __init__(self, probs):
        super(StupidMonkey, self).__init__(probs)
        self.scenes = []
        self.scene_touches = {}

    def dectect_scene(self):
        # return 0
        screen = self.devices.screenshot_cv2
        i = 0
        for scene in self.scenes:
            if is_similar(screen, scene):
                return i
            i += 1
        self.scenes.append(screen)
        return len(self.scenes)-1

    def get_touch_point(self):
        i = self.dectect_scene()
        pos = self.scene_touches.get(i, 0)
        w, h = self.device.display
        # w, h = 1920, 1080
        w, h = w/self.movestep, h/self.movestep # grid points
        y, x = divmod(pos, w-1)
        if y >= h-1:
            return

        x, y = (x+1)*self.movestep, (y+1)*self.movestep
        self.scene_touches[i] = pos+1
        return x, y

    def get_swipe_points(self):
        pass

def test_grid():
    m = StupidMonkey({'touch':10})
    poss = []
    while True:
        pos = m.get_touch_point()
        if not pos:
            break
        poss.append(pos)
    print 'grid point count:', len(poss)

    import cv2
    import numpy
    img = numpy.zeros((1920, 1080))
    for x,y in poss:
        img[x,y] = 255
    img = cv2.resize(img, (540, 960))
    cv2.imshow('grid', img)
    cv2.waitKey()

if __name__ == '__main__':
    from atx.device.android_minicap import AndroidDeviceMinicap
    dev = AndroidDeviceMinicap()
    dev._adb.start_minitouch()
    probs = {'touch':5, 'swipe':1}
    m = Monkey(probs)
    m.run(dev, package='com.netease.testease', maxruns=10000)
    # test_grid()


