#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''
This is only for test airtest itself
'''

import os
import shutil
import airtest

from airtest import base
# from com.dtmilano.android.viewclient import ViewClient 
# from com.dtmilano.android.viewclient import adbclient

DEBUG = os.getenv("DEBUG")=="true"
log = base.getLogger('dummy')


class Device(object):
    def __init__(self, phoneno=None):
        self._snapshot = './default.png'
        self._text = ''
        self._click = None
        self._getCpu = False
        pass

    def snapshot(self, filename):
        ''' save screen snapshot '''
        log.debug('DUMMY take snapshot %s' %(filename))
        shutil.copyfile(self._snapshot, filename)

    def touch(self, x, y, duration=0.1):
        '''
        same as adb -s ${SERIALNO} shell input tap x y
        '''
        log.debug('touch position %s', (x, y))
        self._click = (x, y)

    def drag(self, (x0, y0), (x1, y1), duration=0.5):
        '''
        Drap screen
        '''
        log.debug('drap position %s -> %s', (x0, y0), (x1, y1))

    def shape(self):
        ''' 
        Get screen width and height 
        '''
        return 10, 20

    def type(self, text):
        '''
        Input some text

        @param text: string (text want to type)
        '''
        log.debug('type text: %s', repr(text))
        self._text = text

    def keyevent(self, event):
        '''
        Send keyevent by adb

        @param event: string (one of MENU, HOME, BACK)
        '''
        log.debug('keyevent: %s', event)

    def getMem(self, appname):
        return {}

    def getCpu(self, appname):
        self._getCpu = True
        return 0.0

    def start(self, dictSet):
        '''
        Start a program

        @param dictSet: dict (defined in air.json)
        '''
        log.debug('start %s', dictSet)

    def stop(self, dictSet):
        log.debug('stop %s', dictSet)

    def getdevinfo(self):
        return {
            'cpu_count': 1,
            'mem_total': 2,
            'mem_free': 111,
            'product_brand': 'dummy-brand',
            'product_model': 'dummy-model',
            }
