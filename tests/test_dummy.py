#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import time

import pytest
import atx
from atx.ext import cloudtest

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
    print 'teardown'
    
def test_screenshot():
    screen = d.screenshot()
    assert screen is not None

def test_hook_screenshot():
    called = [False]

    def hook(event):
        print 'event', event
        called[0] = True

    d.add_listener(hook, atx.EVENT_SCREENSHOT)
    d.screenshot()
    assert called[0] == True

def test_cloudtest_hook():
    cloudtest.record_operation(d)
    d.screenshot()

def test_region_screenshot():
    nd = d.region(atx.Bounds(100, 100, 600, 300))
    rs = nd.region_screenshot()
    assert rs is not None
    assert rs.size == (500, 200)

def test_assert_exists():
    d.assert_exists('media/system-app.png')

    with pytest.raises(atx.AssertExistsError):
        d.assert_exists('media/haima.png', timeout=0.1)
