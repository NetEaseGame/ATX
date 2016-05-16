#!/usr/bin/env python
# coding: utf-8
#
# Usage: python -matx screenrecord -o out.avi

import os
import time
import traceback
import cv2
import numpy as np
from atx import adb2 as adb

def main(output='out.avi', scale=0.5, portrait=False, overwrite=True, verbose=True):
    print output, scale, portrait, overwrite, verbose
    if os.path.exists(output):
        print 'output file exists!'
        if overwrite:
            print 'overwriting', output
            os.remove(output)
        else:
            return

    adb.use_openstf()
    img = adb.screenshot()
    while img is None:
        time.sleep(1)
        img = adb.screenshot()
    if verbose:
        cv2.imshow('screen', img)

    w, h = adb.display()
    w, h = int(w*scale), int(h*scale)
    framesize = (w, h) if portrait else (h, w)
    fps = 24.0
    # refs http://www.fourcc.org/codecs.php
    # avaiable fourccs: XVID, MJPG
    fourcc = cv2.cv.FOURCC(*'MJPG')
    writer = cv2.VideoWriter(output, fourcc, fps, framesize)

    # video (width, height), images should be resized to fit in video frame.
    vw, vh = framesize

    tic = time.clock()
    toc = time.clock()
    while True:
        time.sleep(1.0/fps - max(toc-tic, 0))
        tic = time.clock()
        try:
            img = adb.screenshot()
            h, w = img.shape[:2]
            if h*vw == w*vh:
                h, w = vh, vw
                frame = cv2.resize(img, dsize=(w, h))
            else:
                frame = np.zeros((vh, vw, 3), dtype=np.uint8)
                sh = vh*1.0/h
                sw = vw*1.0/w
                if sh < sw:
                    h, w = vh, int(sh*w)
                else:
                    h, w = int(sw*h), vw
                left, top = (vw-w)/2, (vh-h)/2
                frame[top:top+h, left:left+w, :] = cv2.resize(img, dsize=(w, h))

            writer.write(frame)
            toc = time.clock()
            if verbose:
                cv2.imshow('screen', frame)
                cv2.waitKey(1)
        except KeyboardInterrupt:
            print 'Done'
            break
        except:
            traceback.print_exc()
            break
    writer.release()

if __name__ == '__main__':
    main()