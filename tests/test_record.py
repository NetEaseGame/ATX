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

import win32ui
import win32con
import win32api
import win32gui
import win32process
from pyHook import HookManager
from collections import namedtuple

from atx.device.windows import Window, find_process_id

class Recorder(object):

    StepClass = namedtuple('STEP', ('idx', 'type', 'value'))

    def __init__(self, device=None):
        self.steps = []

        self.device = device
        if device is not None:
            self.attach(device)

        self.hook_inputs()

    def hook_inputs(self):
        """监视用户输入，需要把监视点击和键盘的分开，键盘输入作为一个整体"""
        raise NotImplementedError()

    def attach(self, device):
        """绑定设备"""
        raise NotImplementedError()

    def detach(self):
        """解绑设备"""
        raise NotImplementedError()

    def on_click(self, postion):
        """点击时自动截取一小段"""
        step = Recorder.StepClass()

    def on_text(self, text):
        """输入文字整个作为一个case"""
        pass

    def wait_respond(self, response):
        """点击后，记录响应稳定后图片的特征，此函数应该由on_touch或on_text来调用"""
        pass

    def dump(self):
        pass

    def run(self):
        pass

class WindowsRecorder(Recorder):

    def __init__(self, device=None, addon=False):
        super(WindowsRecorder, self).__init__(device)

        _addon_class = namedtuple('addon', ('atom', 'hwnd'))
        self.addon = _addon_class(None, None)
        if addon:
            self.addon = _addon_class(*self.init_addon())

    def init_addon(self):

        def on_create(hwnd, msg, wp, lp):
            print "on_create"

        def on_paint(hwnd, msg, wp, lp):
            if self.device is not None:
                try:
                    l, t, r, b = win32gui.GetWindowRect(self.device._handle)
                except Exception as e:
                    print "device may be distroyed.", str(e)
                    self.detach()
                    win32gui.ShowWindow(hwnd, False)
                else:
                    
                    win32gui.SetWindowPos(hwnd, win32con.HWND_TOPMOST, l, t, r-l, b-t, 0)
                    # win32gui.SetWindowPos(self.device._handle, hwnd, l, t, r-l, b-t, 0)

        def on_close(hwnd, msg, wp, lp):
            print "on_close"
            win32gui.DestroyWindow(hwnd)
            win32gui.PostQuitMessage(0)

        def on_mouse(hwnd, msg, wp, lp):
            print "on_mouse", wp, lp
            return True

        def on_keyboard(hwnd, msg, wp, lp):
            print "on_keyboard", wp, lp
            return True

        wndproc = {
            win32con.WM_PAINT: on_paint,
            win32con.WM_CLOSE: on_close,
            win32con.WM_CREATE: on_create,
        }

        wc = win32gui.WNDCLASS()
        wc.lpszClassName = '_atx_window_record_'
        wc.style = win32con.CS_GLOBALCLASS | win32con.CS_VREDRAW | win32con.CS_HREDRAW
        wc.hbrBackground = win32con.COLOR_WINDOW + 1
        wc.lpfnWndProc = wndproc

        class_atom = win32gui.RegisterClass(wc)
        hwnd = win32gui.CreateWindowEx(
            win32con.WS_EX_LAYERED,# | win32con.WS_EX_TRANSPARENT ,  # dwExStyle,
            class_atom, '',             # lpClassName, lpWindowName,
            win32con.WS_VISIBLE | win32con.WS_CLIPCHILDREN | win32con.WS_CLIPSIBLINGS | win32con.WS_POPUP,   # dwStyle, no frame
            100, 100, 100, 100,         # x, y, nWidth, nHeight
            0, 0, 0,                    # hwndParent, hMenu, hInstance
            None,                       # lpParam
        )  

        ## make transparent
        win32gui.SetLayeredWindowAttributes(hwnd, 0, 50, win32con.LWA_ALPHA | win32con.LWA_COLORKEY)

        return class_atom, hwnd

    def attach(self, device):
        print "attach to device", device
        self.device = device
        if self.addon.hwnd:
            win32gui.ShowWindow(self.addon.hwnd, True)

    def detach(self):
        print "detach from device", self.device
        self.device = None
        if self.addon.hwnd:
            win32gui.ShowWindow(self.addon.hwnd, False)

    def hook_inputs(self):

        def on_mouse(event):
            print event.MessageName, event.WindowName, event.Position, event.Wheel
            return True

        def on_keyboard(event):
            print event.Key, repr(event.Ascii)
            return True

        hm = HookManager()
        hm.MouseLeftDown = on_mouse
        hm.KeyDown = on_keyboard
        hm.HookMouse()
        hm.HookKeyboard()

    def run(self):
        win32gui.PumpMessages()
        if self.addon_class_atom:
            win32gui.UnregisterClass(self.addon_class_atom, None)

def main():
    exe_file = "C:\\Windows\\System32\\calc.exe"
    if not find_process_id(exe_file):
        os.startfile(exe_file)
        time.sleep(3)

    win = Window(exe_file=exe_file)

    rec = WindowsRecorder(addon=True)
    rec.attach(win)
    rec.run()

if __name__ == '__main__':
    main()