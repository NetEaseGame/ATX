#!/usr/bin/env python
# -*- coding: utf-8 -*-

#coding: utf-8

import os
import time

import pytest
import atx


d = atx.connect(platform='dummy')

def setup_function(f):
    d.resolution = (720, 1280)

def teardown_function(f):
    print 'teardown'
    
def test_screenshot():
    screen = d.screenshot()
    assert screen is not None

def test_region_screenshot():
    nd = d.region(atx.Bounds(100, 100, 600, 300))
    rs = nd.region_screenshot()
    assert rs is not None
    assert rs.size == (500, 200)

def test_assert_exists():
    d.assert_exists('media/system-app.png')

    with pytest.raises(atx.AssertExistsError):
        d.assert_exists('media/haima.png', timeout=0.1)