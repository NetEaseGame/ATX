#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import time
import mock

import pytest
import atx
from PIL import Image

d = atx.connect(platform='dummy')

def setup_function(f):
    d.resolution = (1280, 720)


def test_setget_resolution():
    assert d.resolution == (720, 1280)

    d.resolution = None # None is also OK to set
    assert d.resolution is None

    d.resolution = (200, 400)
    assert d.resolution == (200, 400)

    with pytest.raises(TypeError):
        d.resolution = [1, 3]
    with pytest.raises(TypeError):
        d.resolution = 720
    assert d.resolution == (200, 400)


def teardown_function(f):
    print('teardown')


def test_screenshot_normal():
    screen = d.screenshot()
    assert screen is not None


def test_screenshot_first_fail():
    d._fail_first_screenshot = True
    screen = d.screenshot()
    assert screen is not None


def test_screenshot_always_fail():
    import types
    d = atx.connect(platform='dummy')

    def raise_ioerror(self):
        raise IOError('error of io')

    d._take_screenshot = types.MethodType(raise_ioerror, d)
    with pytest.raises(IOError):
        d.screenshot()


def test_hook_screenshot():
    called = [False]

    def hook(event):
        print('event', event)
        called[0] = True

    d.add_listener(hook, atx.EVENT_SCREENSHOT)
    d.screenshot()
    assert called[0] == True

#def test_cloudtest_hook():
#    cloudtest.record_operation(d)
#    d.screenshot()

def test_region_screenshot():
    nd = d.region(atx.Bounds(100, 100, 600, 300))
    rs = nd.region_screenshot()
    assert rs is not None
    assert rs.size == (500, 200)

# def test_assert_exists():
#     d.assert_exists('media/system-app.png')

#     with pytest.raises(atx.AssertExistsError):
#         d.assert_exists('media/haima.png', timeout=0.1)

def test_click():
    d.click(50, 70)
    assert d.last_click == (50, 70)

def test_click_image():
    """ require aircv installed """
    d.click_image('media/system-app.png')
    assert d.last_click == (139, 299)

def test_click_image_offset1():
    d.click_image(atx.Pattern('media/system-app.png'))
    assert d.last_click == (139, 299)

def test_click_image_offset2():
    d.click_image(atx.Pattern('media/system-app.png', offset=(0.5, 0.5)))
    w, h = Image.open('media/system-app.png').size
    assert d.last_click == (139+w/2, 299+h/2)
