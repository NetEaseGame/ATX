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

root = tk.Tk()
root.title("AirtestX Basic GUI")

frm_control = tk.Frame(root, bg='blue')
frm_control.grid(column=0, row=0)
frm_screen = tk.Frame(root, bg='red')
frm_screen.grid(column=0, row=1)

tk.Button(frm_control, text="Refresh").grid(column=0, row=0, sticky=tk.W)
tk.Button(frm_control, text="Save crop").grid(column=1, row=0, sticky=tk.W)

canvas = tk.Canvas(frm_screen, bg="blue", bd=0, highlightthickness=0, relief='ridge')
# canvas.pack(fill=tk.BOTH, expand=tk.YES)
canvas.grid(column=0, row=0)
background = Image.open('jurassic_park_kitchen.jpg')
(width, height) = background.size
canvas.config(width=width, height=height)

background = ImageTk.PhotoImage(background)
canvas.create_image(0, 0, anchor=tk.NW, image=background)

# canvas.create_line(0, 0, 200, 100)
# canvas.create_line(0, 100, 200, 0, fill="red", dash=(4, 4))

canvas.create_rectangle(100, 25, 150, 75)#, fill="blue")
print (width, height)

lastx, lasty = 0, 0
color = 'red'
def xy(event):
    global lastx, lasty
    lastx, lasty = canvas.canvasx(event.x), canvas.canvasy(event.y)


def add_line(event):
    global lastx, lasty
    x, y = canvas.canvasx(event.x), canvas.canvasy(event.y)
    canvas.create_line((lastx, lasty, x, y), fill=color, width=5, tags='currentline')
    lastx, lasty = x, y

def doneStroke(event):
    canvas.itemconfigure('currentline', width=2)        
        
canvas.bind("<Button-1>", xy)
canvas.bind("<B1-Motion>", add_line)
canvas.bind("<B1-ButtonRelease>", doneStroke)

# mainframe = ttk.Frame(root, padding="3 3 12 12")
root.mainloop()