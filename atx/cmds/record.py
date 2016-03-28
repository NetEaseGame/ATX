#-*- encoding: utf-8 -*-

import os
import sys
import time
import Tkinter as tk

import pyHook

import threading
import win32gui
import win32api
import win32con

__dir__ = os.path.dirname(os.path.abspath(__file__))

class SystemTray(object):
    def __init__(self, parent, name, icon_path=None):
        self.parent = parent
        self.name = name
        self.WM_NOTIFY = win32con.WM_USER+20
        self.next_command_id = 1000
        self.commands = {}

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
        
    def balloon(self, msg, title=""):
        flags = win32gui.NIF_ICON | win32gui.NIF_MESSAGE | win32gui.NIF_TIP | win32gui.NIF_INFO
        nid = (self.hwnd, 0, flags, self.WM_NOTIFY, self.hicon, self.name, msg, 300, title)
        win32gui.Shell_NotifyIcon(win32gui.NIM_MODIFY, nid)

    def register_command(self, func, path=".", type=""):
        cid = self.next_command_id
        self.next_command_id += 1
        return cid

    def on_destroy(self, hwnd, msg, wp, lp):
        win32gui.PostMessage(self.parent, win32con.WM_CLOSE, 0, 0)
        win32gui.Shell_NotifyIcon(win32gui.NIM_DELETE, (self.hwnd, 0))

    def on_command(self, hwnd, msg, wp, lp):
        print "on_command"
        cid = win32api.LOWORD(wp)
        if cid == 1023:
            print "hehe"
        elif cid == 1024:
            print "Hello"
        elif cid == 1025:
            win32gui.DestroyWindow(self.hwnd)
        else:
            print "Unknown command -", cid

    def on_tray_notify(self, hwnd, msg, wp, lp):
        if lp == win32con.WM_LBUTTONUP:
            print "left click"
            win32gui.SetForegroundWindow(self.hwnd)
        elif lp == win32con.WM_RBUTTONUP:
            print "right click"
            menu = win32gui.CreatePopupMenu()
            win32gui.AppendMenu( menu, win32con.MF_STRING, 1023, "Display Dialog")
            win32gui.AppendMenu( menu, win32con.MF_STRING, 1024, "Say Hello")
            win32gui.AppendMenu( menu, win32con.MF_STRING, 1025, "Exit" )
            pos = win32gui.GetCursorPos()
            win32gui.SetForegroundWindow(self.hwnd)
            win32gui.TrackPopupMenu(menu, win32con.TPM_LEFTALIGN, pos[0], pos[1], 0, self.hwnd, None)
            win32gui.PostMessage(self.hwnd, win32con.WM_NULL, 0, 0)
        return True

class RecorderGUI(object):
    def __init__(self):
        self._root = root = tk.Tk()

        def _destroy():
            print "root destroy"
            root.destroy()
        root.protocol("WM_DELETE_WINDOW", _destroy)

        def calllater():
            icon_path = os.path.join(__dir__, 'static', 'recorder.ico')
            tray = SystemTray(root.winfo_id(), "recorder", icon_path)
            tray.balloon('hello')

        root.after(300, calllater)

        ## no window for now.
        root.withdraw()

    def mainloop(self):
        self._root.mainloop()

def hook():
    def on_mouse(event):
        if event.MessageName == "mouse move":
            return True
        print event.MessageName, event.Window, event.WindowName, event.Position, event.Wheel
        return True

    def on_keyboard(event):
        print event.Window, event.WindowName, event.Message, Event.Time
        print "\t", repr(event.Ascii), event.KeyId, event.ScanCode, event.flags
        print "\t", event.Key, event.Extended, event.Injected, event.Alt, event.Transition
        return True

    hm = pyHook.HookManager()
    hm.MouseAll = on_mouse
    hm.KeyAll = on_keyboard
    hm.HookMouse()
    hm.HookKeyboard()

if __name__ == '__main__':
    r = RecorderGUI()
    # hook()
    r.mainloop()
