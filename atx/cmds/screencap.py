#!/usr/bin/env python
# coding: utf-8
#
# Usage: python -matx screen [-s 0.8]
from __future__ import absolute_import

import time
from atx import adbkit
# from atx import adb2 as adb


def main(host=None, port=None, serial=None, scale=1.0, out='screenshot.png', method='minicap'):
    """
    If minicap not avaliable then use uiautomator instead

    Disable scale for now.
    Because -s scale is conflict of -s serial
    """
    start = time.time()

    client = adbkit.Client(host=host, port=port)
    device = client.device(serial)
    im = device.screenshot(scale=scale)
    im.save(out)
    print 'Time spend: %.2fs' % (time.time() - start)
    print 'File saved to "%s"' % out
    # return

    # adb.use(serial, host, port)
    # # correct screencap method
    # if not adb.is_file_exists('/data/local/tmp/minicap') and method == 'minicap':
    #     method = 'uiautomator'

    # if method == 'minicap':
    #     try:
    #         adb.screenshot_minicap(filename=out, scale=1.0)
    #         print 'Time spend: %.2fs' % (time.time() - start)
    #         print 'File saved to "%s"' % out
    #         return
    #     except EnvironmentError:
    #         print 'minicap not available, use uiautomator instead.'
    #         method = 'uiautomator'
    
    # if method == 'uiautomator':
    #     print 'Screenshot method use uiautomator'
    #     adb.use_uiautomator()
    #     adb.screenshot(filename=out, scale=1.0)
    #     print 'Time spend: %.2fs' % (time.time() - start)
    #     print 'File saved to "%s"' % out
    #     return

    # print 'method invalid: %s' % method


if __name__ == '__main__':
    main()