#-*- encoding: utf-8 -*-

import os
import sys
import time
import pyHook
import win32api
import win32gui
import win32con
import win32process
import Tkinter as tk
from collections import namedtuple

from atx.device.windows import WindowsDevice
from atx.device.android import AndroidDevice

__dir__ = os.path.dirname(os.path.abspath(__file__))

class BaseRecorder(object):

    StepClass = namedtuple('Step', ('idx', 'type', 'value'))

    def __init__(self, device=None):
        print "hello from BaseRecorder"
        self.steps = []

        self.device = None
        if device is not None:
            self.attach(device)

    def attach(self, device):
        """绑定设备,监视用户输入，需要把监视点击和键盘的分开，键盘输入作为一个整体"""
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
        """点击后，记录响应稳定后图片的特征，此函数应该由on_click或on_text来调用"""
        pass

    def dump(self):
        """把steps输出成py文件"""
        pass

    def run(self):
        print "running"

    def stop(self):
        self.detach()
        print "stopped"

class WindowsRecorder(BaseRecorder):

    _addon_class = namedtuple('addon', ('atom', 'hwnd'))

    def __init__(self, device=None):
        print "hello from WindowsRecorder"
        self.hm = None
        self.watched_hwnds = set()
        super(WindowsRecorder, self).__init__(device)

    def attach(self, device):
        if self.device is not None:
            print "Warning: already attached to a device."
            if device is not self.device:
                self.detach()

        print 111
        def callback(hwnd, extra):
            extra.add(hwnd)
            return True
        handle = device._win._handle
        self.watched_hwnds.add(handle)
        win32gui.EnumChildWindows(handle, callback, self.watched_hwnds)
        print 222, len(self.watched_hwnds)

        def on_mouse(event):
            if device is None:
                return True
            if event.Window in self.watched_hwnds:
                print "Hello", event.Message, event.Position
            return True

        def on_keyboard(event):
            if device is None:
                return True
            if event.Window in self.watched_hwnds:
                print "\t", repr(event.Ascii), event.KeyId, event.ScanCode, event.flags
                print "\t", event.Key, event.Extended, event.Injected, event.Alt, event.Transition
            return True

        print 333
        hm = pyHook.HookManager()
        hm.MouseAllButtons = on_mouse
        hm.KeyAll = on_keyboard
        print 444
        hm.HookMouse()
        print 555
        hm.HookKeyboard()
        self.hm = hm

        print "attach to device", device
        self.device = device

    def detach(self):
        print "detach from device", self.device

        self.device = None
        self.watched_hwnds = set()

        if self.hm is not None:
            self.hm.UnhookMouse()
            self.hm.UnhookKeyboard()
        self.hm = None


class SystemTray(object):
    def __init__(self, parent, name, commands=None, icon_path=None):
        self.parent = parent
        self.name = name
        self.WM_NOTIFY = win32con.WM_USER+20

        wndproc = {
            win32con.WM_DESTROY: self.on_destroy,
            win32con.WM_COMMAND: self.on_command,
            self.WM_NOTIFY: self.on_tray_notify,
        }

        wc = win32gui.WNDCLASS()
        wc.hInstance = hinst = win32api.GetModuleHandle(None)
        wc.lpszClassName = name.title()
        wc.lpfnWndProc = wndproc
        class_atom = win32gui.RegisterClass(wc)
        self.hwnd = win32gui.CreateWindow(wc.lpszClassName, "", win32con.WS_POPUP, 0,0,1,1, parent, 0, hinst, None)
        win32gui.UpdateWindow(self.hwnd)

        if icon_path is not None and os.path.isfile(icon_path):
            icon_flags = win32con.LR_LOADFROMFILE | win32con.LR_DEFAULTSIZE
            hicon = win32gui.LoadImage(None, icon_path, win32con.IMAGE_ICON, 0, 0, icon_flags)
        else:
            shell_dll = os.path.join(win32api.GetSystemDirectory(), "shell32.dll")
            large, small = win32gui.ExtractIconEx(shell_dll, 19, 1) #19 or 76
            hicon = small[0]
            win32gui.DestroyIcon(large[0])
        self.hicon = hicon

        flags = win32gui.NIF_ICON | win32gui.NIF_MESSAGE | win32gui.NIF_TIP | win32gui.NIF_INFO
        nid = (self.hwnd, 0, flags, self.WM_NOTIFY, self.hicon, self.name)
        win32gui.Shell_NotifyIcon(win32gui.NIM_ADD, nid)

        self.next_command_id = 1000
        self.commands = {}
        self.register_command('Exit', lambda:win32gui.DestroyWindow(self.hwnd))
        if commands is not None:
            for n, f in commands[::-1]:
                self.register_command(n, f)

    def balloon(self, msg, title=""):
        flags = win32gui.NIF_ICON | win32gui.NIF_MESSAGE | win32gui.NIF_TIP | win32gui.NIF_INFO
        nid = (self.hwnd, 0, flags, self.WM_NOTIFY, self.hicon, self.name, msg, 300, title)
        win32gui.Shell_NotifyIcon(win32gui.NIM_MODIFY, nid)

    def register_command(self, name, func):
        cid = self.next_command_id
        self.next_command_id += 1
        self.commands[cid] = (name, func)
        return cid

    def on_destroy(self, hwnd, msg, wp, lp):
        win32gui.Shell_NotifyIcon(win32gui.NIM_DELETE, (self.hwnd, 0))
        win32gui.PostMessage(self.parent, win32con.WM_CLOSE, 0, 0)

    def on_command(self, hwnd, msg, wp, lp):
        print "on_command"
        cid = win32api.LOWORD(wp)
        if not self.commands.get(cid):
            print "Unknown command -", cid
            return
        _, func = self.commands[cid]
        try:
            func()
        except Exception as e:
            print str(e)

    def on_tray_notify(self, hwnd, msg, wp, lp):
        if lp == win32con.WM_LBUTTONUP:
            # print "left click"
            # win32gui.SetForegroundWindow(self.hwnd)
            pass
        elif lp == win32con.WM_RBUTTONUP:
            # print "right click"
            menu = win32gui.CreatePopupMenu()
            for cid in sorted(self.commands.keys(), reverse=True):
                name, _ = self.commands[cid]
                win32gui.AppendMenu(menu, win32con.MF_STRING, cid, name)

            pos = win32gui.GetCursorPos()
            win32gui.SetForegroundWindow(self.hwnd)
            win32gui.TrackPopupMenu(menu, win32con.TPM_LEFTALIGN, pos[0], pos[1], 0, self.hwnd, None)
            win32gui.PostMessage(self.hwnd, win32con.WM_NULL, 0, 0)
        return True

class RecorderGUI(object):
    def __init__(self, device=None):
        self.device = device
        self._recorder = None
        self._root = root = tk.Tk()

        def _destroy():
            print "root destroy"
            root.destroy()
            self.stop_record()
            self.device = None

        root.protocol("WM_DELETE_WINDOW", _destroy)

        def calllater():
            icon_path = os.path.join(__dir__, 'static', 'recorder.ico')
            commands  = [
                ("Start Record", self.start_record),
                ("Stop Record", self.stop_record),
            ]
            tray = SystemTray(root.winfo_id(), "recorder", commands, icon_path)
            tray.balloon('hello')

        root.after(300, calllater)

        ## no window for now.
        root.withdraw()

    def mainloop(self):
        self._root.mainloop()

    def start_record(self):
        if self.recorder is None:
            return
        self.recorder.run()

    def stop_record(self):
        if self.recorder is None:
            return
        self.recorder.stop()

    @property
    def recorder(self):
        if self.device is None:
            print "No device choosen."
            self._recorder = None
            return

        if self._recorder is None:
            print "init recorder", type(self.device)
            if isinstance(self.device, WindowsDevice):
                self._recorder = WindowsRecorder(self.device)
            elif isinstance(self.device, AndroidDevice):
                pass

        return self._recorder

if __name__ == '__main__':
    w = RecorderGUI()
    w.mainloop()
