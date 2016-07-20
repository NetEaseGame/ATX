#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import

import os
import time

import wda
import subprocess32 as subprocess
from PIL import Image
from StringIO import StringIO

from atx.device.mixin import DeviceMixin, hook_wrap
from atx.device import Display
from atx import consts
from atx import ioskit

__dir__ = os.path.dirname(os.path.abspath(__file__))


class IOSDevice(DeviceMixin):
    def __init__(self, device_url): #udid=None):
        DeviceMixin.__init__(self)
        self.__device_url = device_url
        self.__display = None
        self.__scale = None
        
        self._wda = wda.Client(device_url)
        self._session = None
        # ioskit.Device.__init__(self, udid)

        # # xcodebuild -project  -scheme WebDriverAgentRunner -destination "id=1002c0174e481a651d71e3d9a89bd6f90d253446" test
        # # Test Case '-[UITestingUITests testRunner]' started.
        # xproj_dir = os.getenv('WEBDRIVERAGENT_DIR')
        # if not xproj_dir:
        #     raise RuntimeError("env-var WEBDRIVERAGENT_DIR need to be set")

        # proc = self._xcproc = subprocess.Popen(['/usr/bin/xcodebuild',
        #     '-project', 'WebDriverAgent.xcodeproj',
        #     '-scheme', 'WebDriverAgentRunner',
        #     '-destination', 'id='+self.udid, 'test'],
        #     stdout=subprocess.PIPE, stderr=subprocess.STDOUT, cwd=xproj_dir, bufsize=1, universal_newlines=True)
        # for line in iter(proc.stdout.readline, b""):
        #     print 'STDOUT:', line.strip()
        #     if 'TEST FAILED' in line:
        #         raise RuntimeError("webdriver start test failed, maybe need to unlock the keychain, try\n" + 
        #             '$ security unlock-keychain ~/Library/Keychains/login.keychain')
        #     elif "Successfully wrote Manifest cache" in line:
        #         print 'GOOD ^_^, wait 5s'
        #         time.sleep(5.0)
        #         break

    # def __del__(self):
    #     if self._xcproc:
    #         print 'Terminate xcodebuild'
    #         self._xcproc.terminate()

    def start_app(self, bundle_id):
        """Start an application
        Args:
            - bundle_id: (string) apk bundle ID

        Returns:
            WDA session object
        """
        # if self._session is not None:
        #     self.stop_app()
        self._session = self._wda.session(bundle_id)
        return self._session

    def stop_app(self):
        if self._session is None:
            return
        self._session.close()
        self._session = None

    def status(self):
        """ Check if connection is ok """
        return self._wda.status()

    @property
    def display(self):
        """ Get screen width and height """
        if not self.__display:
            self.screenshot()
        return self.__display

    @property
    def rotation(self):
        raise NotImplementedError()
        return self._wda.rotation

    def click(self, x, y):
        """Simulate click operation
        Args:
            x, y(int): position
        """
        if self._session is None:
            raise RuntimeError("Need to call start_app before")
        if not self.__scale:
            raw_size = self._session.window_size()
            self.__scale = self.display.width / int(round(min(raw_size['width'], raw_size['height'])))
        rx, ry = x/self.__scale, y/self.__scale
        self._session.tap(rx, ry)

    def screenshot(self, filename=None):
        """Take a screenshot
        Args:
            - filename(string): file name to save

        Returns:
            PIL Image object
        """
        raw_png = self._wda.screenshot()
        img = Image.open(StringIO(raw_png))
        if filename:
            img.save(filename)
        if not self.__display:
            self.__display = Display(*sorted(img.size))
        return img
