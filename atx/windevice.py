#-*- encoding: utf-8 -*-
"""Windows application as a device."""

import os
import time
import struct
import win32ui
import win32con
import win32api
import win32gui
import win32process
from PIL import Image

from atx.device import DeviceMixin
from atx.errors import WindowsAppNotFoundError

def find_process_id(exe_file):
    exe_file = os.path.normpath(exe_file).lower()
    command = "wmic process get processid,commandline"
    for line in os.popen(command).read().lower().splitlines():
        line = line.strip()
        if not line:
            continue
        line = line.split()
        pid = line[-1]
        cmd = " ".join(line[:-1])
        if not cmd:
            continue
        elif cmd.startswith("'"):
            pos = cmd.find("'", 1)
            cmd = cmd[1:pos]
        elif cmd.startswith('"'):
            pos = cmd.find('"', 1)
            cmd = cmd[1:pos]
        else:
            cmd = cmd.split()[0]

        if exe_file == cmd:
            return int(pid)

class Window(object):
    def __init__(self, window_name=None, exe_file=None):
        hwnd = 0
        if window_name is not None:
            hwnd = win32gui.FindWindow(None, window_name)
            if hwnd == 0:
                def callback(h, arg):
                    if window_name in win32gui.GetWindowText(h):
                        hwnd = h
                        return False
                    return True
                win32gui.EnumWindows(callback, None)
            if hwnd == 0:
                raise WindowsAppNotFoundError("Windows Application <%s> not found!" % window_name)

        if hwnd == 0 and exe_file is not None:
            pid = find_process_id(exe_file)
            if pid is not None:
                def callback(h, hs):
                    if win32gui.IsWindowVisible(h) and win32gui.IsWindowEnabled(h):
                        _, p = win32process.GetWindowThreadProcessId(h)
                        if p == pid:
                            hs.append(h)
                        return True
                    return True
                hs = []
                win32gui.EnumWindows(callback, hs)
                if hs: hwnd = hs[0]
            if hwnd == 0:
                raise WindowsAppNotFoundError("Windows Application <%s> is not running!" % exe_file)

        ## if window_name & exe_file both are None, use the screen.
        self._is_desktop = False
        if hwnd == 0:
            hwnd = win32gui.GetDesktopWindow()
            self._is_desktop = True

        # self._window_name = win32gui.GetWindowText(hwnd)
        # self._window_pid = pid
        # self._exe_file = exe_file
        self._handle = hwnd
        self._bmp = None
        self._windc = None
        self._memdc = None

    @property
    def position(self):
        if self._is_desktop:
            left = win32api.GetSystemMetrics(win32con.SM_XVIRTUALSCREEN)
            top = win32api.GetSystemMetrics(win32con.SM_YVIRTUALSCREEN)
            width = win32api.GetSystemMetrics(win32con.SM_CXVIRTUALSCREEN)
            height = win32api.GetSystemMetrics(win32con.SM_CYVIRTUALSCREEN)
            return (left, top, left+width, top+height)

        return win32gui.GetWindowRect(self._handle)

    @property
    def size(self):
        if self._is_desktop:
            width = win32api.GetSystemMetrics(win32con.SM_CXVIRTUALSCREEN)
            height = win32api.GetSystemMetrics(win32con.SM_CYVIRTUALSCREEN)
            return (width, height)
            
        left, top, right, bottom = self.position
        return (right - left, bottom - top)

    def _input_left_mouse(self, x, y):
        left, top, right, bottom = self.position
        width, height = right - left, bottom - top
        if x < 0 or x > width or y < 0 or y > height:
            return

        win32gui.SetForegroundWindow(self._handle)
        pos = win32gui.GetCursorPos()
        win32api.SetCursorPos((left+x, top+y))
        win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, 0, 0)
        win32api.Sleep(100) #ms
        win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, 0, 0)
        win32api.Sleep(100) #ms
        win32api.SetCursorPos(pos)

    def _input_keyboard(self, text):
        pass

    def _prepare_divice_context(self):
        left, top, right, bottom = self.position
        width, height = right - left, bottom - top
        hwindc = win32gui.GetWindowDC(self._handle)
        windc = win32ui.CreateDCFromHandle(hwindc)
        memdc = windc.CreateCompatibleDC()
        bmp = win32ui.CreateBitmap()
        bmp.CreateCompatibleBitmap(windc, width, height)
        memdc.SelectObject(bmp)

        self._windc = windc
        self._memdc = memdc
        self._bmp = bmp

    @property
    def image(self):
        if self._bmp is None:
            self._prepare_divice_context()
        width, height = self.size
        self._memdc.BitBlt((0, 0), (width, height), self._windc, (0, 0), win32con.SRCCOPY)
        return self._bmp

    @property
    def pilimage(self):
        _bits = self.image.GetBitmapBits()
        width, height = self.size

        bits = []
        for i in range(len(_bits)/4):
            ## change to rpg here, by set alpha = -1
            bits.append(struct.pack('4b', _bits[4*i+2], _bits[4*i+1], _bits[4*i+0], -1))

        ## do a turn over
        _bits = []
        for i in range(height):
            for j in range(width):
                _bits.append( bits[(height-1-i)*width+ j] )
        _bits = "".join(_bits)

        img = Image.frombuffer('RGBA', (width, height), _bits)
        return img

    def _screenshot(self, filepath):
        dirpath = os.path.dirname(os.path.abspath(filepath))
        if not os.path.exists(dirpath):
            os.makedirs(dirpath)
        self.image.SaveBitmapFile(self._memdc, filepath)
        time.sleep(0.5)

    def drag(self):
        pass


class WindowsDevice(DeviceMixin):
    def __init__(self, window_name=None, exe_file=None, **kwargs):
        DeviceMixin.__init__(self)
        self._win = Window(window_name, exe_file)

    def screenshot(self, filename=None):
        """Take screen snapshot

        Args:
            filename: filename where save to, optional

        Returns:
            PIL.Image object

        Raises:
            TypeError, IOError
        """
        img = self._win.pilimage
        if filename:
            img.save(filename)
        return img

    def click(self, x, y):
        """Simulate click within window screen.

        Args:
            x, y: int, pixel distance from window (left, top) as origin

        Returns:
            None
        """
        self._win._input_left_mouse(x, y)

    def text(self, text):
        """Simulate text input to window.

        Args:
            text: string

        Returns:
            None
        """
        self._win._input_keyboard(text)

    @property
    def display(self):
        """Display size in pixels."""
        w, h = self._win.size
        return collections.namedtuple('Display', ['width', 'height'])(w, h)