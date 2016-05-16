#!/usr/bin/env python
# coding: utf-8
#
# Usage: python -matx screenrecord -o out.avi

import time
import traceback
import cv2

from atx import adb2 as adb

def main(scale=0.5):
    adb.use_openstf()
    img = adb.screenshot()
    while img is None:
        time.sleep(1)
        img = adb.screenshot()

    while True:
        try:
            img = adb.screenshot()
            h, w = img.shape[:2]
            h, w = int(h*scale), int(w*scale)
            img = cv2.resize(img, dsize=(w, h))
            cv2.imshow('screen', img)
            cv2.waitKey(10)
        except KeyboardInterrupt:
            print 'Done'
            break
        except:
            traceback.print_exc()
            break

if __name__ == '__main__':
    main()