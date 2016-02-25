#!/usr/bin/env python
# -*- coding: utf-8 -*-

#coding: utf-8

import sys
reload(sys)
sys.setdefaultencoding('utf8')

import airtest
import os
import cv2
import time

app = airtest.connect('shit', device='dummy')
screenFile = 'testdata/dummy/default.png'
app.globalSet(image_dirs=['testdata/dummy', '.'])
app.globalSet(image_match_method='template')
app.globalSet(threshold=0.8)

ICON = 'testdata/dummy/add.png'

def setup_function(f):
    app.dev._snapshot = screenFile
    app.dev._text = ''
    app.dev._click = None

def test_locate_image():
    # ap = airtest.connect('test-connect', appname='hello', device='dummy', monitor=False, logfile='log/1')
    app.dev._snapshot = 'testdata/dummy/h15_bg.png'
    print 'get method=', app.globalGet('image_match_method')
    print app.click('back.png')

def test_connect_monitor():
    ap = airtest.connect('test-connect', appname='hello', device='dummy', monitor=False, logfile='log/1')
    ap.dev._getCpu = False
    time.sleep(2.0)
    assert ap.dev._getCpu == False
    ap.globalSet(enable_monitor=False)

    ap = airtest.connect('test-connect', appname='hello', device='dummy', monitor=True, logfile='log/2')
    ap.dev._getCpu = False
    time.sleep(2.0)
    assert ap.dev._getCpu == True
    ap.globalSet(enable_monitor=False)

    ap = airtest.connect('test-connect', appname='hello', device='dummy', logfile='log/3')
    ap.dev._getCpu = False
    time.sleep(2.0)
    assert ap.dev._getCpu == True
    ap.globalSet(enable_monitor=False)
    
def test_snapshot():
    app.takeSnapshot('tmp/nice.png')
    assert os.path.exists('tmp/nice.png')
    os.unlink('tmp/nice.png')

def test_find():
    pos = app.find('aboy')
    assert pos == None

def test_type():
    app.type('hello')
    assert app.dev._text == 'hello'

def test_shape():
    x, y = app.shape()
    assert isinstance(x, int)
    assert isinstance(y, int)

def test_click():
    app.click(u'赵云')
    x, y = app.dev._click
    assert 200 < x < 250
    assert 400 < y < 450

    app.click(u'赵云.png')
    x, y = app.dev._click
    assert 200 < x < 250
    assert 400 < y < 450

    app.click((10, 10))
    assert app.dev._click == (10, 10)

    app.click((0.4, 0.5))
    w, h = app.shape()
    assert app.dev._click == (int(0.4*w), int(0.5*h))


def other():
    scr = cv2.imread(screenFile, 0)
    icon = cv2.imread(iconFile, 0)

    res = cv2.matchTemplate(icon, scr, cv2.TM_CCOEFF)
    minVal, maxVal, minLoc, maxLoc = cv2.minMaxLoc(res)
    topLeft = maxLoc
    print topLeft
