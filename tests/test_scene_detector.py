#-*- encoding: utf-8 -*-

import cv2
import time

from atx.device.android_minicap import AndroidDeviceMinicap
from atx.record.scene_detector import SceneDetector

def test_detect():
    dev = AndroidDeviceMinicap()
    dev._adb.start_minitouch()
    time.sleep(3)

    d = SceneDetector('txxscene')
    old, new = None, None
    while True:
        # time.sleep(0.3)
        screen = dev.screenshot_cv2()
        h, w = screen.shape[:2]
        img = cv2.resize(screen, (w/2, h/2))

        # find hsv
        hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
        hls = cv2.cvtColor(img, cv2.COLOR_BGR2HLS)
        _, _, V = cv2.split(hsv)
        V[V<150] = 0
        cv2.imshow('V', V)
        _, _, L = cv2.split(hls)
        L[L<150] = 0
        cv2.imshow('H', L)

        tic = time.clock()
        new = str(d.detect(img))
        t = time.clock() - tic
        if new != old:
            print 'change to', new
            print 'cost time', t
        old = new

        for _, r in d.current_scene:
            x, y, x1, y1 = r
            cv2.rectangle(img, (x,y), (x1,y1), (0,255,0) ,2)
        cv2.imshow('test', img)
        cv2.waitKey(1)

if __name__ == '__main__':
    test_detect()