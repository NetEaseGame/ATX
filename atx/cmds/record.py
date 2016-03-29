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

Step = namedtuple('Step', ('type', 'value'))

class BaseRecorder(object):

    def __init__(self, device=None):
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

    def run(self):
        """start to record"""
        raise NotImplementedError()

    def stop(self):
        """stop record"""
        raise NotImplementedError()

    def on_click(self, postion):
        """点击时自动截取一小段"""
        self.steps.append(Step('click', postion))

    def on_drag(self, start, end):
        self.steps.append(Step('drag', (start, end)))

    def on_text(self, text):
        """输入文字整个作为一个case"""
        self.steps.append(Step('text', text))

    def wait_respond(self, response):
        """点击后，记录响应稳定后图片的特征，此函数应该由on_click或on_text来调用"""
        pass

    def dump(self):
        """把steps输出成py文件"""
        pass

class WindowsRecorder(BaseRecorder):

    KBFLAG_CTRL = 0x01
    KBFLAG_ALT = 0x02
    KBFLAG_SHIFT = 0x04
    KBFLAG_CAPS = 0x08

    def __init__(self, device=None):
        self.watched_hwnds = set()
        super(WindowsRecorder, self).__init__(device)
        self.kbflag = 0
        self.hm = pyHook.HookManager()
        self.hm.MouseAllButtons = self.on_mouse
        self.hm.KeyAll = self.on_keyboard

    def attach(self, device):
        if self.device is not None:
            print "Warning: already attached to a device."
            if device is not self.device:
                self.detach()

        handle = device.hwnd
        def callback(hwnd, extra):
            extra.add(hwnd)
            return True
        self.watched_hwnds.add(handle)
        win32gui.EnumChildWindows(handle, callback, self.watched_hwnds)

        self.device = device
        print "attach to device", device

    def detach(self):
        print "detach from device", self.device
        self.device = None
        self.watched_hwnds = set()

    def run(self):
        self.hm.HookMouse()
        self.hm.HookKeyboard()

    def stop(self):
        self.hm.UnhookMouse()
        self.hm.UnhookKeyboard()

    def on_mouse(self, event):
        if self.device is None:
            return True
        if event.Window not in self.watched_hwnds:
            return True
        print "on_mouse", event.MessageName, event.Position
        num = int(time.time() * 1000)
        self.device.screenshot("img-%s.png" % num )
        return True

    def on_keyboard(self, event):
        if self.device is None:
            return True
        if event.Window not in self.watched_hwnds:
            return True
        print "on_keyboard", event.MessageName, event.Key, repr(event.Ascii), event.KeyID, event.ScanCode, 
        print event.flags, event.Extended, event.Injected, event.Alt, event.Transition
        return True

class AndroidRecorder(BaseRecorder):
    def attach(self):
        pass

    def detach(self):
        pass

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
        return True

    def on_command(self, hwnd, msg, wp, lp):
        cid = win32api.LOWORD(wp)
        if not self.commands.get(cid):
            print "Unknown command -", cid
            return
        _, func = self.commands[cid]
        try:
            func()
        except Exception as e:
            print str(e)
        return True

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
        self._device = device
        self._recorder = None
        self._root = root = tk.Tk()

        root.protocol("WM_DELETE_WINDOW", self.destroy)

        def calllater():
            icon_path = os.path.join(__dir__, 'static', 'recorder.ico')
            commands  = [
                ("Start Record", self.start_record),
                ("Stop Record", self.stop_record),
            ]
            tray = SystemTray(root.winfo_id(), "recorder", commands, icon_path)
            tray.balloon('hello')

        root.after(2000, calllater)

        # no window for now.
        root.withdraw()

        # need to handle device event

    def destroy(self):
        print "root destroy"
        if self._recorder is not None:
            self._recorder.stop()
        self._root.destroy()
        win32api.PostQuitMessage(0)

    def mainloop(self):
        self._root.mainloop()

    def start_record(self):
        if not self.check_recorder():
            return
        self._recorder.run()

    def stop_record(self):
        if not self.check_recorder():
            return
        self._recorder.stop()

    def check_recorder(self):
        if self._device is None:
            print "No device choosen."
            self._recorder = None
            return False

        if self._recorder is None:
            print "init recorder", type(self._device)
            if isinstance(self._device, WindowsDevice):
                record_class = WindowsRecorder
            elif isinstance(self._device, AndroidDevice):
                record_class = AndroidRecorder
            else:
                print "Unknown device type", type(self._device)
                return False
            self._recorder = record_class(self._device)
        return True

if __name__ == '__main__':
    w = RecorderGUI()
    w.mainloop()
