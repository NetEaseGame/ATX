#!/usr/bin/env python

# USAGE
# python click_and_crop.py --image jurassic_park_kitchen.jpg

# import the necessary packages
import os
import sys
import argparse
import threading
import Tkinter
import tkSimpleDialog
import collections
from Queue import Queue
from StringIO import StringIO
import cv2
from PIL import ImageTk, Image

import atx


Point = collections.namedtuple('Point', ['x', 'y'])

def cv2_to_pil(image):
    img_str = cv2.imencode('.png', image)[1].tostring()
    return Image.open(StringIO(img_str))


def make_mouse_callback(imgs, ref_pt):
    # initialize the list of reference points and boolean indicating
    # whether cropping is being performed or not
    cropping = [False]

    def _click_and_crop(event, x, y, flags, param):
        # grab references to the global variables
        # global ref_pt, cropping

        # if the left mouse button was clicked, record the starting
        # (x, y) coordinates and indicate that cropping is being
        # performed
        if event == cv2.EVENT_LBUTTONDOWN:
            ref_pt[0] = Point(x, y)
            cropping[0] = True

        # check to see if the left mouse button was released
        elif event == cv2.EVENT_LBUTTONUP:
            # record the ending (x, y) coordinates and indicate that
            # the cropping operation is finished
            ref_pt[1] = Point(x, y)
            cropping[0] = False

            # draw a rectangle around the region of interest
            imgs[1] = image = imgs[0].copy()
            cv2.rectangle(image, ref_pt[0], ref_pt[1], (0, 255, 0), 2)
            cv2.imshow("image", image)
        elif event == cv2.EVENT_MOUSEMOVE and cropping[0]:
            img2 = imgs[0].copy()
            cv2.rectangle(img2, ref_pt[0], (x, y), (0, 255, 0), 2)
            imgs[1] = image = img2
            cv2.imshow("image", image)
    return _click_and_crop

def interactive_save(image): #, save_to=None):
    imgpil = cv2_to_pil(image)
    #img_str = cv2.imencode('.png', image)[1].tostring()
    #imgpil = Image.open(StringIO(img_str))

    root = Tkinter.Tk()
    root.geometry('{}x{}'.format(400, 400))
    imgtk = ImageTk.PhotoImage(image=imgpil)
    panel = Tkinter.Label(root, image=imgtk) #.pack()
    panel.pack(side="bottom", fill="both", expand="yes")
    
    # if not save_to:
    save_to = tkSimpleDialog.askstring("Save cropped image", "Enter filename")
    if save_to:
        if save_to.find('.') == -1:
            save_to += '.png'
        print 'Save to:', save_to
        cv2.imwrite(save_to, image)
    root.destroy()

def long_task(secs=2):
    import time
    time.sleep(secs)
    print 'hello'

def worker(que):
    while True:
        (func, args, kwargs) = que.get()
        try:
            func(*args, **kwargs)
        except Exception as e:
            print e
        finally:
            que.task_done()

def simple_ide():
    que = Queue()
    que.put((long_task, (), {}))

    th = threading.Thread(name='worker', target=worker, args=(que,))
    th.daemon = True
    th.start()

    root = Tkinter.Tk()
    root.geometry('{}x{}'.format(400, 400))
    btn_hello = Tkinter.Button(root, text="Hello!")
    #btn_hello.set_text("World")
    btn_hello.pack()
    root.mainloop()

def main():
    # construct the argument parser and parse the arguments
    #simple_ide()
    ap = argparse.ArgumentParser()
    ap.add_argument("-s", "--serial", required=False, help="Android serialno")
    # ap.add_argument("-o", "--output", required=True, help="Output image file, ext must be png")
    args = vars(ap.parse_args())

    d = atx.connect(args["serial"])
    origin = d.screenshot()

    # load the image, clone it, and setup the mouse callback function
    # origin = cv2.imread(output)
    image = cv2.resize(origin, (0, 0), fx=0.5, fy=0.5) 
    images = [image.copy(), image]
    ref_pt = [None, None]
    
    cv2.namedWindow("image")
    cv2.setMouseCallback("image", make_mouse_callback(images, ref_pt))

    while True:
        # display the image and wait for a keypress
        cv2.imshow("image", images[1])
        key = cv2.waitKey(1) & 0xFF

        # if the 'c' key is pressed, break from the loop
        if key == ord("r"):
            origin = d.screenshot()
            image = cv2.resize(origin, (0, 0), fx=0.5, fy=0.5) 
            images[0] = image.copy()
            images[1] = image
        if key == ord("c"):
            if ref_pt[1] is None:
                continue
            (a, b) = ref_pt
            a = Point(a.x*2, a.y*2)
            b = Point(b.x*2, b.y*2)
            roi = origin[a.y:b.y, a.x:b.x]
            interactive_save(roi)
        elif key == ord("q"):
            break

    # close all open windows
    cv2.destroyAllWindows()

if __name__ == '__main__':
    main()
