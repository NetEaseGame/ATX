# -*- coding: utf-8 -*-
# An android event hook via getevent.
# Only ABS_MT_POSITION_X(Y) events are handled.

import re
import math
import time
import numpy as np
import subprocess
import threading
import Queue

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
                pass
            else:
                pass
        elif _type == 'EV_KEY':
            pass
        elif _type == 'EV_ABS':
            self._touch_batch.append((_time, _device, _type, _code, _value))
        else:
            pass

    def emit_key_event(self, event):
        self.queue.put('key event %s' % event)

    def emit_touch_events(self, events):
        self.queue.put('multi touch events %s' % events)

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
                    # new touch. there will be POSITION_X(Y) in the batch
                    # so we handle the changes there.
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
        events = [None] * SLOT_NUM
        touchmoves = [None] * SLOT_NUM
        for i in range(SLOT_NUM):
            dx, dy = diff[i,_X], diff[i,_Y]
            if dx > INF or dy > INF:
                # touch begin
                events[i] = ('touch-down', self._temp_status[i,_X], self._temp_status[i,_Y])
            elif dx < -INF or dy < -INF:
                # touch end
                events[i] = ('touch-up', self._status[i,_X], self._status[i,_Y])
            else:
                r, a = radang(float(dx), float(dy))
                v = r / dt
                touchmoves[i] = (a, r, v, self._temp_status[i,_X], self._temp_status[i,_Y])
                if r > self._move_radius:
                    events[i] = 'touch-move'

        if not any(events):
            return
        for i in range(SLOT_NUM):
            if touchmoves[i] and touchmoves[i][1] > 0:
                events[i] = 'touch-move %3.f %3.f' % touchmoves[i][:2]
        self.emit_touch_events(events)
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

def gesture_recognize(queue):
    wait_begin_time = None
    wait_seconds = 0
    while True:
        try:
            time.sleep(0.001)
            evt = queue.get_nowait()
            print 222, repr(evt)
        except Queue.Empty:
            now = time.time()
            if wait_begin_time is None:
                wait_begin_time = now
            elif now - wait_begin_time > 1:
                wait_seconds += 1
                print 'waited %d second' % wait_seconds
                wait_begin_time = now
            continue
        except Exception as e:
            print 111, e, type(e)
        wait_begin_time = None
        wait_seconds = 0

class GestureRecognizer(object):
    def __init__(self, queue):
        self.queue = queue
        self.running = False

    def register(self, func):
        pass

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
        wait_begin_time = None
        wait_seconds = 0
        while True:
            try:
                time.sleep(0.001)
                evt = self.queue.get_nowait()
                print 222, repr(evt)
            except Queue.Empty:
                if not self.running:
                    break
                now = time.time()
                if wait_begin_time is None:
                    wait_begin_time = now
                elif now - wait_begin_time > 1:
                    wait_seconds += 1
                    print 'waited %d second' % wait_seconds
                    wait_begin_time = now
                continue
            except Exception as e:
                print 111, e, type(e)
            wait_begin_time = None
            wait_seconds = 0

        print 'process done.'


class AndroidInputHookManager(object):

    def __init__(self, serial=None):
        self._serial = serial
        self._queue = Queue.Queue()
        self._listener = None
        self._parser = InputParser(self._queue)
        self._consumer = GestureRecognizer(self._queue)

    def set_serial(self, serial):
        self._serial = serial

    def register(self, keycode, func):
        '''register hook function'''
        pass

    def hook(self):
        '''input should be a filelike object.'''
        cmd = ['adb']
        if self._serial:
            cmd.extend(['-s', self._serial])
        cmd.extend(['shell', 'getevent', '-lt'])
        self._listener = p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        self._consumer.start()

        def listen():
            while True:
                try:
                    line = p.stdout.readline().strip()
                    if not line:
                        if p.poll() is not None:
                            print 'adb terminated.'
                            self._consumer.stop()
                            break
                        continue
                    self._parser.feed(line)
                except KeyboardInterrupt:
                    p.kill()
                except Exception as e:
                    print type(e), str(e)
                    p.kill()

        t = threading.Thread(target=listen)
        t.setDaemon(True)
        t.start()

    def unhook(self):
        if self._listener:
            self._listener.kill()

if __name__ == '__main__':
    hm = AndroidInputHookManager()
    hm.hook()
    time.sleep(10)
    hm.unhook()