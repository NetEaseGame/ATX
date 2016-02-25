#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''
basic operation for a game(like a user does)
'''

import logging
logging.getLogger("paramiko").setLevel(logging.WARNING)

import subprocess
from appium import webdriver
from PIL import Image

from .. import base
from .. import patch
 
log = base.getLogger('ios')

class Monitor(object):
    def __init__(self, ip, appname):
        try:
            import paramiko
        except:
            raise RuntimeError("Require python-lib 'paramiko' installed")

        self._ssh = paramiko.client.SSHClient()
        self._ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        self._ssh.connect(ip, username='root', password='alpine')
        self._ip = ip 
        self._name = appname
        def _sh(*args):
            cmd = args[0] if len(args) == 1 else subprocess.list2cmdline(args)
            stdin, out, err = self._ssh.exec_command(cmd)
            return out.read()
        self.sh = _sh

    @patch.run_once
    def ncpu(self):
        ''' number of cpu '''
        out = self.sh('sysctl', 'hw.ncpu')
        return int(out.strip().split()[1])

    @patch.run_once
    def pid(self):
        name = '/['+self._name[0]+']'+self._name[1:]  # change "grep name" -> "grep [n]ame"
        output = self.sh('ps -eo pid,command | grep '+name)
        return int(output.split()[0])

    def cpu(self):
        ''' cpu usage, range must be in [0, 100] '''
        pid = self.pid()
        output = self.sh('ps -o pcpu -p %d | tail -n+2' % pid)
        cpu = output.strip()
        return float(cpu)/self.ncpu()
        

    def memory(self):
        '''
        @description details view: http://my.oschina.net/goskyblue/blog/296798

        @param package(string): android package name
        @return dict: {'VSS', 'RSS'} (unit KB)
        '''
        output = self.sh('ps -o pmem,rss,vsz -p %d | tail -n+2' % self.pid())
        pmem, rss, vss = output.split()
        return dict(VSS=int(vss), RSS=int(rss), PMEM=float(pmem))


class Device(object):
    def __init__(self, addr=None):
        if not addr:
            addr = '127.0.0.1'
        self.url = 'http://%s:4723/wd/hub' % addr
        self.driver = webdriver.Remote(
            command_executor=self.url,
            desired_capabilities={
                'platformName': 'iOS',
                # after appium 1.2.0, deviceName is required
                'deviceName': 'ios device',
                'autoLaunch': False
            }
        )
        self._scale = None
        self.start()
        self._init()

    def _init(self):
        rw, rh = self._getShapeReal()
        w, h = self._getShapeInput()
        w, h = min(w, h), max(w, h)
        print (rw, rh), (w, h)
        self._scale = float(w)/rw
        print 'SCALE:', self._scale

    def start(self):
        self.driver.launch_app()

    def stop(self):
        self.driver.close_app()

    def clear(self):
        self.stop()

    def snapshot(self, filename):
        ''' save screen snapshot '''
        log.debug('start take snapshot')
        self.driver.save_screenshot(filename)
        log.debug('finish take snapshot and save to '+filename)
        return filename

    def _cvtXY(self, x, y):
        '''
        convert x,y from device real resolution to action input resolution
        '''
        x_input = x * self._scale #self.width / self.width_real
        y_input = y * self._scale #self.height / self.height_real
        log.debug("cvt %s,%s to %s,%s" % (x, y, x_input, y_input))
        return map(int, (x_input, y_input))

    def touch(self, x, y, duration=None):
        '''
        touch screen at (x, y)
        multi finger operation not provided yet
        '''
        if duration:
            duration *= 1000
        x, y = self._cvtXY(x, y)
        log.debug('touch position %s', (x, y))
        self.driver.tap([(x, y)], duration)

    def drag(self, (x1, y1), (x2, y2), duration=None):
        '''
        Simulate drag from (x1, y1) to (x2, y2)
        multi finger operation not provided yet
        '''
        x1, y1 = self._cvtXY(x1, y1)
        x2, y2 = self._cvtXY(x2, y2)
        log.debug('drag from (%s, %s) to (%s, %s)' % (x1, y1, x2, y2))
        if duration:
            duration = duration * 1000 # seconds to ms
        self.driver.swipe(x1, y1, x2, y2, duration)

    def _getShapeReal(self):
        '''
        Get screen real resolution
        '''
        screen_shot = self.snapshot("screen_shot.png")
        img = Image.open(screen_shot)
        self.width_real, self.height_real = img.size
        log.debug('IosDevice real resolution: width:{width}, height:{height}'.format(
            width=self.width_real, height=self.height_real))
        return img.size

    def _getShapeInput(self):
        '''
        Get screen shape for x, y Input
        '''
        screen_size = self.driver.get_window_size()
        self.width, self.height = screen_size["width"], screen_size["height"]
        log.debug('IosDevice input resolution: width:{width}, height:{height}'.format(
            width=self.width, height=self.height))
        return (self.width, self.height)

    def shape(self):
        ''' 
        Get screen width and height 
        '''
        return map(int, [p/self._scale for p in self._getShapeInput()])
        #return (self.width_real, self.height_real)

    def type(self, text):
        '''
        Input some text

        @param text: string (text want to type)
        '''
        print "not provided yet on ios"

if __name__ == '__main__':
    d = Device()
    d.snapshot("test.png")
    d.touch(180, 720)
    print d.shape()
    width, height = d.shape()
    d.drag((width * 0.5, height * 0.5), (width * 0.1, height * 0.5))
    
