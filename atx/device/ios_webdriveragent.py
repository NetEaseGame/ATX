#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import

import os
import io

from PIL import Image
import subprocess32 as subprocess

from atx.device.mixin import DeviceMixin, hook_wrap
from atx.device import Display
from atx import consts
from atx import ioskit

__dir__ = os.path.dirname(os.path.abspath(__file__))


class IOSDevice(DeviceMixin, ioskit.Device):
    def __init__(self, udid=None):
        DeviceMixin.__init__(self)
        ioskit.Device.__init__(self, udid)

        # xcodebuild -project  -scheme WebDriverAgentRunner -destination "id=1002c0174e481a651d71e3d9a89bd6f90d253446" test
        # Test Case '-[UITestingUITests testRunner]' started.
        xproj_dir = os.getenv('WEBDRIVERAGENT_DIR')
        if not xproj_dir:
            raise RuntimeError("env-var WEBDRIVERAGENT_DIR need to be set")

        proc = self._xcproc = subprocess.Popen(['/usr/bin/xcodebuild',
            '-project', 'WebDriverAgent.xcodeproj',
            '-scheme', 'WebDriverAgentRunner',
            '-destination', 'id='+self.udid, 'test'],
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, cwd=xproj_dir, bufsize=1, universal_newlines=True)
        for line in iter(proc.stdout.readline, b""):
            print 'STDOUT:', line.strip()
            if 'TEST FAILED' in line:
                raise RuntimeError("webdriver start test failed, maybe need to unlock the keychain, try\n" + 
                    '$ security unlock-keychain ~/Library/Keychains/login.keychain')
            elif "Test Case '-[UITestingUITests testRunner]' started" in line:
                print 'GOOD ^_^'

    @property
    def display(self):
        raise NotImplementedError()

    @property
    def rotation(self):
        raise NotImplementedError()

    def click(self, x, y):
        raise NotImplementedError()