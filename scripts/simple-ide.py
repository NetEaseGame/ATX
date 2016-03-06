# USAGE
# python click_and_crop.py --image jurassic_park_kitchen.jpg

# import the necessary packages
import argparse
import cv2
import Tkinter
import tkSimpleDialog
from PIL import ImageTk, Image
from StringIO import StringIO


def make_mouse_callback(imgs, ref_pt):
    # initialize the list of reference points and boolean indicating
    # whether cropping is being performed or not
    cropping = [False]
    clone = imgs[0]

    def _click_and_crop(event, x, y, flags, param):
        # grab references to the global variables
        # global ref_pt, cropping

        # if the left mouse button was clicked, record the starting
        # (x, y) coordinates and indicate that cropping is being
        # performed
        if event == cv2.EVENT_LBUTTONDOWN:
            ref_pt[0] = (x, y)
            cropping[0] = True

        # check to see if the left mouse button was released
        elif event == cv2.EVENT_LBUTTONUP:
            # record the ending (x, y) coordinates and indicate that
            # the cropping operation is finished
            ref_pt[1] = (x, y)
            cropping[0] = False

            # draw a rectangle around the region of interest
            imgs[1] = image = clone.copy()
            cv2.rectangle(image, ref_pt[0], ref_pt[1], (0, 255, 0), 2)
            cv2.imshow("image", image)
        elif event == cv2.EVENT_MOUSEMOVE and cropping[0]:
            img2 = clone.copy()
            cv2.rectangle(img2, ref_pt[0], (x, y), (0, 255, 0), 2)
            imgs[1] = image = img2
            cv2.imshow("image", image)
    return _click_and_crop

def interactive_save(image):
    img_str = cv2.imencode('.png', image)[1].tostring()
    imgpil = Image.open(StringIO(img_str))

    root = Tkinter.Tk()
    root.geometry('{}x{}'.format(400, 400))
    imgtk = ImageTk.PhotoImage(image=imgpil)
    panel = Tkinter.Label(root, image=imgtk) #.pack()
    panel.pack(side="bottom", fill="both", expand="yes")
    Tkinter.Button(root, text="Hello!").pack()
    save_to = tkSimpleDialog.askstring("Save cropped image", "Enter filename")
    if save_to:
        if save_to.find('.') == -1:
            save_to += '.png'
        print 'Save to:', save_to
        cv2.imwrite(save_to, image)
    root.destroy()

def main():
    # construct the argument parser and parse the arguments
    ap = argparse.ArgumentParser()
    ap.add_argument("-i", "--image", required=True, help="Path to the image")
    args = vars(ap.parse_args())

    # load the image, clone it, and setup the mouse callback function
    image = cv2.imread(args["image"])
    clone = image.copy()
    images = [clone, image]
    ref_pt = [None, None]
    
    cv2.namedWindow("image")
    cv2.setMouseCallback("image", make_mouse_callback(images, ref_pt))

    # keep looping until the 'q' key is pressed
    while True:
        # display the image and wait for a keypress
        cv2.imshow("image", images[1])
        key = cv2.waitKey(1) & 0xFF

        # if the 'c' key is pressed, break from the loop
        if key == ord("c"):
            if ref_pt[1] is None:
                continue
            roi = clone[ref_pt[0][1]:ref_pt[1][1], ref_pt[0][0]:ref_pt[1][0]]
            interactive_save(roi)
        elif key == ord("q"):
            break

    # if there are two reference points, then crop the region of interest
    # from teh image and display it

    # close all open windows
    cv2.destroyAllWindows()

if __name__ == '__main__':
    main()