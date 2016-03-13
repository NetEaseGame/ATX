#!/usr/bin/env python
# coding: utf-8
#
# > How to get tkinter canvas to dynamically resize to window width?
# http://stackoverflow.com/questions/22835289/how-to-get-tkinter-canvas-to-dynamically-resize-to-window-width
#
# > Canvas tutoril
# http://www.tkdocs.com/tutorial/canvas.html
#
# > Canvas API reference
# http://effbot.org/tkinterbook/canvas.htm
#
# > Tutorial canvas tk
# http://www.tutorialspoint.com/python/tk_canvas.htm

import Tkinter as tk
import tkSimpleDialog
from PIL import Image, ImageTk

import atx


class CropIDE(object):
    def __init__(self, title='AirtestX Basic GUI', screenshot=None):
        self._root = tk.Tk()
        self._init_items()
        self._root.title(title)
        self._lastx = 0
        self._lasty = 0
        self._bounds = None # crop area
        self._center = (0, 0) # center point, used for offset
        self._size = (90, 90)
        self._moved = False # click or click and move
        self._color = 'red' # draw color
        self._tkimage = None # keep reference
        self._image = None
        self._screenshot = screenshot
        self._ratio = 0.5

    def _init_items(self):
        root = self._root
        frm_control = tk.Frame(root, bg='blue')
        frm_control.grid(column=0, row=0)
        frm_screen = tk.Frame(root, bg='#aaa')
        frm_screen.grid(column=0, row=1)

        tk.Button(frm_control, text="Refresh", command=self._redraw).grid(column=0, row=0, sticky=tk.W)
        tk.Button(frm_control, text="Save crop", command=self._save_crop).grid(column=1, row=0, sticky=tk.W)

        self.canvas = tk.Canvas(frm_screen, bg="blue", bd=0, highlightthickness=0, relief='ridge')
        self.canvas.grid(column=0, row=0, padx=10, pady=10)
        self.canvas.bind("<Button-1>", self._stroke_start)
        self.canvas.bind("<B1-Motion>", self._stroke_move)
        self.canvas.bind("<B1-ButtonRelease>", self._stroke_done)

    def _fix_bounds(self, bounds):
        bounds = [x/self._ratio for x in bounds]
        (x0, y0, x1, y1) = bounds
        if x0 > x1:
            x0, y0, x1, y1 = x1, y1, x0, y0
        # in case of out of bounds
        w, h = self._size
        x0 = max(0, x0)
        y0 = max(0, y0)
        x1 = min(w, x1)
        y1 = min(h, y1)
        return map(int, [x0, y0, x1, y1])

    def _save_crop(self):
        print self._bounds
        if self._bounds is None:
            return
        bounds = self._fix_bounds(self._bounds)
        print bounds
        save_to = tkSimpleDialog.askstring("Save cropped image", "Enter filename")
        if save_to:
            if save_to.find('.') == -1:
                save_to += '.png'
            print('Save to:', save_to)
            self._image.crop(bounds).save(save_to)
            # cv2.imwrite(save_to, image)

    def _redraw(self):
        image = self._screenshot()
        self.draw_image(image)
        self._bounds = None
        self._reset()

    def _reset(self):
        self.canvas.delete('boundsLine')
        self.canvas.delete('clickPosition')

    def _stroke_start(self, event):
        self._moved = False
        c = self.canvas
        self._lastx, self._lasty = c.canvasx(event.x), c.canvasy(event.y)
        print 'click:', self._lastx, self._lasty

    def _stroke_move(self, event):
        self._moved = True
        self._reset()
        c = self.canvas
        x, y = c.canvasx(event.x), c.canvasy(event.y)
        self._bounds = (self._lastx, self._lasty, x, y)
        self._draw_bounds(self._bounds)
        x, y = (self._lastx+x)/2, (self._lasty+y)/2
        self.tag_point(x, y)

    def _stroke_done(self, event):
        c = self.canvas
        x, y = c.canvasx(event.x), c.canvasy(event.y)
        if self._moved:
            x, y = (self._lastx+x)/2, (self._lasty+y)/2
        self._center = (x, y) # rember position
        self.tag_point(x, y)
        self.canvas.itemconfigure('boundsLine', width=2)

    def _draw_bounds(self, bounds):
        c = self.canvas
        (x0, y0, x1, y1) = self._bounds
        c.create_rectangle(x0, y0, x1, y1, outline=self._color, tags='boundsLine', width=5)#, fill="blue")
        # c.create_line((x0, y0, x1, y1), fill=self._color, width=2, tags='boundsLine', dash=(4, 4))
        # c.create_line((x0, y1, x1, y0), fill=self._color, width=2, tags='boundsLine', dash=(4, 4))

    def tag_point(self, x, y):
        # coord = 10, 50, 110, 150
        self.canvas.delete('clickPosition')
        r = max(min(self._size)/30*self._ratio, 5)
        self.canvas.create_line(x-r, y, x+r, y, width=2, fill=self._color, tags='clickPosition')
        self.canvas.create_line(x, y-r, x, y+r, width=2, fill=self._color, tags='clickPosition')
        # coord = x-r, y-r, x+r, y+r
        # self.canvas.create_oval(coord, fill='gray', stipple="gray50", tags='clickPosition')

    def draw_image(self, image):
        self._image = image
        self._size = (width, height) = image.size
        w, h = int(width*self._ratio), int(height*self._ratio)
        # print w, h
        image = image.copy()
        image.thumbnail((w, h), Image.ANTIALIAS)
        tkimage = ImageTk.PhotoImage(image)
        self._tkimage = tkimage # keep a reference
        self.canvas.config(width=w, height=h)
        self.canvas.create_image(0, 0, anchor=tk.NW, image=tkimage)

    def mainloop(self):
        self._root.mainloop()
        

def atx_ide(serial):
    d = atx.connect(serial)
    gui = CropIDE('AirtestX IDE SN: %s' % serial, screenshot=d.screenshot)
    gui.draw_image(d.screenshot())
    gui.mainloop()

def test():
    # image = Image.open('jurassic_park_kitchen.jpg')
    gui = CropIDE('AirtestX IDE')
    image = Image.open('screen.png')
    gui.draw_image(image)
    gui.tag_point(100, 100)
    # gui.canvas.create_rectangle(10, 60, 30, 70, fill="red", stipple="gray12")
    gui.mainloop()


if __name__ == '__main__':
    # main()
    # atx.connect().screenshot().save('screen.png')
    atx_ide(None)
    # test()
# canvas.create_line(0, 0, 200, 100)
# canvas.create_line(0, 100, 200, 0, fill="red", dash=(4, 4))

# canvas.create_rectangle(100, 25, 150, 75)#, fill="blue")
# print (width, height)

# lastx, lasty = 0, 0
# color = 'red'
# def xy(event):
#     global lastx, lasty
#     lastx, lasty = canvas.canvasx(event.x), canvas.canvasy(event.y)


# def add_line(event):
#     global lastx, lasty
#     x, y = canvas.canvasx(event.x), canvas.canvasy(event.y)
#     canvas.create_line((lastx, lasty, x, y), fill=color, width=5, tags='boundsLine')
#     lastx, lasty = x, y

# def doneStroke(event):
#     canvas.itemconfigure('boundsLine', width=2)      
        
# canvas.bind("<Button-1>", xy)
# canvas.bind("<B1-Motion>", add_line)
# canvas.bind("<B1-ButtonRelease>", doneStroke)

# # mainframe = ttk.Frame(root, padding="3 3 12 12")
# root.mainloop()