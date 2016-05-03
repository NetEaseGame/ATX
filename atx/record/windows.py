#-*- encoding: utf-8 -*-

# import win32api
# import win32con
import win32gui
# import win32process
import pywintypes
from pyHook import HookManager, HookConstants

from atx.record.base import BaseRecorder

class WindowsRecorder(BaseRecorder):

    KBFLAG_CTRL = 0x01
    KBFLAG_ALT = 0x02
    KBFLAG_SHIFT = 0x04
    KBFLAG_CAPS = 0x08

    default_radius = 25
    capture_interval = 0.05
    capture_maxnum = 30

    def __init__(self, device=None):
        self.watched_hwnds = set()
        super(WindowsRecorder, self).__init__(device)
        self.kbflag = 0
        self.hm = HookManager()
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
        except pywintypes.error:
            pass

        self.device = device
        print "attach to device", device

    def detach(self):
        print "detach from device", self.device
        self.device = None
        self.watched_hwnds = set()

    def hook(self):
        self.hm.HookMouse()
        self.hm.HookKeyboard()

    def unhook(self):
        self.hm.UnhookMouse()
        self.hm.UnhookKeyboard()

    def _hook_on_mouse(self, event):
        if self.device is None:
            return True
        if event.Window not in self.watched_hwnds:
            return True
        if event.Message == HookConstants.WM_LBUTTONUP:
            x, y = self.device.norm_position(event.Position)
            # ignore the clicks outside the rect if the window has a frame.
            if x < 0 or y < 0:
                return True
            self.on_click((x, y))

        return True

    def _hook_on_keyboard(self, event):
        if self.device is None:
            return True
        if event.Window not in self.watched_hwnds:
            return True
        print "on_keyboard", event.MessageName, event.Key, repr(event.Ascii), event.KeyID, event.ScanCode, 
        print event.flags, event.Extended, event.Injected, event.Alt, event.Transition
        return True