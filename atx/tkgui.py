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

import threading
import Tkinter as tk
import tkSimpleDialog
import tkFileDialog
from Queue import Queue

import atx
from PIL import Image, ImageTk


def insert_code(filename, code, save=True, marker='# ATX CODE'):
    """ Auto append code """
    content = ''
    for line in open(filename, 'rb'):
        if line.strip() == marker:
            cnt = line.find(marker)
            content += line[:cnt] + code
        content += line
    if save:
        with open(filename, 'wb') as f:
            f.write(content)
    return content

class CropIDE(object):
    def __init__(self, title='AirtestX Basic GUI', device=None):
        self._device = device
        self._root = tk.Tk()
        self._root.title(title)
        self._queue = Queue()

        self._refresh_text = tk.StringVar()
        self._refresh_text.set("Refresh")
        self._gencode_text = tk.StringVar()
        self._attachfile_text = tk.StringVar()

        self._init_items()
        self._init_thread()

        self._lastx = 0
        self._lasty = 0
        self._bounds = None # crop area
        self._center = (0, 0) # center point
        self._offset = (0, 0) # offset to image center
        self._size = (90, 90)
        self._moved = False # click or click and move
        self._color = 'red' # draw color
        self._tkimage = None # keep reference
        self._image = None
        self._ratio = 0.5

    def _init_items(self):
        root = self._root
        root.resizable(0, 0)

        frm_control = tk.Frame(root, bg='#bbb')
        frm_control.grid(column=0, row=0, padx=5, sticky=tk.NW)
        frm_screen = tk.Frame(root, bg='#aaa')
        frm_screen.grid(column=1, row=0)

        frm_ctrl_btns = tk.Frame(frm_control)
        frm_ctrl_btns.grid(column=0, row=0, sticky=tk.W)
        tk.Label(frm_control, text='-'*30).grid(column=0, row=1, sticky=tk.EW)
        frm_ctrl_code = tk.Frame(frm_control)
        frm_ctrl_code.grid(column=0, row=2, sticky=tk.EW)

        tk.Button(frm_ctrl_btns, textvariable=self._refresh_text, command=self._redraw).grid(column=0, row=0, sticky=tk.W)
        tk.Button(frm_ctrl_btns, text="Wakeup", command=self._device.wakeup).grid(column=0, row=1, sticky=tk.W)
        tk.Button(frm_ctrl_btns, text="Save cropped", command=self._save_crop).grid(column=0, row=2, sticky=tk.W)

        tk.Label(frm_ctrl_code, text='Generated code').grid(column=0, row=0, sticky=tk.W)
        tk.Entry(frm_ctrl_code, textvariable=self._gencode_text, width=30).grid(column=0, row=1, sticky=tk.W)
        tk.Button(frm_ctrl_code, text='Run code', command=self._run_code).grid(column=0, row=2, sticky=tk.W)
        tk.Button(frm_ctrl_code, text='Insert and Run', command=self._run_and_insert).grid(column=0, row=3, sticky=tk.W)
        tk.Button(frm_ctrl_code, text='Select File', command=self._run_selectfile).grid(column=0, row=4, sticky=tk.W)
        tk.Label(frm_ctrl_code, textvariable=self._attachfile_text).grid(column=0, row=5, sticky=tk.W)

        self.canvas = tk.Canvas(frm_screen, bg="blue", bd=0, highlightthickness=0, relief='ridge')
        self.canvas.grid(column=0, row=0, padx=10, pady=10)
        self.canvas.bind("<Button-1>", self._stroke_start)
        self.canvas.bind("<B1-Motion>", self._stroke_move)
        self.canvas.bind("<B1-ButtonRelease>", self._stroke_done)

    def _worker(self):
        que = self._queue
        while True:
            (func, args, kwargs) = que.get()
            try:
                func(*args, **kwargs)
            except Exception as e:
                print e
            finally:
                que.task_done()
    
    def _run_async(self, func, args=(), kwargs={}):
        self._queue.put((func, args, kwargs))

    def _init_thread(self):
        th = threading.Thread(name='thread', target=self._worker)
        th.daemon = True
        th.start()

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
            if self._offset == (0, 0):
                self._gencode_text.set('click_image("%s")' % save_to)
            else:
                code = 'click_image(atx.Pattern("{name}", offset=({x}, {y})))'.format(
                    name=save_to, x=self._offset[0], y=self._offset[1])
                self._gencode_text.set(code)

    def _run_code(self):
        code = 'self._device.'+self._gencode_text.get()
        exec(code)

    def _run_and_insert(self):
        self._run_code()
        filename = self._attachfile_text.get().strip()
        code_snippet = self._gencode_text.get().strip()
        if filename and code_snippet:
            insert_code(filename, code_snippet+'\n')

    def _run_selectfile(self):
        filename = tkFileDialog.askopenfilename(**dict(
            filetypes=[('All files', '.*'), ('Python', '.py')],
            title='Select file'))
        self._attachfile_text.set(filename)
        print filename

    def _redraw(self):
        def foo():
            image = self._device.screenshot()
            self.draw_image(image)
            self._refresh_text.set("Refresh")

        self._run_async(foo)
        self._refresh_text.set("Refreshing ...")
        self._reset()

    def _reset(self):
        self._bounds = None
        self._offset = (0, 0)
        self._center = (0, 0)
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
            self._offset = (0, 0)
        elif self._bounds is None:
            # print x, y
            self._gencode_text.set('click(%d, %d)' % (x/self._ratio, y/self._ratio))
        elif self._bounds is not None:
            (x0, y0, x1, y1) = self._fix_bounds(self._bounds)
            cx, cy = (x/self._ratio, y/self._ratio)
            mx, my = (x0+x1)/2, (y0+y1)/2
            self._offset = (offx, offy) = map(int, (cx-mx, cy-my))
            self._gencode_text.set('offset=(%d, %d)' % (offx, offy))
        # print self._bounds
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
        

def main(serial, **kwargs):
    d = atx.connect(serial, **kwargs)
    gui = CropIDE('AirtestX IDE SN: %s' % serial, device=d) #screenshot=d.screenshot)
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
    main(None)
    # test()
