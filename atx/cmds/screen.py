#!/usr/bin/env python
# coding: utf-8
#
# Usage: python -matx screen [-s 0.8]

import os
import time
import traceback
import cv2
from functools import partial
from atx import adb2 as adb

__dir__ = os.path.dirname(os.path.abspath(__file__))

def gui(scale=0.5):
    from PIL import Image, ImageTk
    import Tkinter as tk
    import tkFileDialog

    class Screen(object):
        def __init__(self):
            self.root = tk.Tk()
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

            def _screen2touch(w, h, x, y):
                '''convert touch position'''
                ori = adb.orientation()
                if ori == 0:
                    return x, y
                elif ori == 1: # landscape-right
                    return w-y, x
                elif ori == 2: # upsidedown
                    return w-x, h-y
                elif ori == 3: # landscape-left
                    return h-x, y
                return x, y
            
            w, h = adb.display()
            screen2touch = partial(_screen2touch, w, h)

            def on_mouse_down(event):
                self.canvas.focus_set()
                x, y = int(event.x/scale), int(event.y/scale)
                x, y = screen2touch(x, y)
                adb._mini.touchqueue.put('d 0 %d %d 30\nc\n' % (x, y))

            def on_mouse_up(event):
                adb._mini.touchqueue.put('u 0\nc\n')

            def on_mouse_drag(event):
                x, y = int(event.x/scale), int(event.y/scale)
                x, y = screen2touch(x, y)
                adb._mini.touchqueue.put('m 0 %d %d 30\nc\n' % (x, y))

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

        # def refresh_screen(self, screen):
        #     # refresh rate is about 0.03 second, cause flickering
        #     if screen is None:
        #         return
        #     t0 = time.time()
        #     h, w = screen.shape[:2]
        #     w, h = int(w*scale), int(h*scale)
        #     screen = cv2.resize(screen, (w, h))
        #     self.image = Image.fromarray(screen[:, :, ::-1])
        #     self.tkimage = ImageTk.PhotoImage(self.image)
            
        #     # # thumbnail is slow... around 0.16 second
        #     # w, h = self.image.size
        #     # image = self.image.copy()
        #     # image.thumbnail((w, h), Image.ANTIALIAS)
        #     # self.tkimage = ImageTk.PhotoImage(image)

        #     self.canvas.config(width=w, height=h)
        #     if self.canvas_image is None:
        #         self.canvas_image = self.canvas.create_image(0, 0, anchor=tk.NW, image=self.tkimage)
        #     else:
        #         self.canvas.itemconfig(self.canvas_image, image=self.tkimage)
        #     print time.time() - t0

        def _refresh_screen(self):
            self.image = adb.screenshot(scale=scale)
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

    adb.use_openstf(enabletouch=True)#, on_screenchange=s.refresh_screen)
    img = adb.screenshot()
    while img is None:
        time.sleep(1)
        img = adb.screenshot()

    s.run()

def simple(scale=0.5):
    adb.use_openstf()
    img = adb.screenshot(format='cv2')
    while img is None:
        time.sleep(1)
        img = adb.screenshot(format='cv2')

    print 'Press Ctrl-C or Esc to quit.'

    cv2.namedWindow('screen')
    while True:
        try:
            img = adb.screenshot(format='cv2', scale=scale)
            cv2.imshow('screen', img)
            key = cv2.waitKey(10)
            if key == 27: # Escape
                break
        except KeyboardInterrupt:
            print 'Done'
            break
        except:
            traceback.print_exc()
            break

    cv2.destroyWindow('screen')

def main(scale=0.5, controls=True):
    '''interact'''
    if not controls:
        simple(scale)
    else:
        gui(scale)

if __name__ == '__main__':
    main()