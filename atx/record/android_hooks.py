# -*- coding: utf-8 -*-
# An android event hook via getevent.
# Only ABS_MT_POSITION_X(Y) events are handled.
#
# Basic input: TouchDown(D), TouchUp(U), TouchMove(M)
# Basic timeouts: TouchPressTimeout(P), TouchFollowTimeout(F), TouchMoveStopTimeout(S)
# guestures are defined as follows:
#   Tap/Touch/Click: DM?UF
#   TapFollow: (DM?U)+DM?UF
#   LongPress: DP, may be followed by Drag or Swipe
#   Drag: D?M+S, may be followed by Drag or Swipe
#   Swipe/Fling: D?M+U, difference with `Drag` is that `TouchMoveStopTimeout` cannot be fired.
#   2-Finger-Pinch: distance changing
#   2-Finger-Drag: distance hold while moving
# where '?' after M means a little movement and '+' means a large one.
# other guestures are ignored.

import re
import math
import time
import numpy as np
import subprocess
import threading
import Queue
import traceback

__all__ = ['AndroidInputHookManager', 'HookManager', 'HookConstants']

# global, max MultiTap count. Set to 1 to disable MultiTap, 0 for infinite.
_MULTI_TAP_NUM = 3

def set_multitap(count):
    if count < 0:
        print 'Cannot set to negative count.'
        return
    global _MULTI_TAP_NUM
    _MULTI_TAP_NUM = int(count)

class HookConstants:
    # basic events
    TOUCH_ANY  = 1 << 3
    TOUCH_DOWN = 1 << 3 ^ 1
    TOUCH_UP   = 1 << 3 ^ 2
    TOUCH_MOVE = 1 << 3 ^ 3
    # only used for gesture analyze
    TOUCH_PRESS_TIMEOUT     = 1 << 3 ^ 4
    TOUCH_FOLLOW_TIMEOUT    = 1 << 3 ^ 5
    TOUCH_MOVESTOP_TIMEOUT  = 1 << 3 ^ 6

    # DOWN is odd, UP is even & DONW + 1 == UP
    KEY_ANY = 1 << 4
    KEY_HOME_DOWN = 1 << 4 ^ 1
    KEY_HOME_UP   = 1 << 4 ^ 2
    KEY_BACK_DOWN = 1 << 4 ^ 3
    KEY_BACK_UP   = 1 << 4 ^ 4
    KEY_MENU_DOWN = 1 << 4 ^ 5
    KEY_MENU_UP   = 1 << 4 ^ 6
    KEY_POWER_DOWN      = 1 << 4 ^ 7
    KEY_POWER_UP        = 1 << 4 ^ 8
    KEY_VOLUMEDOWN_DOWN = 1 << 4 ^ 9
    KEY_VOLUMEDOWN_UP   = 1 << 4 ^ 10
    KEY_VOLUMEUP_DOWN   = 1 << 4 ^ 11
    KEY_VOLUMEUP_UP     = 1 << 4 ^ 12

    # gestures
    GST_TAP         = 1 << 5 ^ 1
    GST_MULTI_TAP   = 1 << 5 ^ 2
    GST_LONG_PRESS  = 1 << 5 ^ 3
    GST_LONG_PRESS_RELEASE = 1 << 5 ^ 4
    GST_DRAG        = 1 << 5 ^ 5
    GST_SWIPE       = 1 << 5 ^ 6
    GST_PINCH_IN    = 1 << 5 ^ 7
    GST_PINCH_OUT   = 1 << 5 ^ 8

HC = HookConstants

HCREPR = {
    HC.TOUCH_DOWN : 'D',
    HC.TOUCH_UP   : 'U',
    HC.TOUCH_MOVE : 'M',
    HC.TOUCH_PRESS_TIMEOUT     : 'P',
    HC.TOUCH_FOLLOW_TIMEOUT    : 'F',
    HC.TOUCH_MOVESTOP_TIMEOUT  : 'S',
    HC.GST_TAP: 'Tap',
    HC.GST_MULTI_TAP: 'MultiTap',
    HC.GST_LONG_PRESS: 'LongPress',
    HC.GST_LONG_PRESS_RELEASE: 'PressRelease',
    HC.GST_DRAG: 'Drag',
    HC.GST_SWIPE: 'Swipe',
    HC.GST_PINCH_IN: 'PinchIn',
    HC.GST_PINCH_OUT: 'PinchOut',
}

class Event(object):
    def __init__(self, time, msg):
        self.time = time
        self.msg = msg

    def __str__(self):
        return '%s_%s' % (self.__class__.__name__, HCREPR.get(self.msg, self.msg))

    def __repr__(self):
        return '%s(%s)' % (self.__class__.__name__,
            ', '.join(['%s=%s' % (k, v) for k, v in self.__dict__.iteritems()]))

class KeyEvent(Event):
    def __init__(self, time, msg, key):
        super(KeyEvent, self).__init__(time, msg)
        # convert to KEYCODE_xxx for 'adb input keyevent xxx'
        if key.startswith('KEY_'):
            key = 'KEYCODE_' + key[4:]
        self.key = key

class TouchEvent(Event):
    def __init__(self, time, msg, slotid, x, y, pressure, touch_major, **extra):
        super(TouchEvent, self).__init__(time, msg)
        self.slotid = slotid
        self.x = x
        self.y = y
        self.pressure = pressure
        self.touch_major = touch_major
        self.__dict__.update(extra)

class TouchTimeoutEvent(Event):
    def __init__(self, time, msg, slotid):
        super(TouchTimeoutEvent, self).__init__(time, msg)
        self.slotid = slotid

class GestureEvent(Event):
    def __init__(self, msg, track):
        # suffixes: s for start, e for end.
        # two-finger guestures need two tracks
        if msg in (HC.GST_PINCH_IN, HC.GST_PINCH_OUT):
            t1, t2 = track[0], track[1]
            ts = min(t1[0].time, t2[0].time)
            te = max(t1[-1].time, t2[-1].time)
        else:
            es, ee = track[0], track[-1]
            ts, te = track[0].time, track[-1].time
            print 'Gesture', HCREPR.get(msg, msg), ''.join([HCREPR.get(e.msg, e.msg) for e in track]), (es.x, es.y), (ee.x, ee.y)
            if msg in (HC.GST_SWIPE, HC.GST_DRAG):
                # TODO: check for corners for complicated trace
                self.points = [(es.x, es.y), (ee.x, ee.y)]
            else:
                self.points = [(es.x, es.y), (ee.x, ee.y)]

        super(GestureEvent, self).__init__(ts, msg)
        self.duration = te - ts

SLOT_NUM = 5
_X, _Y, _VR, _VA, _MJ, _PR, FIELD_NUM = range(7)
INF = 9999

class InputParser(object):
    _pat = re.compile('\[\s*(?P<time>[0-9.]+)\] (?P<device>/dev/.*): +(?P<type>\w+) +(?P<code>\w+) +(?P<value>\w+)')
    _move_radius = 10

    def __init__(self, queue):
        self.timediff = None
        self.queue = queue
        # the 'standard' status temp_status is compared to.
        # if changes are great enough, new event are emitted.
        # velocity will be calculated for touch-move events.
        self._status = np.ones((SLOT_NUM, FIELD_NUM), dtype=int) * (-INF)
        self._status_time = 0
        # realtime status, minor changes are cumulated
        self._temp_status = np.ones((SLOT_NUM, FIELD_NUM), dtype=int) * (-INF)
        self._temp_status_time = 0

        self._touch_batch = []
        self._curr_slot = 0

    def feed(self, line):
        # print line
        m = self._pat.search(line)
        if not m:
            return
        _time, _device, _type, _code, _value = m.groups()
        _time = float(_time)
        if self.timediff is None:
            self.timediff = time.time() - _time
        _time = self.timediff + _time
        try:
            _value = int(_value, 16)
        except:
            pass

        if _type == 'EV_SYN':
            if _code in ('SYN_REPORT', 'SYN_MT_REPORT'):
                try:
                    self._process_touch_batch()
                except IndexError: # there might be a 6th finger, ignore that.
                    self._touch_batch = []
            elif _code == 'SYN_DROPPED':
                self._touch_batch = []
            else:
                # print 'unknown syn code', _code
                pass
        elif _type == 'EV_KEY':
            self.emit_key_event(_time, _code, _value)
        elif _type == 'EV_ABS':
            self._touch_batch.append((_time, _device, _type, _code, _value))
        else:
            # print 'unknown input event type', _type
            pass

    def emit_key_event(self, _time, _code, _value):
        name = '%s_%s' % (_code, _value)
        msg = getattr(HC, name, None)
        if msg is None:
            return
        event = KeyEvent(_time, msg, _code)
        self.queue.put(event)

    def emit_touch_event(self, event):
        self.queue.put(event)

    def _process_touch_batch(self):
        '''a batch syncs in about 0.001 seconds.'''
        if not self._touch_batch:
            return

        _time = self._temp_status_time
        changed = False

        for (_time, _device, _type, _code, _value) in self._touch_batch:
            if _code == 'ABS_MT_TRACKING_ID':
                if _value == 0xffffffff:
                    self._temp_status[self._curr_slot] = -INF
                    changed = True
                else:
                    pass
            elif _code == 'ABS_MT_SLOT':
                self._curr_slot = _value
            else:
                if _code == 'ABS_MT_POSITION_X':
                    self._temp_status[self._curr_slot,_X] = _value
                    changed = True
                elif _code == 'ABS_MT_POSITION_Y':
                    self._temp_status[self._curr_slot,_Y] = _value
                    changed = True
                elif _code == 'ABS_MT_PRESSURE':
                    self._temp_status[self._curr_slot,_PR] = _value
                elif _code == 'ABS_MT_TOUCH_MAJOR':
                    self._temp_status[self._curr_slot,_MJ] = _value
                else:
                    print 'Unknown code', _code

        self._temp_status_time = _time
        self._touch_batch = []
        if not changed:
            return

        # check differences, if position changes are big enough then emit events
        diff = self._temp_status - self._status
        dt = self._temp_status_time - self._status_time
        emitted = False
        for i in range(SLOT_NUM):
            arr = self._temp_status[i]
            oldarr = self._status[i]
            dx, dy = diff[i,_X], diff[i,_Y]
            if dx > INF or dy > INF:
                # touch begin
                event = TouchEvent(_time, HC.TOUCH_DOWN, i, arr[_X], arr[_Y], arr[_PR], arr[_MJ])
                self.emit_touch_event(event)
                emitted = True
            elif dx < -INF or dy < -INF:
                # touch end
                event = TouchEvent(_time, HC.TOUCH_UP, i, oldarr[_X], oldarr[_Y], oldarr[_PR], oldarr[_MJ])
                self.emit_touch_event(event)
                emitted = True
            else:
                r, a = radang(float(dx), float(dy))
                if r > self._move_radius:
                    v = r / dt
                    event = TouchEvent(_time, HC.TOUCH_MOVE, i, arr[_X], arr[_Y], arr[_PR], arr[_MJ], angle=a, velocity=v)
                    self.emit_touch_event(event)
                    emitted = True

        if not emitted:
            return
        self._status = self._temp_status.copy()
        self._status_time = self._temp_status_time

def radang(x, y):
    '''return (radius, angle) of a vector(x, y)'''
    if x == 0:
        if y == 0:
            return 0, 0
        return abs(y), 90+180*(y<0)
    if y == 0:
        return abs(x), 180*(x<0)

    r = math.sqrt(x*x+y*y)
    a = math.degrees(math.atan(y/x))
    if x < 0:
        a += 180
    elif y < 0:
        a += 360
    return r, a

class GestureRecognizer(object):

    double_tap_delay = 0.5
    long_press_delay = 1
    move_stop_delay = 0.2
    pinch_difference_square = 3000

    def __init__(self, queue):
        self.queue = queue
        self.dispatch_map = {}
        self.running = False

        self.touches = [None] * SLOT_NUM

        # used for recognition
        self.tracks = [None for i in range(SLOT_NUM)]
        self.track_slots = set()

    def register(self, keycode, func):
        self.dispatch_map[keycode] = func

    def start(self):
        if self.running:
            return
        self.running = True
        t = threading.Thread(target=self.process)
        t.setDaemon(True)
        t.start()

    def stop(self):
        self.running = False

    def process(self):
        '''handle events and trigger time-related events'''
        timediff = 0
        while True:
            try:
                time.sleep(0.001)
                event = self.queue.get_nowait()
                self.handle_event(event)
                if event.msg & HC.KEY_ANY:
                    continue
                if timediff == 0:
                    timediff = time.time() - event.time
                self.touches[event.slotid] = event
            except Queue.Empty:
                if not self.running:
                    break
                now = time.time() - timediff
                for i in range(SLOT_NUM):
                    e = self.touches[i]
                    if e is None:
                        continue
                    if e.msg == HC.TOUCH_DOWN and now - e.time > self.long_press_delay:
                        self.analyze_tracks(TouchTimeoutEvent(now, HC.TOUCH_PRESS_TIMEOUT, i))
                        self.touches[i] = None
                    elif e.msg == HC.TOUCH_UP and now - e.time > self.double_tap_delay:
                        self.analyze_tracks(TouchTimeoutEvent(now, HC.TOUCH_FOLLOW_TIMEOUT, i))
                        self.touches[i] = None
                    elif e.msg == HC.TOUCH_MOVE and now - e.time > self.move_stop_delay:
                        self.analyze_tracks(TouchTimeoutEvent(now, HC.TOUCH_MOVESTOP_TIMEOUT, i))
                        self.touches[i] = None
            except:
                traceback.print_exc()

        print 'process done.'

    def handle_event(self, event):
        self.dispatch_event(event.msg, event)
        if event.msg & HC.KEY_ANY:
            self.dispatch_event(HC.KEY_ANY, event)
        else:
            self.dispatch_event(HC.TOUCH_ANY, event)
            self.analyze_tracks(event)

    def dispatch_event(self, msg, event):
        func = self.dispatch_map.get(msg)
        if func is None:
            return
        try:
            func(event)
        except:
            traceback.print_exc()

    def analyze_tracks(self, event):
        pass

    def handle_gesture(self, msg, tracks):
        event = GestureEvent(msg, tracks)
        func = self.dispatch_map.get(msg)
        if func is None:
            return
        try:
            func(event)
        except:
            traceback.print_exc()

## NOT COMPLEMENTED ##
class SimpleGestureRecognizer(GestureRecognizer):

    N_FINGER = 2

    def analyze_tracks(self, event):
        # handle one-finger and two-finger gestures only
        # means a third finger will be ignored even if one of the
        # first two fingers leaves the screen.
        i = event.slotid

        # begin guesture when touch down
        if event.msg == HC.TOUCH_DOWN:
            if len(self.track_slots) == self.N_FINGER and i not in self.track_slots:
                return
            if self.tracks[i] is None:
                self.tracks[i] = []
                self.track_slots.add(i)
            self.tracks[i].append(event)
            return

        if self.tracks[i] is None:
            return

        if event.msg == HC.TOUCH_FOLLOW_TIMEOUT:
            self.tracks[i] = []
        elif event.msg == HC.TOUCH_PRESS_TIMEOUT:
            # print ''.join([HCREPR.get(e.msg) for e in self.tracks[i]]), 'long press'
            self.tracks[i] = []
        elif event.msg == HC.TOUCH_MOVESTOP_TIMEOUT:
            # print ''.join([HCREPR.get(e.msg) for e in self.tracks[i]]), 'drag'
            self.tracks[i] = []
            if len(self.track_slots) == 2:
                for s in self.track_slots:
                    print s, ''.join([HCREPR.get(e.msg) for e in self.tracks[s]])
                print
        elif event.msg == HC.TOUCH_UP:
            self.tracks[i].append(event)
            if len(self.track_slots) == 2:
                for s in self.track_slots:
                    print s, ''.join([HCREPR.get(e.msg) for e in self.tracks[s]])
                print
            self.tracks[i] = None
            self.track_slots.discard(i)
        else: # TOUCH_MOVE
            self.tracks[i].append(event)
            return

            # check for pinch/pan
            if len(self.track_slots) == 2:
                t1, t2 = [self.tracks[s] for s in self.track_slots]
                if len(t1) == 0 or len(t2) == 0 or len(t1) + len(t2) < 6:
                    return
                # make copy and check distance changing
                t1, t2 = t1[:], t2[:]
                dists = []
                while len(dists) < 5:
                    e1, e2 = t1[-1], t2[-1]
                    dx, dy = e1.x-e2.x, e1.y-e2.y
                    dists.append(dx*dx+dy*dy)
                    if e1.time < e2.time:
                        if len(t2) == 1:
                            break
                        else:
                            t2.pop()
                    else:
                        if len(t1) == 1:
                            break
                        else:
                            t1.pop()
                print [dists[j+1]-dists[j] for j in range(len(dists)-1)]
                # just keep latest position
                for s in self.track_slots:
                    self.tracks[s] = self.tracks[s][-1:]

class RegexpGestureRecognizer(GestureRecognizer):

    N_FINGER = 1

    def analyze_tracks(self, event):
        # handle one-finger gestures only
        i = event.slotid

        # begin guesture when touch down
        if event.msg == HC.TOUCH_DOWN:
            if len(self.track_slots) == self.N_FINGER and i not in self.track_slots:
                return
            if not self.tracks[i]:
                self.tracks[i] = []
                self.track_slots.add(i)
            self.tracks[i].append(event)
            return

        if self.tracks[i] is None:
            return

        s = ''.join([HCREPR.get(e.msg) for e in self.tracks[i]])

        if event.msg == HC.TOUCH_FOLLOW_TIMEOUT:
            if re.match('^DM?U$', s):
                self.handle_gesture(HC.GST_TAP, self.tracks[i][:])
            elif re.match('^(DM?U)+DM?U$', s):
                self.handle_gesture(HC.GST_MULTI_TAP, self.tracks[i][:])
            self.tracks[i] = None
            self.track_slots.discard(i)
        elif event.msg == HC.TOUCH_MOVESTOP_TIMEOUT:
            if re.match('^D?MM+$', s):
                self.handle_gesture(HC.GST_DRAG, self.tracks[i][:])
            self.tracks[i] = []
        elif event.msg == HC.TOUCH_PRESS_TIMEOUT:
            if s == 'D':
                self.handle_gesture(HC.GST_LONG_PRESS, self.tracks[i][:])
            self.tracks[i] = []
        elif event.msg == HC.TOUCH_UP:
            self.tracks[i].append(event) # note: it's not the same with s after add
            if s == '':
                self.handle_gesture(HC.GST_LONG_PRESS_RELEASE, [event])
            elif re.match('^D?MM+$', s):
                self.handle_gesture(HC.GST_SWIPE, self.tracks[i][:])
                self.tracks[i] = []
            elif _MULTI_TAP_NUM == 1 and re.match('^DM?$', s):
                self.handle_gesture(HC.GST_TAP, self.tracks[i][:])
                self.tracks[i] = []
            elif _MULTI_TAP_NUM > 1 and re.match('^(DM?U){%d}DM?$' % (_MULTI_TAP_NUM-1,), s):
                self.handle_gesture(HC.GST_MULTI_TAP, self.tracks[i][:])
                self.tracks[i] = []
        elif event.msg == HC.TOUCH_MOVE:
            if re.match('^(DU)+D$', s):
                if s == 'DUD':
                    self.handle_gesture(HC.GST_TAP, self.tracks[i][:-1])
                else:
                    self.handle_gesture(HC.GST_MULTI_TAP, self.tracks[i][:-1])
                self.tracks[i] = self.tracks[i][-1:]
            self.tracks[i].append(event)

NOTACTIVE, ACTIVE, STAGE_1, STAGE_2, TRIGGERED = range(5)

## NOT COMPLEMENTED ##
class StateMachineGestureRecognizer(GestureRecognizer):

    state_map = {
        HC.GST_TAP: {
            NOTACTIVE: { HC.TOUCH_DOWN : ACTIVE },
            ACTIVE: {
                HC.TOUCH_MOVE: STAGE_1,
                HC.TOUCH_PRESS_TIMEOUT : NOTACTIVE,
                HC.TOUCH_FOLLOW_TIMEOUT : TRIGGERED,
            },
            STAGE_1: {
                HC.TOUCH_MOVE: NOTACTIVE,
                HC.TOUCH_PRESS_TIMEOUT : NOTACTIVE,
                HC.TOUCH_FOLLOW_TIMEOUT : TRIGGERED,
            }
        },
        HC.GST_SWIPE: {
            NOTACTIVE: { HC.TOUCH_DOWN: ACTIVE },
            ACTIVE: { HC.TOUCH_UP: NOTACTIVE, HC.TOUCH_MOVE: STAGE_1},
            STAGE_1: { HC.TOUCH_UP: NOTACTIVE, HC.TOUCH_MOVE: STAGE_2 },
            STAGE_2: { HC.TOUCH_UP: TRIGGERED, HC.TOUCH_MOVESTOP_TIMEOUT: TRIGGERED},
        },
    }

    def __init__(self, queue):
        super(self.__class__, self).__init__(queue)
        self.state = {}
        for k in self.state_map:
            self.state[k] = NOTACTIVE
        print self.state_map

    def analyze_tracks(self, event):
        for k, v in self.state.iteritems():
            s = self.state_map.get(k, {}).get(v, {}).get(event.msg)
            if s is not None:
                self.state[k] = s
        triggered = False
        for k, v in self.state.iteritems():
            if v == TRIGGERED:
                print 'trigger event', k
                triggered = True
        if triggered:
            for k in self.state:
                self.state[k] = NOTACTIVE

class AndroidInputHookManager(object):

    def __init__(self, serial=None, processor_class=RegexpGestureRecognizer):
        self._serial = serial
        self.running = False
        self._queue = Queue.Queue()
        self._listener = None
        self._parser = InputParser(self._queue)
        self._processor = processor_class(self._queue)

    def set_serial(self, serial):
        self._serial = serial

    def register(self, keycode, func):
        '''register hook function'''
        self._processor.register(keycode, func)

    def hook(self):
        self._processor.start()
        self.running = True
        t = threading.Thread(target=self._run_hook)
        t.setDaemon(True)
        t.start()

    def _run_hook(self):
        cmd = ['adb']
        if self._serial:
            cmd.extend(['-s', self._serial])
        cmd.extend(['shell', 'getevent', '-lt'])

        while True:
            # start listener
            self._listener = p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            while True:
                try:
                    line = p.stdout.readline().strip()
                    if not line:
                        if p.poll() is not None:
                            break
                        continue
                    self._parser.feed(line)
                except KeyboardInterrupt:
                    p.kill()
                except:
                    p.kill()
                    traceback.print_exc()

            if not self.running:
                break
            state = subprocess.check_output(['adb', '-s', self._serial, 'get-state']).strip()
            if state != 'device':
                print 'adb status(%s) wrong! stop hook.' % (state,)
                break
            print 'adb getevent died, reconnecting...'
            time.sleep(1)

    def unhook(self):
        self.running = False
        self._processor.stop()
        if self._listener:
            self._listener.kill()

HookManager = AndroidInputHookManager

if __name__ == '__main__':
    hm = AndroidInputHookManager(processor_class=RegexpGestureRecognizer)
    hm.hook()
    while True:
        try:
            time.sleep(0.1)
        except KeyboardInterrupt:
            break
    hm.unhook()
