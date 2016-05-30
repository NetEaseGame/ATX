#!/usr/bin/env python
# coding: utf-8
#
# Usage: python -matx screen [-s 0.8]

from atx import adb2 as adb

capture_methods = ('minicap', 'uiautomator')

def main(host=None, port=None, serial=None, out='screenshot.png', method='minicap'):
    """
    If minicap not avaliable then use uiautomator instead

    Disable scale for now.
    Because -s scale is conflict of -s serial
    """
    adb.use(serial, host, port)
    # correct screencap method
    if not adb.is_file_exists('/data/local/tmp/minicap') and method == 'minicap':
        method = 'uiautomator'

    if method == 'minicap':
        try:
            adb.screenshot_minicap(filename=out, scale=1.0)
            print 'File saved to "%s"' % out
            return
        except EnvironmentError:
            print 'minicap not available, use uiautomator instead.'
            method = 'uiautomator'
    
    if method == 'uiautomator':
        print 'Screenshot method use uiautomator'
        adb.use_uiautomator()
        adb.screenshot(filename=out, scale=1.0)
        print 'File saved to "%s"' % out
        return

    print 'method invalid: %s' % method


if __name__ == '__main__':
    main()