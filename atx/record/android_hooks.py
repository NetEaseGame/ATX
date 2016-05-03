# -*- coding: utf-8 -*-
# An android event hook via getevent.
# Only ABS_MT_POSITION_X(Y) events are handled.
#
# Basic input: TouchDown(D), TouchUp(U), TouchMove(M)
# Basic timeouts: TouchPressTimeout(P), TouchFollowTimeout(F), TouchMoveStopTimeout(S)
# guestures are defined as follows:
#   Tap: DM?UF
#   TapFollow: (DM?U)+DM?UF
#   LongPress: DP, may be followed by Drag or half-Fling
#   Drag: D?M+S, may be followed by Drag or half-Fling
#   Fling: DM+U
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

class HookConstants:
    # basic events
    TOUCH_DOWN = 0x01
    TOUCH_UP   = 0x02
    TOUCH_MOVE = 0x03
    TOUCH_PRESS_TIMEOUT = 0x04
    TOUCH_FOLLOW_TIMEOUT = 0x05
    TOUCH_MOVESTOP_TIMEOUT = 0x06

    KEY_ANY = 0x10
    KEY_HOME_DOWN = 0x11
    KEY_HOME_UP   = 0x12
    KEY_BACK_DOWN = 0x13
    KEY_BACK_UP   = 0x14
    KEY_MENU_DOWN = 0x15
    KEY_MENU_UP   = 0x16
    KEY_POWER_DOWN      = 0x17
    KEY_POWER_UP        = 0x18
    KEY_VOLUMEDOWN_DOWN = 0x19
    KEY_VOLUMEDOWN_UP   = 0x1a
    KEY_VOLUMEUP_DOWN   = 0x1b
    KEY_VOLUMEUP_UP     = 0x1c

    # gestures
    GST_TAP = 0x21
    GST_DOUBLE_TAP = 0x22
    GST_LONG_PRESS = 0x23
    GST_SWIPE = 0x24
    GST_DRAG = 0x25
    GST_PINCH = 0x26

    # maybe used for uiautomator press
    KEY_HOME = 'home'
    KEY_MENU = 'menu'
    KEY_BACK = 'back'
    KEY_POWER      = 'power'
    KEY_VOLUMEDOWN = 'volume_down'
    KEY_VOLUMEUP   = 'volume_up'

class Event(object):
    msg = None
    def __init__(self, time, slotid=None):
        self.time = time
        self.slotid = slotid

class TouchEvent(Event):
    def __init__(self, time, slotid, x, y, pressure, touch_major):
        '''msg: touch_down, touch_up, touch_move'''
        super(TouchEvent, self).__init__(time, slotid)
        self.x = x
        self.y = y
        self.pressure = pressure
        self.touch_major = touch_major

class TouchDownEvent(TouchEvent):
    msg = HookConstants.TOUCH_DOWN

class TouchUpEvent(TouchEvent):
    msg = HookConstants.TOUCH_UP

class TouchMoveEvent(TouchEvent):
    msg = HookConstants.TOUCH_MOVE
    def __init__(self, time, slotid, x, y, pressure, touch_major, distance, direction, speed):
        super(TouchMoveEvent, self).__init__(time, slotid, x, y, pressure, touch_major)
        self.distance = distance
        self.direction = direction
        self.speed = speed

class TouchPressTimeout(Event):
    msg = HookConstants.TOUCH_PRESS_TIMEOUT

class TouchFollowTimeout(Event):
    msg = HookConstants.TOUCH_FOLLOW_TIMEOUT

class TouchMoveStopTimeout(Event):
    msg = HookConstants.TOUCH_MOVESTOP_TIMEOUT

class KeyEvent(Event):
    msg = HookConstants.KEY_ANY
    def __init__(self, time, msg, key):
        '''msg: keydown, keyup'''
        super(KeyEvent, self).__init__(time)
        self.key = key
        self.msg = msg

class GestureEvent(Event):
    msg = None
    def __init__(self, time, endtime, slotid):
        super(GestureEvent, self).__init__(time, slotid)
        self.endtime = endtime

class Tap(GestureEvent):
    msg = HookConstants.GST_TAP

class DoubleTap(GestureEvent):
    msg = HookConstants.GST_DOUBLE_TAP


SLOT_NUM = 5
_X, _Y, _VR, _VA, _MJ, _PR, FIELD_NUM = range(7)
INF = 9999

class InputParser(object):
    _pat = re.compile('\[\s*(?P<time>[0-9.]+)\] (?P<device>/dev/.*): +(?P<type>\w+) +(?P<code>\w+) +(?P<value>\w+)')
    _move_radius = 10

    def __init__(self, queue):
        self.queue = queue
        # the 'standard' status temp_status is compared to. 
        # if changes are great enough, new event are emitted.
        # velocity will be calculated for touch-move events.
        self._status = np.ones((SLOT_NUM, FIELD_NUM), dtype=int) * (-INF)
        self._status_time = 0
        # realtime status, minor changes are cumulated
        self._temp_status = np.ones((SLOT_NUM, FIELD_NUM), dtype=int) * (-INF)
        self._temp_status_time = 0
        # self._trackids = [None] * SLOT_NUM

        self._touch_batch = []
        self._curr_slot = 0

    def feed(self, line):
        # print line
        m = self._pat.search(line)
        if not m:
            return
        _time, _device, _type, _code, _value = m.groups()
        _time = float(_time)
        try:
            _value = int(_value, 16)
        except:
            pass

        if _type == 'EV_SYN':
            if _code in ('SYN_REPORT', 'SYN_MT_REPORT'):
                self._process_touch_batch()
            elif _code == 'SYN_DROPPED':
                self._touch_batch = []
            else:
                print 'unknown syn code', _code
        elif _type == 'EV_KEY':
            self.emit_key_event(_time, _code, _value)
        elif _type == 'EV_ABS':
            self._touch_batch.append((_time, _device, _type, _code, _value))
        else:
            print 'unknown input event type', _type

    def emit_key_event(self, _time, _code, _value):
        name = '%s_%s' % (_code, _value)
        msg = getattr(HookConstants, name, None)
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
                    # self._trackids[self._curr_slot] = None
                    self._temp_status[self._curr_slot] = -INF
                    changed = True
                else:
                    # self._trackids[self._curr_slot] = _value
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
            # trackid = self._trackids[i]
            dx, dy = diff[i,_X], diff[i,_Y]
            if dx > INF or dy > INF:
                # touch begin
                event = TouchDownEvent(_time, i, arr[_X], arr[_Y], arr[_PR], arr[_MJ])
                self.emit_touch_event(event)
                emitted = True
            elif dx < -INF or dy < -INF:
                # touch end
                event = TouchUpEvent(_time, i, oldarr[_X], oldarr[_Y], oldarr[_PR], oldarr[_MJ])
                self.emit_touch_event(event)
                emitted = True
            else:
                r, a = radang(float(dx), float(dy))
                if r > self._move_radius:
                    v = r / dt
                    event = TouchMoveEvent(_time, i, arr[_X], arr[_Y], arr[_PR], arr[_MJ], r, a, v)
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
    move_stop_delay = 0.5
    pinch_difference_square = 3000

    def __init__(self, queue):
        self.queue = queue
        self.dispatch_map = {}
        self.running = False

        # only used in process thread so we don't need a lock
        self.touchdowns = [None]*SLOT_NUM
        self.touchups = [None]*SLOT_NUM
        self.touchmoves = [None]*SLOT_NUM

        # used for recognition
        self.tracks = [[] for i in range(SLOT_NUM)]
        self.track_slots = set()

    def handle_event(self, event):
        print 'handle event', event
        self.dispatch_event(event)
        if event.msg & HookConstants.KEY_ANY: # skip keys
            return
        self.analyze_tracks(event)

    def analyze_tracks(self, e):
        # handle one-finger and two-finger gestures only
        # means a third finger will be ignored even if one of the
        # first two fingers leaves the screen.
        # hint: try it on <Boom Beach>

        HC = HookConstants
        i = e.slotid

        # end guesture when touch up
        if e.msg == HC.TOUCH_UP:
            if not self.tracks[i]:
                return
            self.tracks[i].append(e)
            # self.post_gesture(i, self.tracks[i])
            self.tracks[i] = None
            self.track_slots.discard(i)
        
        # begin guesture when touch down
        elif e.msg == HC.TOUCH_DOWN:
            if len(self.track_slots) == 2:
                return
            self.tracks[i]  = [e]
            self.track_slots.add(i)
            
        # find drag/pan/pinch/swipe guestures
        elif e.msg == HC.TOUCH_MOVE:
            if not self.tracks[i]:
                return
            self.tracks[i].append(e)

            if len(self.track_slots) == 1: # single finger move
                if e.time - self.tracks[i][0].time > 1:
                    print 'drag'
            elif len(self.track_slots) == 2: # two finger move, may be pan/pinch
                t1, t2 = [self.tracks[s] for s in self.track_slots]
                # check for pinch
                if len(t1) + len(t2) < 5:
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

                print dists[::-1]

    def post_gesture(self, slotid, track):
        print slotid, track

    def register(self, keycode, func):
        self.dispatch_map[keycode] = func

    def dispatch_event(self, event):
        func = self.dispatch_map.get(event.msg)
        if not func:
            return
        try:
            func(event)
        except:
            traceback.print_exc()

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
        HC = HookConstants
        timediff = 0
        while True:
            try:
                time.sleep(0.001)
                event = self.queue.get_nowait()
                self.handle_event(event)
                if timediff == 0:
                    timediff = time.time() - event.time
                if event.msg == HC.TOUCH_DOWN:
                    self.touchdowns[event.slotid] = event
                    self.touchups[event.slotid] = None
                elif event.msg == HC.TOUCH_UP:
                    self.touchups[event.slotid] = event
                    self.touchdowns[event.slotid] = None
                elif event.msg == HC.TOUCH_MOVE:
                    self.touchdowns[event.slotid] = None
                    self.touchups[event.slotid] = None
                    self.touchmoves[event.slotid] = event
            except Queue.Empty:
                if not self.running:
                    break
                now = time.time() - timediff
                for i in range(SLOT_NUM):
                    d = self.touchdowns[i]
                    u = self.touchups[i]
                    m = self.touchmoves[i]
                    # long press
                    if d is not None and now - d.time > self.long_press_delay:
                        print i, 'long press!'
                        self.handle_event(TouchPressTimeout(now, i))
                        self.touchdowns[i] = None
                    # double tap
                    if u is not None and now - u.time > self.double_tap_delay:
                        print i, 'double tap timeout!'
                        self.handle_event(TouchFollowTimeout(now, i))
                        self.touchups[i] = None
                    # move stop
                    if m is not None and now - m.time > self.move_stop_delay:
                        print i, 'move stop!'
                        self.handle_event(TouchMoveStopTimeout(now, i))
                        self.touchmoves[i] = None

            except:
                traceback.print_exc()

        print 'process done.'


class AndroidInputHookManager(object):

    def __init__(self, serial=None):
        self._serial = serial
        self._queue = Queue.Queue()
        self._listener = None
        self._parser = InputParser(self._queue)
        self._processor = GestureRecognizer(self._queue)

    def set_serial(self, serial):
        self._serial = serial

    def register(self, keycode, func):
        '''register hook function'''
        self._processor.register(keycode, func)

    def hook(self):
        '''input should be a filelike object.'''
        cmd = ['adb']
        if self._serial:
            cmd.extend(['-s', self._serial])
        cmd.extend(['shell', 'getevent', '-lt'])
        self._listener = p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        self._processor.start()

        def listen():
            while True:
                try:
                    line = p.stdout.readline().strip()
                    if not line:
                        if p.poll() is not None:
                            print 'adb terminated.'
                            self._processor.stop()
                            break
                        continue
                    self._parser.feed(line)
                except KeyboardInterrupt:
                    p.kill()
                except Exception as e:
                    p.kill()
                    print type(e), str(e)

        t = threading.Thread(target=listen)
        t.setDaemon(True)
        t.start()

    def unhook(self):
        if self._listener:
            self._listener.kill()

HookManager = AndroidInputHookManager

if __name__ == '__main__':
    hm = AndroidInputHookManager()
    hm.hook()
    while True:
        try:
            time.sleep(0.1)
        except KeyboardInterrupt:
            break
    hm.unhook()