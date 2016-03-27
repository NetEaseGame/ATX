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
import pywintypes
from pyHook import HookManager
from collections import namedtuple

from atx.device.windows import Window, find_process_id

class Recorder(object):

    StepClass = namedtuple('Step', ('idx', 'type', 'value'))

    def __init__(self, device=None):
        self.steps = []

        self.device = device
        if device is not None:
            self.attach(device)

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

    _addon_class = namedtuple('addon', ('atom', 'hwnd'))

    def __init__(self, device=None, with_addon=False):
        self.watched_hwnds = set()
        self.addon = WindowsRecorder._addon_class(None, None)
        self.with_addon = with_addon
        self.hm = None

        super(WindowsRecorder, self).__init__(device)

    def init_addon(self):

        def on_create(hwnd, msg, wp, lp):
            print "on_create"

        def on_paint(hwnd, msg, wp, lp):
            # print win32gui.GetForegroundWindow()
            if self.device is not None:
                try:
                    l, t, r, b = win32gui.GetWindowRect(self.device._handle)
                except Exception as e:
                    print "device may be distroyed.", str(e)
                    self.detach()
                    # win32gui.SetWindowPos(hwnd, win32con.HWND_BOTTOM, 0, 0, 1, 1, 0)
                else:
                    win32gui.SetWindowPos(hwnd, win32con.HWND_TOPMOST, l, t, r-l, b-t, 0)
            else:
                win32gui.SetWindowPos(hwnd, win32con.HWND_TOPMOST, 100, 100, 100, 100, 0)

        def on_close(hwnd, msg, wp, lp):
            print "on_close"
            win32gui.DestroyWindow(hwnd)
            win32gui.PostQuitMessage(0)

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
            win32con.WS_EX_LAYERED | win32con.WS_EX_TRANSPARENT ,  # dwExStyle,
            class_atom, '',             # lpClassName, lpWindowName,
            win32con.WS_VISIBLE | win32con.WS_CLIPCHILDREN | win32con.WS_CLIPSIBLINGS | win32con.WS_POPUP,   # dwStyle, no frame
            100, 100, 100, 100,         # x, y, nWidth, nHeight
            0, 0, 0,                    # hwndParent, hMenu, hInstance
            None,                       # lpParam
        )  

        ## make transparent
        win32gui.SetLayeredWindowAttributes(hwnd, 0, 80, win32con.LWA_ALPHA | win32con.LWA_COLORKEY)

        return class_atom, hwnd

    def attach(self, device):
        print "attach to device", device
        self.device = device

        ## try to filter evets using all child-window's handles
        ## But the opertations on menus are tricky
        ## so just go the easy way for now.

        def callback(hwnd, extra):
            extra.add(hwnd)
            return True

        self.watched_hwnds.add(self.device._handle)
        win32gui.EnumChildWindows(self.device._handle, callback, self.watched_hwnds)
        print "find %s child window" % len(self.watched_hwnds) # 67 for calc

        if self.with_addon:
            atom, hwnd = self.init_addon()
            self.addon = WindowsRecorder._addon_class(atom, hwnd)
            win32gui.SetParent(hwnd, self.device._handle)

        # hmenu = win32gui.GetMenu(self.device._handle)
        # print "hmenu:", hmenu
        # self.watched_hwnds.add(hmenu)
        # print "find %s child window" % len(self.watched_hwnds) # 67 for calc
        self.hook_inputs()

    def detach(self):
        print "detach from device", self.device
        if self.addon.hwnd:
            win32gui.DestroyWindow(self.addon.hwnd)
            win32gui.UnregisterClass(self.addon.atom, None)
            self.addon = WindowsRecorder._addon_class(None, None)

        self.device = None
        self.watched_hwnds = set()
        self.unhook_inputs()

    def hook_inputs(self):
        if self.hm is not None:
            return

        def on_mouse(event):
            if self.device is None:
                return True
            ok = event.Window in self.watched_hwnds
            print ok, event.MessageName, event.Window, event.WindowName, event.Position, event.Wheel
            return True

        def on_keyboard(event):
            if self.device is None:
                return True
            ok = event.Window in self.watched_hwnds
            print ok, event.Window, event.WindowName, event.Message, Event.Time
            print "\t", repr(event.Ascii), event.KeyId, event.ScanCode, event.flags
            print "\t", event.Key, event.Extended, event.Injected, event.Alt, event.Transition
            return True

        hm = HookManager()
        hm.MouseAll = on_mouse
        hm.KeyAll = on_keyboard
        hm.HookMouse()
        hm.HookKeyboard()
        self.hm = hm

    def unhook_inputs(self):
        if self.hm is not None:
            self.hm.UnhookMouse()
            self.hm.UnhookKeyboard()
        self.hm = None

    def run(self):
        win32gui.PumpMessages()

    def pause(self):
        pass


"""
static PyObject *PyPumpWaitingMessages(PyObject *self, PyObject *args)
{
    MSG msg;
    long result = 0;
    // Read all of the messages in this next loop, 
    // removing each message as we read it.
    Py_BEGIN_ALLOW_THREADS
    while (PeekMessage(&msg, NULL, 0, 0, PM_REMOVE)) {
        // If it's a quit message, we're out of here.
        if (msg.message == WM_QUIT) {
            result = 1;
            break;
        }
        // Otherwise, dispatch the message.
        DispatchMessage(&msg); 
    } // End of PeekMessage while loop
    Py_END_ALLOW_THREADS
    return PyInt_FromLong(result);
}

// @pymethod |pythoncom|PumpMessages|Pumps all messages for the current thread until a WM_QUIT message.
static PyObject *pythoncom_PumpMessages(PyObject *self, PyObject *args)
{
    MSG msg;
    int rc;
    Py_BEGIN_ALLOW_THREADS
    while ((rc=GetMessage(&msg, 0, 0, 0))==1) {
        TranslateMessage(&msg); // needed?
        DispatchMessage(&msg);
    }
    Py_END_ALLOW_THREADS
    if (rc==-1)
        return PyWin_SetAPIError("GetMessage");
    Py_INCREF(Py_None);
    return Py_None;
}
"""

def main():
    exe_file = "C:\\Windows\\System32\\calc.exe"
    if not find_process_id(exe_file):
        os.startfile(exe_file)
        time.sleep(3)

    win = Window(exe_file=exe_file)

    rec = WindowsRecorder(with_addon=True)
    rec.attach(win)
    rec.run()

if __name__ == '__main__':
    main()