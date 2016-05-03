#-*- encoding: utf-8 -*-
# I'm Shakespeare!

import re
import cv2
import time
import warnings
import traceback
from random import randint

from scene_detector import SceneDetector

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


class StupidMonkey(Monkey):
    '''find touchables through hard work'''

    movestep = 30 #pixels

    def __init__(self, probs, scene_directory, device=None):
        super(StupidMonkey, self).__init__(probs)
        self.scene_touches = {}
        self.scene_detector = SceneDetector(scene_directory, device)
        self.device = device

    def get_touch_point(self):
        scene = self.scene_detector.detect()
        if scene is None:
            return

        pos = self.scene_touches.get(str(scene), 0)
        # w, h = self.device.display
        w, h = 1080, 1920
        w, h = w/self.movestep, h/self.movestep # grid points
        x, y = divmod(pos, w-1)
        if x >= h-1:
            return

        x, y = (x+1)*self.movestep, (y+1)*self.movestep
        self.scene_touches[str(scene)] = pos+1
        return x, y

    def get_swipe_points(self):
        pass

if __name__ == '__main__':
    from atx.device.android_minicap import AndroidDeviceMinicap
    dev = AndroidDeviceMinicap()
    dev._adb.start_minitouch()
    time.sleep(3)
    probs = {'touch':5, 'swipe':1}
    # m = Monkey(probs)
    # m.run(dev, package='im.yixin', maxruns=100)
    m = StupidMonkey(probs, '../../tests/txxscene', dev)
    old, new = None, None
    while True:
        # time.sleep(0.3)
        screen = m.device.screenshot_cv2()
        h, w = screen.shape[:2]
        img = cv2.resize(screen, (w/2, h/2))

        tic = time.clock()
        new = str(m.scene_detector.detect())
        t = time.clock() - tic
        if new != old:
            print 'change to', new
            print 'cost time', t
        old = new

        if m.cur_rect is not None:
            x, y, x1, y1 = m.cur_rect
            cv2.rectangle(img, (x,y), (x1,y1), (0,255,0) ,2)
        cv2.imshow('test', img)
        cv2.waitKey(1)
