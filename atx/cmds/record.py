#-*- encoding: utf-8 -*-

import os
import sys
import traceback
import Tkinter as tk
import tkSimpleDialog
import tkMessageBox

mswindows = (sys.platform == "win32")

import win32api
import win32con
import win32gui

from atx.device.android import AndroidDevice
from atx.device.android_minicap import AndroidDeviceMinicap
from atx.device.windows import WindowsDevice
from atx.record.android import AndroidRecorder
from atx.record.windows import WindowsRecorder

__dir__ = os.path.dirname(os.path.abspath(__file__))

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
        try:
            class_atom = win32gui.RegisterClass(wc)
        except:
            pass
        self.hwnd = win32gui.CreateWindow(wc.lpszClassName, "", win32con.WS_POPUP, 0,0,1,1, 0, 0, hinst, None)
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
        # win32gui.PostMessage(self.parent, win32con.WM_CLOSE, 0, 0)
        return True

    def on_command(self, hwnd, msg, wp, lp):
        print 1111111
        cid = win32api.LOWORD(wp)
        if not self.commands.get(cid):
            print "Unknown command -", cid
            return
        _, func = self.commands[cid]
        try:
            func()
        except Exception as e:
            traceback.print_exc()
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

    # def create_menu(self, menu, menu_options):
    #     for option_text, option_icon, option_action, option_id in menu_options[::-1]:
    #         if option_icon:
    #             option_icon = self.prep_menu_icon(option_icon)
            
    #         if option_id in self.menu_actions_by_id:                
    #             item, extras = win32gui_struct.PackMENUITEMINFO(text=option_text,
    #                                                             hbmpItem=option_icon,
    #                                                             wID=option_id)
    #             win32gui.InsertMenuItem(menu, 0, 1, item)
    #         else:
    #             submenu = win32gui.CreatePopupMenu()
    #             self.create_menu(submenu, option_action)
    #             item, extras = win32gui_struct.PackMENUITEMINFO(text=option_text,
    #                                                             hbmpItem=option_icon,
    #                                                             hSubMenu=submenu)
    #             win32gui.InsertMenuItem(menu, 0, 1, item)

class SelectDeviceDialog(tkSimpleDialog.Dialog):
    def body(self, master):
        print 'SelectDeviceDialog'
        box = tk.Frame(master)
        self.btn_and = tk.Button(box, text='Android', command=self.show_android_device)
        self.btn_and.pack(side=tk.LEFT, padx=10)
        self.btn_win = tk.Button(box, text='Windows', command=self.show_windows_device)
        self.btn_win.pack(side=tk.LEFT, padx=10)
        box.pack()
        self.listbox = tk.Listbox(master, width=50, height=10, selectmode=tk.SINGLE)
        self.listbox.pack()

        self.listbox.bind('<Double-Button-1>', self.ok)

        self.update_idletasks()
        self.show_android_device()

    def apply(self, event=None):
        sel = self.listbox.curselection()
        if not sel:
            return
        idx = sel[0]
        self.result = self.devices[idx]
        print self.result

    def show_android_device(self):
        self.btn_and.config(relief=tk.SUNKEN, state=tk.ACTIVE)
        self.btn_win.config(relief=tk.RAISED, state=tk.NORMAL)
        self.device_class = 'android'
        self.devices = ['sdfsfsf xiaomi IV', 'sdfsdfsf hasdf wx']
        self.listbox.delete(0, tk.END)
        for d in self.devices:
            self.listbox.insert(tk.END, d)

    def show_windows_device(self):
        self.btn_win.config(relief=tk.SUNKEN, state=tk.ACTIVE)
        self.btn_and.config(relief=tk.RAISED, state=tk.NORMAL)
        self.device_class = 'windows'
        self.devices = ['window-%d' % i for i in range(100)]
        self.listbox.delete(0, tk.END)
        for d in self.devices:
            self.listbox.insert(tk.END, d)

class RecorderGUI(object):
    def __init__(self, device=None):
        self._device = device
        self._recorder = None
        self.recording = False
        self._root = root = tk.Tk()

        root.protocol("WM_DELETE_WINDOW", self.destroy)

        self.tray = None
        def calllater():
            self.create_tray()

        tk.Button(root, text='choose', command=self.choose_device).pack()

        root.after(200, calllater)

        # no window for now.
        root.withdraw()

        # need to handle device event

    def create_tray(self):
        icon_path = os.path.join(__dir__, 'static', 'recorder.ico')
        commands  = [
            ('Choose Device', self.choose_device),
            ("Start Record", self.start_record),
            ("Stop Record", self.stop_record),
        ]
        tray = SystemTray(self._root.winfo_id(), "recorder", commands, icon_path)
        self.tray = tray
        tray.balloon('hello')
        win32gui.PumpMessages()
        self.tray = None

    def destroy(self):
        print "root destroy"
        if self._recorder is not None:
            self._recorder.stop()
        self._root.destroy()
        win32api.PostQuitMessage(0)

    def mainloop(self):
        try:
            self._root.mainloop()
        except KeyboardInterrupt:
            self.destroy()

    def choose_device(self, event=None):
        print 1111111, self.tray
        win32gui.PostMessage(self.tray.hwnd, win32con.WM_CLOSE, 0, 0)
        # self.tray.destroy()
        # self._root.deiconify()
        d = SelectDeviceDialog(self._root)
        self.create_tray()
        print d.result

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
            elif isinstance(self._device, (AndroidDevice, AndroidDeviceMinicap)):
                record_class = AndroidRecorder
            else:
                print "Unknown device type", type(self._device)
                return False
            self._recorder = record_class(self._device)
        return True

def main():
    w = RecorderGUI()
    w.mainloop()  

if __name__ == '__main__':
    main()
