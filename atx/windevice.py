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

def find_process_id(exe_file):
    exe_file = os.path.normpath(exe_file).lower()
    command = "wmic process get processid,commandline"
    for line in os.popen(command).read().lower().splitlines():
        line = line.split()
        if not line:
            continue
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
            raise DeviceNotFoundError("WindowsDevice not found!")

        # self._window_name = win32gui.GetWindowText(hwnd)
        # self._window_pid = pid
        # self._exe_file = exe_file
        self._handle = hwnd
        self._bmp = None
        self._windc = None
        self._memdc = None

    @property
    def position(self):
        return win32gui.GetWindowRect(self._handle)
        # return win32gui.GetClientRect(self._handle)

    @property
    def size(self):
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
        w, h = self.size
        s = len(_bits)

        bits = []
        for i in range(s/4):
            ## change to rpg here, by set alpha = -1
            bits.append(struct.pack('4b', _bits[4*i+2], _bits[4*i+1], _bits[4*i+0], -1))

        ## do a turn over
        _bits = []
        for i in range(h):
            for j in range(w):
                _bits.append( bits[(h-1-i)*w+ j] )
        _bits = "".join(_bits)

        img = Image.frombuffer('RGBA', (w, h), _bits)
        return img

    def screenshot(self, filepath):
        dirpath = os.path.dirname(os.path.abspath(filepath))
        if not os.path.exists(dirpath):
            os.makedirs(dirpath)
        self.image.SaveBitmapFile(self._memdc, filepath)
        time.sleep(0.5)

    def set_cursor(self):
        """show mouse position when cursor is inside window."""
        cur = win32gui.LoadCursor(0, win32con.IDC_CROSS)
        win32gui.SetCursor(cur)

    def drag(self):
        pass


    def test(self):
        # self.screenshot('screenshot.bmp')
        # self._input_left_mouse(300, 200)
        # self.screenshot('screenshot2.bmp')
        # self.pilimage.save('test.png')
        self.set_cursor()
        win32api.SetCursorPos((100, 100))


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

    def touch(self, x, y):
        """Touch specified position

        Args:
            x, y: int, pixel distance from window (left, top) as origin

        Returns:
            None
        """
        self.click(x, y)

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