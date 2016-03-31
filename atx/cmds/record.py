#-*- encoding: utf-8 -*-

import os
import cv2
import sys
import time
import bisect
import tempfile
import threading
import Tkinter as tk
import win32api
import win32con
import win32gui
import win32process
import pywintypes
import pyHook
from math import ceil
from pyHook import HookConstants
from collections import namedtuple

from atx.device.windows import WindowsDevice
from atx.device.android import AndroidDevice
from atx.imutils import diff_rect

__dir__ = os.path.dirname(os.path.abspath(__file__))

__CaptureRecord = namedtuple('__CaptureRecord', ('ctime', 'image'))
class CaptureRecord(__CaptureRecord):
    def __eq__(self, other):
        return self[0] == other[0]
    def __ne__(self, other):
        return not self == other
    def __gt__(self, other):
        return self[0] > other[0]
    def __ge__(self, other):
        return not self<other
    def __lt__(self, other):
        return self[0] < other[0]
    def __le__(self, other):
        return not other<self

__Step = namedtuple('Step', ('index', 'ctime', 'image', 'action', 'args'))
class Step(__Step):
    def to_script(self, timeout, indent=4):
        res = []
        res.append('with d.watch("%s-target.png", %s) as w:' % (self.index, ceil(timeout)))
        res.append('%sw.on("%s-action.png", %s).click()' % (' '*indent, self.index, self.args))
        return '\n'.join(res)

class BaseRecorder(object):

    def __init__(self, device=None):
        self.steps = []
        self.device = None
        if device is not None:
            self.attach(device)

        self.running = False
        
        self.steps_lock = threading.Lock()
        self.step_index = 0
        self.last_step = None
        self.default_radius = 20

        self.look_ahead_num = 3 # diff with later screens to find target object 
        self.capture_interval = 0.05
        self.capture_maxnum = 50 # watch out your memory!
        self.capture_lock = threading.Lock()
        self.capture_cache = []
        self.capture_tmpdir = os.path.join(os.getcwd(), 'screenshots', time.strftime("%Y%m%d"))
        if not os.path.exists(self.capture_tmpdir):
            os.makedirs(self.capture_tmpdir)

        t = threading.Thread(target=self.async_capture)
        t.setDaemon(True)
        t.start()

    def attach(self, device):
        """Attach to device, if current device is not None, should
        detach from it first. """
        raise NotImplementedError()

    def detach(self):
        """Detach from current device."""
        raise NotImplementedError()

    def run(self):
        """Start watching inputs & device screen."""
        raise NotImplementedError()

    def stop(self):
        """Stop record."""
        raise NotImplementedError()

    def next_index(self):
        with self.steps_lock:
            self.step_index += 1
            return self.step_index

    def on_touch(self, position):
        """Handle touch input event."""
        t = threading.Thread(target=self.__async_handle_touch, args=(position, ))
        t.setDaemon(True)
        t.start()

    def __async_handle_touch(self, position):
        t = time.time()
        # add a little delay, so we can check the screen after the touch
        time.sleep(self.capture_interval*(self.look_ahead_num+1))
        self.capture_lock.acquire()
        try:
            # trace back a few moments, find a untouched image
            # we're sure all item[0] won't be same
            idx = bisect.bisect(self.capture_cache, (t, None))
            if idx == 0 or idx == len(self.capture_cache):
                print "no captured screens yet", idx
                return
            # just use two for now. 
            before, after = self.capture_cache[idx-1], self.capture_cache[idx:idx+self.look_ahead_num]
        finally:
            self.capture_lock.release()

        idx = self.next_index()
        t0, img0 = before
        for t1, img1 in after:
            rect = diff_rect(img0, img1, position)
            if rect is not None:
                print idx, "click at", position, 'found rect', rect
                break
        if rect is None:
            rect = self.__get_default_rect(img0.shape[:2], position)
            print idx, "click at", position, 'use default rect', rect

        x0, y0, x1, y1 = rect
        subimg = img0[y0:y1, x0:x1, :]
        filepath = os.path.join(self.capture_tmpdir, "%d-action.png" % idx)
        cv2.imwrite(filepath, subimg)
        # filepath = os.path.join(self.capture_tmpdir, "%d-1.png" % idx)
        # cv2.imwrite(filepath, img0)
        # filepath = os.path.join(self.capture_tmpdir, "%d-2.png" % idx)
        # cv2.imwrite(filepath, img1)

        step = Step(idx, t, img0, 'touch', position)
        self.__pack_last_step(step)


    def __pack_last_step(self, step):
        # find target for last step and pack it.
        if not self.last_step:
            self.last_step = step
            return

        last_step = self.last_step
        rect = diff_rect(last_step.image, step.image)
        if rect is None:
            h, w = step.image.shape[:2]
            if step.action == 'touch':
                position = step.args
            else:
                position = w/2, h/2
            rect = self.__get_default_rect(step.image, position)

        x0, y0, x1, y1 = rect
        subimg = step.image[y0:y1, x0:x1, :]
        filepath = os.path.join(self.capture_tmpdir, "%d-target.png" % step.index)
        cv2.imwrite(filepath, subimg)

        timeout = step.ctime - last_step.ctime
        script = last_step.to_script(timeout)
        # save last step
        with self.steps_lock:
            self.steps.append(script)
        self.last_step = step

    def __get_default_rect(self, size, position):
        h, w = size
        x, y = position
        r = self.default_radius
        return (max(x-r,0), max(y-r,0), min(x+r,w), min(y+r,h))

    def on_drag(self, start, end):
        """Handle drag input event."""

    def on_text(self, text):
        """Handle text input event."""

    def dump(self, filepath=None):
        """Generate python scripts."""
        filepath = os.path.join(self.capture_tmpdir, 'steps.py')
        with open(filepath, 'w') as f:
            with self.steps_lock:
                f.write('\n'.join(self.steps))

    def async_capture(self):
        """Keep capturing device screen. Should run in background
        as a thread."""
        while True:
            self.capture_lock.acquire()
            try:
                time.sleep(self.capture_interval)
                if not self.running or self.device is None:
                    continue
                img = self.device.screenshot_cv2()
                self.capture_cache.append(CaptureRecord(time.time(), img))

                # TODO: change capture_cache to a loop list
                while len(self.capture_cache) > self.capture_maxnum:
                    _, img = self.capture_cache.pop(0)

            finally:
                self.capture_lock.release()

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
        self.hm.MouseAllButtons = self._hook_on_mouse
        self.hm.KeyAll = self._hook_on_keyboard

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
        try:
            # EnumChildWindows may crash for windows have no any child.
            # refs: https://mail.python.org/pipermail/python-win32/2005-March/003042.html
            win32gui.EnumChildWindows(handle, callback, self.watched_hwnds)
        except pywintypes.error as e:
            pass

        self.device = device
        print "attach to device", device

    def detach(self):
        print "detach from device", self.device
        self.device = None
        self.watched_hwnds = set()

    def run(self):
        self.hm.HookMouse()
        self.hm.HookKeyboard()
        with self.capture_lock:
            self.running = True

    def stop(self):
        with self.capture_lock:
            self.running = False
        self.hm.UnhookMouse()
        self.hm.UnhookKeyboard()

        # for test, dump steps when stop
        self.dump()

    def _hook_on_mouse(self, event):
        if self.device is None:
            return True
        if event.Window not in self.watched_hwnds:
            return True
        if event.Message == HookConstants.WM_LBUTTONUP:
            x, y = self.device.norm_position(event.Position)
            # ignore the touches outside the rect if the window has a frame.
            if x < 0 or y < 0:
                return True
            self.on_touch((x, y))

        return True

    def _hook_on_keyboard(self, event):
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
