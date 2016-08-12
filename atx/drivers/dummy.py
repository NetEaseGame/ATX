# coding: utf-8
#
# dummy device is used for test

from __future__ import absolute_import

import os

from PIL import Image

from atx.drivers.mixin import DeviceMixin, hook_wrap
from atx.drivers import Display
from atx import consts


__dir__ = os.path.dirname(os.path.abspath(__file__))

class DummyDevice(DeviceMixin):
    def __init__(self, *args, **kwargs):
        DeviceMixin.__init__(self)
        self._display = Display(1280, 720)
        self._rotation = 1
        self.last_click = None
        self.serial = '1234'

    @hook_wrap(consts.EVENT_SCREENSHOT)
    def screenshot(self, filename=None):
        """ Take a screenshot """
        # screen size: 1280x720
        screen_path = os.path.join(__dir__, '../../tests/media/dummy_screen.png')
        screen = Image.open(screen_path)
        if filename:
            screen.save(filename)
        return screen

    @property
    def display(self):
        return self._display

    @property
    def rotation(self):
        return self._rotation

    def click(self, x, y):
        self.last_click = (x, y)