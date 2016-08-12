#-*- encoding: utf-8 -*-

import os
import sys
import time

from atx.drivers.windows import WindowsDevice, find_process_id
from atx.drivers.android import AndroidDevice
from atx.cmds.record import RecorderGUI

def get_calc_win():
    exe_file = "C:\\Windows\\System32\\calc.exe"
    if not find_process_id(exe_file):
        os.startfile(exe_file)
        time.sleep(3)

    win = WindowsDevice(exe_file=exe_file)
    print "window handle", hex(win.hwnd)
    return win

def get_game_win():
    window_name = "MyLuaGame"
    win = WindowsDevice(window_name=window_name)
    print "window handle", hex(win.hwnd)
    return win

def get_android_dev():
    dev = AndroidDevice()
    print 'android devcie', dev._serial
    return dev

if len(sys.argv) > 1 and sys.argv[1] == 'win':
    get_device = get_calc_win
else:
    get_device = get_android_dev

def main():
    dev = get_device()
    print "display size %dx%d" % dev.display

    r = RecorderGUI(dev)
    r.mainloop()

if __name__ == '__main__':
    main()