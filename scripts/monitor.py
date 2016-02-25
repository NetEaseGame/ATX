#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''
nija test example
'''

import sys
import os
import airtest
import time

serialno = os.getenv('AIRTEST_PHONENO') or '10.242.62.143:5555'
appname  = os.getenv('AIRTEST_APPNAME') or 'com.netease.rz'
device = os.getenv('DEVICE') or 'android'

app = airtest.connect(serialno, appname=appname, device=device)

try:
    while True:
        app.sleep(10)
        app.takeSnapshot('%d.png' % int(time.time()))
except KeyboardInterrupt:
    print 'Exit'

