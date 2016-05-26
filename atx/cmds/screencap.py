#!/usr/bin/env python
# coding: utf-8
#
# Usage: python -matx screen [-s 0.8]

from atx import adb2 as adb

capture_methods = ('minicap', 'uiautomator')

def main(host=None, port=None, serial=None, scale=1.0, out='screenshot.png', method='minicap'):
    '''interact'''
    adb.use(serial, host, port)
    if method == 'minicap':
        try:
            adb.screenshot_minicap(filename=out, scale=scale)
            return
        except EnvironmentError:
            print 'minicap not available, use `adb screencap` instead.'
    elif method == 'uiautomator':
        print 'starting uiautomator server, may take a long time..'
        adb.use_uiautomator()
    adb.screenshot(filename=out, scale=scale)

if __name__ == '__main__':
    main()