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
from PIL import Image, ImageTk

class CropIDE(object):
    def __init__(self, title='AirtestX Basic GUI'):
        self._root = tk.Tk()
        self._init_items()
        self._root.title(title)
        self._lastx = 0
        self._lasty = 0
        self._color = 'red'
        self._image = None

    def _init_items(self):
        root = self._root
        frm_control = tk.Frame(root, bg='blue')
        frm_control.grid(column=0, row=0)
        frm_screen = tk.Frame(root, bg='red')
        frm_screen.grid(column=0, row=1)

        tk.Button(frm_control, text="Refresh", command=self._reset).grid(column=0, row=0, sticky=tk.W)
        tk.Button(frm_control, text="Save crop").grid(column=1, row=0, sticky=tk.W)

        self.canvas = tk.Canvas(frm_screen, bg="blue", bd=0, highlightthickness=0, relief='ridge')
        self.canvas.grid(column=0, row=0)
        self.canvas.bind("<Button-1>", self._xy)
        self.canvas.bind("<B1-Motion>", self._add_line)
        self.canvas.bind("<B1-ButtonRelease>", self._done_stroke)

    def _reset(self):
        self.canvas.delete('currentline')

    def _xy(self, event):
        c = self.canvas
        self._lastx, self._lasty = c.canvasx(event.x), c.canvasy(event.y)
        print self._lastx, self._lasty

    def _add_line(self, event):
        self._reset()
        c = self.canvas
        x, y = c.canvasx(event.x), c.canvasy(event.y)
        c.create_rectangle(self._lastx, self._lasty, x, y, 
            tags='currentline', width=5)#, fill="blue")
        c.create_line((self._lastx, self._lasty, x, y), fill=self._color, width=2, tags='currentline', dash=(4, 4))
        c.create_line((self._lastx, y, x, self._lasty), fill=self._color, width=2, tags='currentline', dash=(4, 4))
        # self._lastx, self._lasty = x, y

    def _done_stroke(self, event):
        self.canvas.itemconfigure('currentline', width=2)

    def draw_image(self, image):
        tkimage = ImageTk.PhotoImage(image)
        (width, height) = image.size
        self._image = tkimage # keep a reference
        self.canvas.config(width=width, height=height)
        self.canvas.create_image(0, 0, anchor=tk.NW, image=tkimage)

    def mainloop(self):
        self._root.mainloop()
        

def main():
    gui = CropIDE('Simple IDE')
    image = Image.open('jurassic_park_kitchen.jpg')
    # (width, height) = image.size
    # tkimage = ImageTk.PhotoImage(image)
    # gui.canvas.create_image(0, 0, anchor=tk.NW, image=tkimage)
    gui.draw_image(image)
    # gui.canvas.create_line(0, 100, 200, 0, fill="red", dash=(4, 4))
    gui.mainloop()


if __name__ == '__main__':
    main()
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
#     canvas.create_line((lastx, lasty, x, y), fill=color, width=5, tags='currentline')
#     lastx, lasty = x, y

# def doneStroke(event):
#     canvas.itemconfigure('currentline', width=2)      
        
# canvas.bind("<Button-1>", xy)
# canvas.bind("<B1-Motion>", add_line)
# canvas.bind("<B1-ButtonRelease>", doneStroke)

# # mainframe = ttk.Frame(root, padding="3 3 12 12")
# root.mainloop()