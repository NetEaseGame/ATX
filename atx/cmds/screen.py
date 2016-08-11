#!/usr/bin/env python
# coding: utf-8
#
# Usage: python -matx screen [-s 0.8]

import os
import time
import traceback
import cv2
from functools import partial

from atx.adbkit.client import Client
from atx.adbkit.device import Device
from atx.adbkit.mixins import MinicapStreamMixin, RotationWatcherMixin, MinitouchStreamMixin

class AdbWrapper(RotationWatcherMixin, MinicapStreamMixin, MinitouchStreamMixin, Device):
    def __init__(self, *args, **kwargs):
        super(self.__class__, self).__init__(*args, **kwargs)

        self._display = self.display
        def on_rotation_change(v):
            self.open_minicap_stream()
            self._display = self.display

        self.open_rotation_watcher(on_rotation_change=on_rotation_change)
        self.open_minitouch_stream()

    def send_touch(self, cmd):
        self._MinitouchStreamMixin__touch_queue.put(cmd)

    def input(self, char):
        self.shell('input', 'text', char)

def get_adb(host, port, serial):
    client = Client(host, port)
    if serial is None:
        serial = list(client.devices().keys())[0]
    return AdbWrapper(client, serial)

__dir__ = os.path.dirname(os.path.abspath(__file__))

def screen_with_controls(host, port, serial, scale=0.5):
    from PIL import Image, ImageTk
    import Tkinter as tk
    import tkFileDialog

    adb = get_adb(host, port, serial)

    class Screen(object):
        def __init__(self):
            self.root = tk.Tk()
            self.root.title('Sync Screen')
            # self.image = Image.open(os.path.join(__dir__, 'static', 'screen.png'))
            self.image = None
            self.tkimage = None
            self.canvas_image = None

            self.make_toolbar()
            self.make_canvas()

        def make_toolbar(self):
            # tools: capture, power, home, menu, back, volume_up, volume_down, turn_screen, keymapping_settings
            toolbar = tk.Frame(self.root)
            self.icons = [] # need to keep a reference for tk images. wtf.

            def capture():
                if self.image is None:
                    print 'Not initialized, try later.'
                    return
                d = tkFileDialog.asksaveasfilename(filetypes=(('Images', '*.png;*.jpg;'),), initialfile='screen.png')
                if not d: # canceled
                    return
                if not d.endswith('.png') and not d.endswith('.jpg'):
                    d += '.png'
                print 'Save to', d
                self.image.save(d)

            icon = ImageTk.PhotoImage(file=os.path.join(__dir__, 'static', 'icons', 'save.ico'))
            tk.Button(toolbar, image=icon, command=capture).pack(side=tk.LEFT, padx=2, pady=2)
            self.icons.append(icon)

            # def rotate():
            #     print 'rotate screen (Not Implemented yet.)'
            # icon = ImageTk.PhotoImage(file=os.path.join(__dir__, 'static', 'icons', 'rotate.ico'))
            # tk.Button(toolbar, image=icon, command=rotate).pack(side=tk.LEFT, padx=2, pady=2)
            # self.icons.append(icon)

            for key in ('power', 'home', 'menu', 'back', 'volume_up', 'volume_down'):
                icon = ImageTk.PhotoImage(file=os.path.join(__dir__, 'static', 'icons', '%s.ico' % key))
                self.icons.append(icon)
                b = tk.Button(toolbar, image=icon, command=lambda k=key:adb.keyevent('KEYCODE_%s' % k.upper()))
                b.pack(side=tk.LEFT, padx=2, pady=2)

            toolbar.pack(side=tk.TOP, fill=tk.X)

        def make_canvas(self):
            # screen canvas, bind mouse input & keyboard input
            self.canvas = tk.Canvas(self.root, bg='black', bd=0, highlightthickness=0)
            self.canvas.pack()

            def screen2touch(x, y):
                '''convert touch position'''
                w, h, o = adb._display
                if o == 0:
                    return x, y
                elif o == 1: # landscape-right
                    return w-y, x
                elif o == 2: # upsidedown
                    return w-x, h-y
                elif o == 3: # landscape-left
                    return y, h-x
                return x, y
            
            def on_mouse_down(event):
                self.canvas.focus_set()
                x, y = int(event.x/scale), int(event.y/scale)
                x, y = screen2touch(x, y)
                adb.send_touch('d 0 %d %d 30\nc\n' % (x, y))

            def on_mouse_up(event):
                adb.send_touch('u 0\nc\n')

            def on_mouse_drag(event):
                x, y = int(event.x/scale), int(event.y/scale)
                x, y = screen2touch(x, y)
                adb.send_touch('m 0 %d %d 30\nc\n' % (x, y))

            self.canvas.bind('<ButtonPress-1>', on_mouse_down)
            self.canvas.bind('<ButtonRelease-1>', on_mouse_up)
            self.canvas.bind('<B1-Motion>', on_mouse_drag)

            keymap = {'\r':'KEYCODE_ENTER', ' ':'KEYCODE_SPACE', '\x08':'KEYCODE_DEL', }

            def on_key(event):
                c = event.char
                # print 'key pressed', repr(c), type(c)
                if c in 'adbcdefghijklmnopqrstuvwxyz0123456789':
                    adb.input(c)
                    return 'break'
                if c in keymap:
                    adb.keyevent(keymap[c])
                    return 'break'

            self.canvas.bind('<Key>', on_key)

        def _refresh_screen(self):
            img = adb.screenshot_cv2()
            if scale != 1.0:
                h, w = img.shape[:2]
                h, w = int(scale*h), int(scale*w)
                img = cv2.resize(img, (w, h))

            self.image = Image.fromarray(img[:, :, ::-1])
            self.tkimage = ImageTk.PhotoImage(self.image)
            w, h = self.image.size
            self.canvas.config(width=w, height=h)
            if self.canvas_image is None:
                self.canvas_image = self.canvas.create_image(0, 0, anchor=tk.NW, image=self.tkimage)
            else:
                self.canvas.itemconfig(self.canvas_image, image=self.tkimage)

            self.root.after(10, self._refresh_screen)

        def run(self):
            self._refresh_screen()
            self.root.mainloop()

    s = Screen()

    img = adb.screenshot_cv2()
    while img is None:
        time.sleep(1)
        img = adb.screenshot_cv2()

    s.run()

def screen_simple(host, port, serial, scale=0.5):
    adb = get_adb(host, port, serial)

    img = adb.screenshot_cv2()
    while img is None:
        time.sleep(1)
        img = adb.screenshot_cv2()

    print 'Press Ctrl-C or Esc to quit.'

    winname = 'Sync Screen'
    cv2.namedWindow(winname)
    while True:
        try:
            img = adb.screenshot_cv2()
            if scale != 1.0:
                h, w = img.shape[:2]
                h, w = int(scale*h), int(scale*w)
                img = cv2.resize(img, (w, h))
            cv2.imshow(winname, img)
            key = cv2.waitKey(10)
            if key == 27: # Escape
                break
        except KeyboardInterrupt:
            print 'Done'
            break
        except:
            traceback.print_exc()
            break

    cv2.destroyWindow(winname)

def main(serial=None, host=None, port=None, scale=0.5, simple=False):
    '''interact'''
    if simple:
        screen_simple(host, port, serial, scale)
    else:
        screen_with_controls(host, port, serial, scale)

if __name__ == '__main__':
    main()