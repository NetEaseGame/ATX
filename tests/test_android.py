#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import cv2
import time

def main():
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

def test():
    import struct
    import socket
    import subprocess
    import threading
    import Queue
    import traceback
    import numpy as np

    # def watch_orientation():
    #     out = subprocess.check_output('adb shell pm path jp.co.cyberagent.stf.rotationwatcher')
    #     path = out.strip().split(':')[-1]
    #     # path = '/data/app/jp.co.cyberagent.stf.rotationwatcher-1/base.apk'
    #     print 111, path
    #     cmd = 'adb shell CLASSPATH="%s" app_process /system/bin "jp.co.cyberagent.stf.rotationwatcher.RotationWatcher"' % path
    #     p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    #     while True:
    #         line = p.stdout.readline().strip()
    #         if not line:
    #             if p.poll() is None:
    #                 break
    #         print 'orientation is', line
    #     p.kill()
    #     p.stdout.close()

    # t = threading.Thread(target=watch_orientation)
    # t.setDaemon(True)
    # t.start()
    # time.sleep(10000)

    port = 1313
    subprocess.call('adb forward tcp:%s localabstract:minicap' % port)
    cmd = 'adb shell LD_LIBRARY_PATH=/data/local/tmp /data/local/tmp/minicap -P 1080x1920@1080x1920/0 -S'
    p = subprocess.Popen(cmd)

    time.sleep(5)
    queue = Queue.Queue()
    def listen():
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect(('127.0.0.1', port))
        try:
            t = s.recv(24)
            print struct.unpack('<2B5I2B', t)
            while True:
                frame_size = struct.unpack("<I", s.recv(4))[0]
                trunks = []
                recvd_size = 0
                while recvd_size < frame_size:
                    trunk_size = min(8192, frame_size-recvd_size)
                    d = s.recv(trunk_size)
                    trunks.append(d)
                    recvd_size += len(d)
                queue.put(''.join(trunks))
        except:
            traceback.print_exc()
            return
        finally:
            s.close()

    def str2img(jpgstr):
        nparr = np.fromstring(jpgstr, np.uint8)
        return cv2.imdecode(nparr, cv2.IMREAD_COLOR)

    t = threading.Thread(target=listen)
    t.setDaemon(True)
    t.start()

    cv2.namedWindow("preview")
    while True:
        try:
            time.sleep(0.005)
            frame = queue.get_nowait()
        except Queue.Empty:
            if p.poll() is not None:
                break
            continue
        except:
            break
        else:
            img = str2img(frame)
            h, w = img.shape[:2]
            img = cv2.resize(img, (w/2,h/2))
            cv2.imshow('preview', img)
            key = cv2.waitKey(1)

    subprocess.call('adb forward --remove tcp:%s' % port)
    p.kill()
    cv2.destroyAllWindows()


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
            w, h = d._screen.shape[:2]
            img = cv2.resize(d._screen, (h/2, w/2))
            cv2.imshow('preview', img)
            key = cv2.waitKey(1)
            if key == 100: # d for dump
                filename = time.strftime('%Y%m%d%H%M%S.png')
                cv2.imwrite(filename, d._screen)
        except KeyboardInterrupt:
            break
    cv2.destroyWindow('preview')

if __name__ == '__main__':
    # main()
    # test()
    test_minicap()