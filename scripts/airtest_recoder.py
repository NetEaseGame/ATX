#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# 2014/07/02 by codeskyblue
#
'''
convert adb event to air.test program
usage is simple:
    python airtest_recorder.py output.py
'''

import sys
import time
import subprocess
import re
import os

DEVSCREEN = '/dev/input/event1'

__header__ = '''
import airtest
app = airtest.connect("{id}")
'''

def getRawShape():
    output = subprocess.check_output('adb shell getevent -p '+DEVSCREEN, shell=True)
    re.compile(r'0035.*max (\d+)')
    max_x = re.search(r'0035.*max (\d+)', output).group(1)
    max_y = re.search(r'0036.*max (\d+)', output).group(1)
    return max_x, max_y

def getShape():
    rsRE = re.compile('\s*mRestrictedScreen=\(\d+,\d+\) (?P<w>\d+)x(?P<h>\d+)')
    for line in subprocess.check_output('adb shell dumpsys window', shell=True).splitlines():
        m = rsRE.match(line)
        if m:
            return m.groups()
    raise RuntimeError('Couldn\'t find mRestrictedScreen in dumpsys')

def getScale():
    rawx, rawy = getRawShape()
    w, h = getShape()
    width, height = min(w, h), max(w, h)
    print '#raw', rawx, rawy
    print '# screen.width:', width
    print '# screen.height:', height
    if width == w:
        print("def click(x, y): app.touch(x, y)")
    else:
        print("def click(x, y): app.touch(y, %s-x)", width)
    print("def sleep(d): app.sleep(d)")
    return float(rawx)/float(width), float(rawy)/float(height)

def getDeviceId():
    output = subprocess.check_output('adb devices', shell=True)
    match = re.search(r'([\w\d:.]+)\s+device\s*$', output)
    if match:
        return match.group(1)
    raise RuntimeError("Couldn't find avaliable device")

def main(pipe, filename):
    xs, ys = [], []
    lastOper = ''
    touchStart = 0
    start = time.time()
    begin = time.time()

    deviceId = getDeviceId()
    scaleX, scaleY = getScale()

    def record(fmt, *args):
        outstr = fmt % args
        if filename:
            with open(filename, 'a') as file:
                file.write(outstr + '\n')
        print outstr

    record(__header__.format(id=deviceId))

    # plen()
    while True:
        line = pipe.readline()
        if not line.startswith(DEVSCREEN):
            continue
        channel, event, oper, value = line.split()
        # print event, oper, value#int(value, 16)
        value = int(value, 16)
        if oper == 'SYN_REPORT':
            continue
        
        if oper == 'ABS_MT_POSITION_X':
            xs.append(value)
        elif oper == 'ABS_MT_POSITION_Y':
            ys.append(value)
        elif oper == 'SYN_MT_REPORT':
            if lastOper == oper:
                xs = map(lambda x: x/scaleX, xs)
                ys = map(lambda y: y/scaleY, ys)
                if len(xs) != 0 and len(ys) != 0: # every thing is OK
                    (x1, y1), (x2, y2) = (xs[0], ys[0]), (xs[-1], ys[-1])
                    dist = ((x2-x1)*(x2-x1) + (y2-y1)*(y2-y1))**0.5

                    duration = time.time()-touchStart
                    # print 'Duration:', duration
                    # touch up
                    if dist < 50:
                        record('app.click((%d, %d))', x1, y1)
                    else:
                        record('app.drag((%d, %d), (%d, %d))', x1, y1, x2, y2)
                xs, ys = [], []
            else:
                if len(xs) == 1:
                    # touch down
                    record('app.sleep(%.2f)', float(time.time()-start))
                    start = time.time()
                    touchStart = time.time()      
        lastOper = oper

if __name__ == '__main__':
    try:
        filename = None if len(sys.argv) == 1 else sys.argv[1]
        if filename and os.path.exists(filename):
            os.unlink(filename)
        p = subprocess.Popen(['adb', 'shell', 'getevent', '-l'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        main(p.stdout, filename)
    except KeyboardInterrupt:
        print 'Exit'
        p.kill()
