#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# License under MIT


from __future__ import absolute_import

import os

import subprocess32 as subprocess
from PIL import Image

from atx import consts
from atx import errors
from atx import patch
from atx import base
from atx import imutils
from atx import strutils
from atx.device import Bounds
from atx import logutils
from atx.device.mixin import DeviceMixin, hook_wrap
from atx import ioskit


__dir__ = os.path.dirname(os.path.abspath(__file__))
log = logutils.getLogger(__name__)

class IOSDevice(DeviceMixin):
    def __init__(self, bundle_id=None, udid=None):
        self._proc = None

        self.screen_rotation = 0
        self.d = ioskit.Device(udid)
        # self.bundle_id = bundle_id
        if not bundle_id:
            print 'WARNING [ios.py]: bundle_id is not set, only limited functions can be used.'

    def _init_instruments(self, bundle_id):
        self._bundle_id = bundle_id
        self._proc = subprocess.Popen(['sleep', '500'])

    def _close(self):
        print 'Terminate sleep'
        if self._proc:
            self._proc.terminate()

    def __del__(self):
        self._close()

    def screenshot(self, filename=None):
        '''
        Take ios screenshot
        Args:
            - filename(string): optional
        Returns:
            PIL.Image object
        '''
        image = self.d.screenshot()
        if self.screen_rotation:
            method = getattr(Image, 'ROTATE_{}'.format(self.screen_rotation*90))
            image = image.transpose(method)
        if filename:
            image.save(filename)
        return image

    def click(self, x, y):
        raise NotImplementedError()

    def install(self, filepath):
        raise NotImplementedError()
