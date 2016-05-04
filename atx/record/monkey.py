#-*- encoding: utf-8 -*-
# I'm Shakespeare!

import re
import cv2
import time
import warnings
import traceback
from random import randint, choice

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

    actions = ('touch', 'swipe', 'pinchin', 'pinchout', 'home', 'menu', 'back')
    delay = 0.5

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

    def run(self, device, package=None, maxruns=None):
        self.device = device
        pids = None
        if package is not None:
            self.device.start_app(package)
            time.sleep(1)
            pids = self.device.get_package_pids(package)

        for reporter in self.reporters:
            reporter.prepare(device, package, pids)

        count = 0
        while maxruns is None or count < maxruns:
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

        func = getattr(self, 'do_%s' % a, None)
        if func is not None:
            func()
        else:
            print 'unknown action', a

    def do_touch(self):
        w, h = self.device.display
        x, y = randint(1, w), randint(1, h)
        self.device.touch(x, y)

    def do_swipe(self):
        w, h = self.device.display
        x1, y1, x2, y2 = randint(1, w), randint(1, h), randint(1, w), randint(1, h)
        self.device.swipe(x1, y1, x2, y2)

    # def do_pinchin(self):
    #     w, h = self.device.display
    #     angle = randint(0, 360)

    # def do_pinchout(self):
    #     w, h = self.device.display
    #     angle = randint(0, 360)

    def do_home(self):
        self.device.home()

    def do_menu(self):
        self.device.menu()

    def do_back(self):
        self.device.back()

class StupidMonkey(Monkey):
    '''find touchables through hard work'''

    movestep = 30 #pixels

    def __init__(self, probs, scene_directory):
        super(StupidMonkey, self).__init__(probs)
        self.scene_detector = SceneDetector(scene_directory)
        self.scene_touches = {}
        self.scene_rects = {}

    def get_current_scene(self):
        screen = self.device.screenshot_cv2()
        h, w = screen.shape[:2]
        img = cv2.resize(screen, (w/2, h/2))
        scene = self.scene_detector.detect(img)

        for rect in self.scene_rects.get(str(scene),{}).itervalues():
            l, t, r, b = rect
            cv2.rectangle(img, (l, t), (r, b), 255, 2)
        cv2.imshow('scene', img)
        cv2.waitKey(1)
        return scene

    def do_touch(self):
        # width, height = self.device.display
        width, height = 1080, 1920
        scene = self.get_current_scene()
        if scene is None:
            # fall back to random point
            x, y = randint(1, width), randint(1, height)
        else:
            pos = self.scene_touches.get(str(scene), 0)
            w, h = width/self.movestep, height/self.movestep # grid points
            dy, dx = divmod(pos, w-1)
            if dy >= h-1:
                # TODO: return a random clickable point
                x, y = randint(1, width), randint(1, height)
            else:
                x, y = (dx+1)*self.movestep, (dy+1)*self.movestep
                self.scene_touches[str(scene)] = pos+1

        self.last_touch_point = x, y
        self.device.touch(x, y)

        # watch what happend after touch
        if scene is None:
            return
        newscene = self.get_current_scene()
        if newscene is None or newscene == scene:
            return
        s1 = str(scene)
        s2 = str(newscene)
        if s1 not in self.scene_rects:
            self.scene_rects[s1] = {}
        if s2 not in self.scene_rects[s1]:
            self.scene_rects[s1][s2] = (x, y, x, y)
        else:
            l, t, r, b = self.scene_rects[s1][s2]
            l, r = min(l, x), max(r, x)
            t, b = min(t, y), max(t, y)
            self.scene_rects[s1][s2] = (l, t, r, b)

    def do_swipe(self):
        pass

class RandomContourMonkey(Monkey):

    def do_touch(self):
        width, height = 1080, 1920

        screen = self.device.screenshot_cv2()
        h, w = screen.shape[:2]
        img = cv2.resize(screen, (w/2, h/2))
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        edges = cv2.Canny(gray, 80, 200)
        _, thresh = cv2.threshold(edges, 0, 255, cv2.THRESH_OTSU)
        contours, _ = cv2.findContours(thresh, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_SIMPLE)
        contours.sort(key=lambda cnt: len(cnt), reverse=True)

        rects = []
        for cnt in contours:
            hull = cv2.convexHull(cnt)
            hull_area = cv2.contourArea(hull)
            x,y,w,h = cv2.boundingRect(cnt)
            rect_area = float(w*h)
            if w<20 or h<20 or rect_area<100:
                continue
            if hull_area/rect_area < 0.50:
                continue
            rects.append((x, y, x+w, y+h))
            cv2.rectangle(img, (x, y), (x+w, y+h), 255, 2)

        if not rects:
            x, y = randint(1, width), randint(1, height)
        else:
            x1, y1, x2, y2 = choice(rects)
            x, y = randint(x1, x2), randint(y1, y2)
            cv2.rectangle(img, (x1, y1), (x2, y2), (0, 255, 0), 2)

        x, y = self.device.screen2touch(x*2, y*2)
        self.device.touch(x, y)
        cv2.imshow('img', img)
        cv2.waitKey(1)

    def do_swipe(self):
        pass

if __name__ == '__main__':
    pass