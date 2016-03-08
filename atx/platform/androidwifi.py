#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''
TODO: not finished
basic operation for a game(like a user does)
'''

# import os
import re
import urllib
import requests

# from .. import base
# log = base.getLogger('androidwifi')

class Device(object):
    def __init__(self, addr=None):
        self._addr = addr
        if not self._addr.startswith('http://'):
            self._addr = 'http://'+self._addr

    def _req(self, uri, params):
        ''' Make a GET Request '''
        ret = requests.get(self._addr+'/'+uri, params=params)
        print 'DEUBG(%s, %s): %s' %(uri, params, ret.text)
        return ret

    def snapshot(self, filename):
        ''' save screen snapshot '''
        urllib.urlretrieve(self._addr+'/screen.png', filename)

    def touch(self, x, y, duration=0.1):
        '''
        touch position
        '''
        # self._req('click', dict(x=x, y=y, event=eventType))
        pass

    def drag(self, (x0, y0), (x1, y1), duration=0.5):
        '''
        Drap screen
        '''
        self._req('drag', dict(x0=x0,y0=y0,x1=x1,y1=y1,duration=duration))
        

    def shape(self):
        ''' 
        Get screen width and height 
        '''
        return (0, 0)

    def type(self, text):
        '''
        Input some text

        @param text: string (text want to type)
        '''
        # log.debug('type text: %s', repr(text))
        pass

    def keyevent(self, event):
        '''
        Send keyevent by adb

        @param event: string (one of MENU, HOME, BACK)
        '''
        self.adb.shell('input keyevent '+str(event))

    def meminfo(self, appname):
        '''
        Retrive memory info for app
        @param package(string): android package name
        @return dict: {'VSS', 'RSS', 'PSS'} (unit KB)
        '''
        return dict(VSS=1)

    def cpuinfo(self, appname):
        '''
        @param package(string): android package name
        @return dict: {'total': float, 'average': float}
        '''
        total=100
        return dict(total=total, average=total/self._devinfo['cpu_count'])

    def getdevinfo(self):
        # cpu
        output = self.adb.shell('cat /proc/cpuinfo')
        matches = re.compile('processor').findall(output)
        cpu_count = len(matches)
        # mem
        output = self.adb.shell('cat /proc/meminfo')
        match = re.compile('MemTotal:\s*(\d+)\s*kB\s*MemFree:\s*(\d+)', re.IGNORECASE).match(output)
        if match:
            mem_total = int(match.group(1), 10)>>10 # MB
            mem_free = int(match.group(2), 10)>>10
        else:
            mem_total = -1
            mem_free = -1

        # brand = self.adb.getProperty('ro.product.brand')
        return {
            'cpu_count': cpu_count,
            'mem_total': mem_total,
            'mem_free': mem_free,
            'product_brand': self.adb.getProperty('ro.product.brand'),
            'product_model': self.adb.getProperty('ro.product.model')
            }

if __name__ == '__main__':
    dev = Device('http://10.242.115.60:8765')
    dev.touch(1, 2)
    dev.drag((1,2), (3,4))