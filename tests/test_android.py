#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import cv2
import time
import numpy as np
import matplotlib.pyplot as plt
import scipy.fftpack
from cv2 import cv

def test_screenshot():
    from atx.device.android import AndroidDevice
    dev = AndroidDevice()
    print 'screen display:', dev.display
    # screen = dev._screenshot_uiauto()
    for i in range(10):
        t0 = time.clock()
        # screen = dev.screenshot()
        screen = dev._screenshot_minicap()
        print time.clock() - t0
    print dev.screenshot_method
    screen.save('tmp.png')

# def run_test():
#     d = SomeDevice()
#     d.connect() //setup info, screen
#     d.reset()

#     d.info.serial
#     d.info.wlan_ip
#     d.info.sreensize

#     d.screen = Screen(device)
#     d.screen.resolution                                 screen 1 thread
#     d.screen.orientation                                orientation 1 thread
#     d.screen.click(x, y)
#     d.screen.save('hello.png')
#     d.screen.region(l,t,w,h).save('region.png')
#     d.screen.search('xxx.png')
#     d.screen.exists('xxx.png')
#     d.screen.on()
#     d.screen.off()

#     # for android
#     d.keys.home()
#     d.keys.volup()
#     d.keys.voldown()

#     # for windows
#     d.text('hello')

#     ## short cuts
#     d.controls.install(pkg)     uiautomator.device.server.adb
#     d.controls.uninstall(pkg)
#     d.controls.startapp()
#     d.controls.stopapp()
#     d.controls.reboot()

#     # recorder.listener.start()
#     # recorder.listener.stop()
#     # recorder.listener.on_touch_down()                        listener 1 thread
#     # recorder.listener.on_touch_move()
#     # recorder.listener.on_touch_up()
#     # recorder.listener.on_click()
#     # recorder.listener.on_drag()

#     w = d.watcher()
#     w.wait('xxx.png', 5).click(x,y).expect('xxx.png', 3) --> Exception means fail
#     w.wait(1).click(x,y)
#     w.exists('xxx.png')

def test_minicap():
    from atx.device.android_minicap import AndroidDeviceMinicap

    cv2.namedWindow("preview")
    d = AndroidDeviceMinicap()

    while True:
        try:
            h, w = d._screen.shape[:2]
            img = cv2.resize(d._screen, (w/2, h/2))
            cv2.imshow('preview', img)
            key = cv2.waitKey(1)
            if key == 100: # d for dump
                filename = time.strftime('%Y%m%d%H%M%S.png')
                cv2.imwrite(filename, d._screen)
        except KeyboardInterrupt:
            break
    cv2.destroyWindow('preview')

def test_minitouch():
    from atx.device.android_minicap import SubAdb
    
    adb = SubAdb()
    adb.start_minitouch()
    adb.home()
    for pos in ((100, 200), (1000, 200), ):#(100, 1900), (1000, 1900)):
        adb.touch(*pos)
        time.sleep(1)
    for i in range(10):
        adb.swipe(100, 100, 500, 100)
        time.sleep(1)
        adb.swipe(500, 100, 100, 100)
        time.sleep(1)
    return adb


if __name__ == '__main__':
    # test_screenshot()
    test_minicap()
    # adb = test_minitouch()