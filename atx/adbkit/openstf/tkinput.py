#-*- encoding: utf-8 -*-

import sys
import Tkinter as tk

import service
import keycode

if sys.platform == 'win32':
    from ctypes import wintypes, byref, windll
    import win32con

    def handle_hotkey(root, callback):
        msg = wintypes.MSG()
        if windll.user32.GetMessageA(byref(msg), None, 0, 0) != 0:
            if msg.message == win32con.WM_HOTKEY:
                if msg.wParam == 1:
                    print 'Hotkey triggered!'
                    callback()
        windll.user32.TranslateMessage(byref(msg))
        windll.user32.DispatchMessageA(byref(msg))
        root.after(1, handle_hotkey, root, callback)

    # hotkey map refs: https://msdn.microsoft.com/en-us/library/windows/desktop/dd375731(v=vs.85).aspx
    # not yet used here.
    def register_hotkey(root, key, callback):
        key = key.split('-')
        mod = 0
        if 'Ctrl' in key:
            mod |= win32con.MOD_CONTROL
        if 'Shift' in key:
            mod |= win32con.MOD_SHIFT
        if 'Alt' in key:
            mod |= win32con.MOD_ALT
        key = key[-1].upper()
        assert key in 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
        if windll.user32.RegisterHotKey(None, 1, mod, ord(key)) != 0:
            print("Hotkey registered!")
            handle_hotkey(root, callback)

else:
    def register_hotkey(root, key, callback):
        print 'Register hotkey failed.'

def main():
    service.start()

    root = tk.Tk()
    root.resizable(0, 0)
    root.title('STF Input')
    sv = tk.StringVar()

    if sys.platform == 'win32':
        backspace = '\x08'
    else:
        backspace = '\x7f'

    def send(event, sv=sv):
        char = event.char
        if not char:
            return
        text = sv.get()
        if char == '\r' and text: # use <Return> to input
            service.type(text)
            sv.set('')
            return
        if char == backspace and text: #  use <Backspace> to delete, <Del> not avaialable.
            sv.set('')
            return
        if char == '\x16': # skip <Ctrl-V>
            service.keyboard(char)
            sv.set('')
            return 'break'
        if char in keycode.KEYBOARD_KEYS or char in keycode.CTRLED_KEYS:
            service.keyboard(char)

    entry = tk.Entry(root, textvariable=sv)
    entry.pack()
    entry.focus_set()
    entry.bind('<Key>', send)

    state = [1]
    def toggle(root=root, entry=entry):
        if state[0] == 0:
            root.deiconify()
            entry.focus_set()
            state[0] = 1
        else:
            root.withdraw()
            state[0] = 0

    register_hotkey(root, 'Ctrl-Alt-Z', toggle) # not very well with IME

    try:
        root.mainloop()
    finally:
        service.stop()

if __name__ == '__main__':
    main()