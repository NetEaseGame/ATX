#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# License under MIT


from __future__ import absolute_import

import os
import json
import time

import yaml
import subprocess32 as subprocess
from PIL import Image

from atx import consts
from atx import errors
from atx import patch
from atx import base
from atx import imutils
from atx import strutils
from atx import logutils
from atx import ioskit
from atx.drivers import Bounds, Display
from atx.drivers.mixin import DeviceMixin, hook_wrap


__dir__ = os.path.dirname(os.path.abspath(__file__))
log = logutils.getLogger(__name__)

class IOSDevice(DeviceMixin):
    def __init__(self, bundle_id=None, udid=None):
        DeviceMixin.__init__(self)

        self.d = ioskit.Device(udid)
        self.udid = self.d.udid

        self._proc = None
        self._display = None #Display(2208, 1242)
        self._scale = 1
        self._env = os.environ.copy()
        self._init_display()

        self.screen_rotation = 1 # TODO: auto judge

        if not bundle_id:
            print 'WARNING [ios.py]: bundle_id is not set' #, use "com.netease.atx.apple" instead.'
            # self._init_instruments('com.netease.atx.apple')
        else:
            self._init_instruments(bundle_id)

    def _init_display(self):
        model = self.d.info['HardwareModel']
        with open(os.path.join(__dir__, 'ios-models.yml'), 'rb') as f:
            items = yaml.load(f.read())
        for item in items:
            if model == item.get('model'):
                (width, height) = map(int, item.get('pixel').split('x'))
                self._scale = item.get('scale')
                self._display = Display(width*self._scale, height*self._scale)
                break
        if self._display is None:
            raise RuntimeError("TODO: not support your phone for now, You need contact the author.")
    
    def _init_instruments(self, bundle_id):
        self._bootstrap = os.path.join(__dir__, 'bootstrap.sh')
        self._bundle_id = bundle_id
        self._env.update({'UDID': self.udid, 'BUNDLE_ID': self._bundle_id})
        # 1. remove pipe
        # subprocess.check_output([self._bootstrap, 'reset'], env=self._env)
        # 2. start instruments
        self._proc = subprocess.Popen([self._bootstrap, 'instruments'], env=self._env, stdout=subprocess.PIPE)
        self.sleep(5.0)
        self._wait_instruments()

    def _wait_instruments(self):
        ret = self._run('1')
        if ret != 1:
            log.error('Instruments stdout:\n' + self._proc.stdout.read())
            raise RuntimeError('Instruments start failed, expect 1 but got %s' % (ret,))

    def _run(self, code):
        # print self._proc.poll()
        # print code
        encoded_code = json.dumps({'command': code})
        output = subprocess.check_output([self._bootstrap, 'run', encoded_code], env=self._env)
        # print output
        try:
            return json.loads(output)
        except:
            print 'unknown json output:', output
            return output

    def _run_nowait(self, code):
        ''' TODO: change to no wait '''
        print self._proc.poll()
        encoded_code = json.dumps({'command': code, 'nowait': True})
        output = subprocess.check_output([self._bootstrap, 'run', '--nowait', encoded_code], env=self._env)
        return output

    def _close(self):
        print 'Terminate instruments'
        if self._proc:
            self._proc.terminate()
        # 1. remove pipe
        subprocess.check_output([self._bootstrap, 'reset'], env=self._env)

    def __del__(self):
        if hasattr(self, '_bootstrap'):
            self._close()

    @property
    def rotation(self):
        return self.screen_rotation
    
    @property
    def display(self):
        return self._display

    @property
    def info(self):
        return self.d.info

    def screenshot(self, filename=None):
        '''
        Take ios screenshot
        Args:
            - filename(string): optional
        Returns:
            PIL.Image object
        '''
        image = self.d.screenshot()
        if self.rotation:
            method = getattr(Image, 'ROTATE_{}'.format(self.rotation*90))
            image = image.transpose(method)
        if filename:
            image.save(filename)
        return image

    def click(self, x, y):
        '''
        Simulate click operation
        Args:
            - x (int): position of x
            - y (int): position of y
        Returns:
            self
        '''
        self._run_nowait('target.tap({x: %d, y: %d})' % (x/self._scale, y/self._scale))
        return self

    def install(self, filepath):
        self.d.install(filepath)

    def sleep(self, sec):
        self.delay(sec)

    def type(self, text):
        self._run_nowait('$.typeString(%s)' % json.dumps(text))

    def start_app(self, bundle_id):
        self.d.start_app(bundle_id)

    def current_app(self):
        ''' todo, maybe return dict is a better way '''
        return self._run('target.frontMostApp().bundleID()').strip().strip('"')
