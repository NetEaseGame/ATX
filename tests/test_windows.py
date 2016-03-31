#-*- encoding: utf-8 -*-

import os
import time

from atx.device.windows import Window, FrozenWindow, WindowsDevice


# def _input_left_mouse(self, x, y):
#     left, top, right, bottom = self.position
#     width, height = right - left, bottom - top
#     if x < 0 or x > width or y < 0 or y > height:
#         return

#     win32gui.SetForegroundWindow(self._handle)
#     pos = win32gui.GetCursorPos()
#     win32api.SetCursorPos((left+x, top+y))
#     win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, 0, 0)
#     win32api.Sleep(100) #ms
#     win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, 0, 0)
#     win32api.Sleep(100) #ms
#     win32api.SetCursorPos(pos)

# def drag(self):
#     pass

# def _input_keyboard(self, text):
#     pass


def test():
    try:
        name = u"Windows 任务管理器"
        win = FrozenWindow(name.encode("gbk"), exclude_border=True)
        win.set_foreground()
        time.sleep(0.1)
        win._screenshot('taskman-pil.png')
        time.sleep(0.5)
        win._screenshot_cv2('taskman-cv2.png')
    except Exception as e:
        print str(e)

    try:
        filepath = "C:\\Windows\\System32\\calc.exe"
        win = Window(exe_file=filepath)
        win.set_foreground()
        time.sleep(0.1)
        win._screenshot('calc-pil.png')
        time.sleep(0.5)
        win._screenshot_cv2('calc-cv2.png')
    except Exception as e:
        print str(e)

    dev = WindowsDevice()
    dev.screenshot('screen.png')

if __name__ == '__main__':
    test() 