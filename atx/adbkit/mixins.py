# -*- coding: utf-8 -*-
# minin classes. 
# use extra resource to enhance original adb device.
# interface class should have raw_cmd method with a signature 
# as follows:
#
#   def raw_cmd(self, *args, **kwargs):
#       ...
#       return subprocess.Popen(...)
#
# where `args` is adb command arguments and kwargs are 
# subprocess keyword arguments.

import os
import Queue
import re
import socket
import struct
import subprocess
import threading
import time
import traceback

__dir__ = os.path.dirname(os.path.abspath(__file__))

class RotationWatcherMixin(object):

    __rotation = 0
    __watcher_process = None

    def open_rotation_watcher(self, on_rotation_change=None):
        package_name = 'jp.co.cyberagent.stf.rotationwatcher'
        out = self.raw_cmd('shell', 'pm', 'list', 'packages', stdout=subprocess.PIPE).communicate()[0]
        if package_name not in out:
            apkpath = os.path.join(__dir__, '..', 'vendor', 'RotationWatcher.apk')
            print 'install rotationwatcher...', apkpath
            if 0 != self.raw_cmd('install', '-r', '-t', apkpath).wait():
                print 'install rotationwatcher failed.'
                return

        if self.__watcher_process is not None:
            self.__watcher_process.kill()

        out = self.raw_cmd('shell', 'pm', 'path', package_name, stdout=subprocess.PIPE).communicate()[0]
        path = out.strip().split(':')[-1]
        p = self.raw_cmd('shell', 
            'CLASSPATH="%s"' % path, 
            'app_process',
            '/system/bin',
            'jp.co.cyberagent.stf.rotationwatcher.RotationWatcher', 
            stdout=subprocess.PIPE)
        self.__watcher_process = p

        queue = Queue.Queue()

        def _pull():
            while True:
                line = p.stdout.readline().strip()
                if not line:
                    if p.poll() is not None:
                        print 'rotationwatcher stopped'
                        break
                    continue
                queue.put(line)

        t = threading.Thread(target=_pull)
        t.setDaemon(True)
        t.start()

        def listener(value):
            try:
                self.__rotation = int(value)/90
            except:
                return
            if callable(on_rotation_change):
                on_rotation_change(self.__rotation)

        def _listen():
            while True:
                try:
                    time.sleep(0.005)
                    line = queue.get_nowait()
                    listener(line)
                except Queue.Empty:
                    if p.poll() is not None:
                        break
                    continue
                except:
                    traceback.print_exc()

        t = threading.Thread(target=_listen)
        t.setDaemon(True)
        t.start()

def str2img(jpgstr, orientation=None):
    import numpy as np
    import cv2
    arr = np.fromstring(jpgstr, np.uint8)
    img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    if orientation == 1:
        return cv2.flip(cv2.transpose(img), 0) # counter-clockwise
    if orientation == 3:
        return cv2.flip(cv2.transpose(img), 1) # clockwise
    return img

class MinicapStreamMixin(object):
    __screen = None
    __minicap_process = None

    def __install_minicap(self):
        # install minicap & minitouch
        os.system('python -m atx minicap')

    def open_minicap_stream(self, port=1313):
        # ensure minicap installed
        out = self.raw_cmd('shell', 'ls', '"/data/local/tmp/minicap"', stdout=subprocess.PIPE).communicate()[0]
        if 'No such file or directory' in out:
            self.__install_minicap()

        if self.__minicap_process is not None:
            self.__minicap_process.kill()

        # if minicap is already started, kill it first.
        out = self.raw_cmd('shell', 'ps', '-C', '/data/local/tmp/minicap', stdout=subprocess.PIPE).communicate()[0]
        out = out.strip().split('\n')
        if len(out) > 1:
            idx = out[0].split().index('PID')
            pid = out[1].split()[idx]
            print 'minicap is running, killing', pid
            self.raw_cmd('shell', 'kill', '-9', pid).wait()

        # start minicap
        out = self.raw_cmd('shell', 'LD_LIBRARY_PATH=/data/local/tmp', '/data/local/tmp/minicap', '-i', 
                    stdout=subprocess.PIPE).communicate()[0]
        m = re.search('"width": (\d+).*"height": (\d+).*"rotation": (\d+)', out, re.S)
        w, h, r = map(int, m.groups())
        w, h = min(w, h), max(w, h)
        params = '{x}x{y}@{x}x{y}/{r}'.format(x=w, y=h, r=r)
        print 'starting minicap', params

        p = self.raw_cmd('shell', 
                    'LD_LIBRARY_PATH=/data/local/tmp', 
                    '/data/local/tmp/minicap', 
                    '-P %s' % params,
                    '-S',
                    stdout=subprocess.PIPE)
        self.__minicap_process = p
        time.sleep(0.5)
        # forward to tcp port 
        self.raw_cmd('forward', 'tcp:%s' % port, 'localabstract:minicap').wait()

        queue = Queue.Queue()

        # pull data from socket
        def _pull():
            # print 'start pull', p.pid, p.poll()
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            try:
                assert p.poll() is None
                s.connect(('127.0.0.1', port))
                t = s.recv(24)
                print 'minicap connected', struct.unpack('<2B5I2B', t)
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
            except Exception as e:
                if not isinstance(e, struct.error):
                    traceback.print_exc()
                if p.poll() is not None:
                    print 'Process died.'
                    print p.stdout.read()
                else:
                    print 'stoping minicap ...'
                    p.kill()
            finally:
                s.close()
                self.raw_cmd('forward', '--remove', 'tcp:%s' % port).wait()

        t = threading.Thread(target=_pull)
        t.setDaemon(True)
        t.start()

        out = self.raw_cmd('shell', 'getprop', 'ro.build.version.sdk', stdout=subprocess.PIPE).communicate()[0]
        sdk = int(out.strip())
        orientation = r/90

        def _listen():
            while True:
                try:
                    time.sleep(0.005)
                    frame = queue.get_nowait()
                    if sdk <= 16:
                        img = str2img(frame, orientation)
                    else:
                        img = str2img(frame)
                    self.__screen = img
                except Queue.Empty:
                    if p.poll() is not None:
                        print 'minicap died'
                        print p.stdout.read()
                        break
                    continue
                except:
                    traceback.print_exc()

        t = threading.Thread(target=_listen)
        t.setDaemon(True)
        t.start()

    def screenshot_cv2(self):
        return self.__screen

class MinitouchStreamMixin(object):
    __touch_queue = None
    __minitouch_process = None

    def __install_minitouch(self):
        # install minicap & minitouch
        os.system('python -m atx minicap')

    def open_minitouch_stream(self, port=1111):
        if self.__touch_queue is None:
            self.__touch_queue = Queue.Queue()

        # ensure minicap installed
        out = self.raw_cmd('shell', 'ls', '"/data/local/tmp/minitouch"', stdout=subprocess.PIPE).communicate()[0]
        if 'No such file or directory' in out:
            self.__install_minitouch()

        if self.__minitouch_process is not None:
            self.__minitouch_process.kill()

        out = self.raw_cmd('shell', 'ps', '-C', '/data/local/tmp/minitouch', stdout=subprocess.PIPE).communicate()[0]
        out = out.strip().split('\n')
        if len(out) > 1:
            p = None
        else:
            p = self.raw_cmd('shell', '/data/local/tmp/minitouch')
            time.sleep(1)
            if p.poll() is not None:
                print 'start minitouch failed.'
                return
        self.__minitouch_process = p                
        self.raw_cmd('forward', 'tcp:%s' % port, 'localabstract:minitouch').wait()

        def send():
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            try:
                s.connect(('127.0.0.1', port))
                while True:
                    cmd = self.__touch_queue.get() # wait here
                    if not cmd:
                        continue
                    elif cmd[-1] != '\n':
                        cmd += '\n'
                    s.send(cmd)    
            except:
                traceback.print_exc()
            finally:
                s.close()
                self.raw_cmd('forward', '--remove', 'tcp:%s' % port).wait()

        t = threading.Thread(target=send)
        t.setDaemon(True)
        t.start()

    def click(self, x, y):
        cmd = 'd 0 %d %d 30\nc\nu 0\nc\n' % (int(x), int(y))
        self.__touch_queue.put(cmd)

    def swipe(self, sx, sy, ex, ey, steps=20):
        x1, y1, x2, y2 = map(int, (x1, y1, x2, y2))
        dx = (x2-x1)/steps
        dy = (y2-y1)/steps
        send = self.touchqueue.put
        send('d 0 %d %d 30\nc\n' % (x1, y1))
        for i in range(steps-1):
            x, y = x1+(i+1)*dx, y1+(i+1)*dy
            send('m 0 %d %d 30\nc\n' % (x, y))
        send('u 0 %d %d 30\nc\nu 0\nc\n' % (x2, y2))

    def pinchin(self, x1, y1, x2, y2, steps=10):
        pass

    def pinchout(self, x1, y1, x2, y2, steps=10):
        pass

class OpenSTFServiceMixin(object):
    pass


#-------------- examples ----------------#

class DummyDevice(object):
    def raw_cmd(self, *args, **kwargs):
        cmds = ['adb'] + list(args)
        print cmds
        return subprocess.Popen(cmds, **kwargs)

# Mixins should come in front to override functions in Base
class TestDevice(MinitouchStreamMixin, MinicapStreamMixin, RotationWatcherMixin, DummyDevice):
    def __init__(self, *args, **kwargs):
        super(self.__class__, self).__init__(*args, **kwargs)
        self.open_rotation_watcher(on_rotation_change=lambda v: self.open_minicap_stream())
        self.open_minitouch_stream()

if __name__ == '__main__':
    import cv2
    dev = TestDevice()
    while True:
        img = dev.screenshot_cv2()
        if img is not None:
            cv2.imshow('screen', img)
        cv2.waitKey(10)

