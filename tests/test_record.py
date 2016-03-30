#-*- encoding: utf-8 -*-

# first, attach a transparent window W infront of 
# the watched one. W will watch all mouse & keyboard
# events for the window

# second, on each input event, we check the differences
# between the window screens before and after the event. 

# the differences indicates a shape which is the one
# user touched. We can translate the event into a
# testcase.

# the event response time is crucial and may be varing
# between games & even ui-parts in one game. 

import os
import time

from atx.device.windows import WindowsDevice, find_process_id
from atx.cmds.record import RecorderGUI

def get_calc_win():
    exe_file = "C:\\Windows\\System32\\calc.exe"
    if not find_process_id(exe_file):
        os.startfile(exe_file)
        time.sleep(3)

    win = WindowsDevice(exe_file=exe_file)
    return win

def get_game_win():
    window_name = "MyLuaGame"
    win = WindowsDevice(window_name=window_name)
    return win

def main():
    win = get_game_win()
    print "window handle", hex(win.hwnd)
    print "window size %dx%d" % win.size

    r = RecorderGUI(win)
    r.mainloop()

if __name__ == '__main__':
    main()