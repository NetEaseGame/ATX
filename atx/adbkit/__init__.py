#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Blueprint, not finished yet.

>>> dev.packages()
[{'name': 'com.example.demo', 'version': 2}]
>>> dev.forward_list()
[{'local': 'tcp:8001', 'remote': 'tcp:8000'}]
>>> dev.properties()
{'ro.build.brand', 'MI2', ...}
>>> dev.install('demo.apk')
True
>>> dev.uninstall('com.example.demo', keep_data=True) # DONE
True
>>> dev.logcat() # TODO
>>> dev.pull('/data/local/tmp/_screen.png', './')
True
>>> dev.push('./demo.apk', '/data/local/tmp/demo.apk')
True
>>> dev.listdir('/data/local/tmp')
['_screen.png']
>>> dev.shell('ls', '-l', '/data/local/tmp/')
:output as string, replace \r\n to '\n'
>>> dev.start_activity('com.example.demo', '.Client')
None
>>> dev.stat('/data/local/tmp/_screen.png')
:posix.stat_result object
>>> dev.current_app()
com.example.demo
>>> dev.orientation()
: one of [1-4]
>>> dev.screenshot() # DONE
: PIL image object
>>> dev.keyevent('HOME')
None
>>> dev.open_minicap()
True
>>> dev.open_minitouch()
True
>>> dev.touch(100, 100)
None
>>> dev.swipe() # TODO
>>> dev.pinch() # only in minitouch
"""

from __future__ import absolute_import

from atx.adbkit.client import Client


if __name__ == '__main__':
    adb = Client()
    print(adb.devices())
    print(adb.version())
    dev = adb.device() #'10.250.210.165:57089')
    # print dev.keyevent('HOME')
    print(dev.display)
    # for pkg in dev.packages():
    #     print pkg
    # dev.screenshot('s.png', scale=1.0)
    print(dev.is_locked())
    print(dev.wake())
    dev.click(568, 1488)
    print(dev.current_app())
