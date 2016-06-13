#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# extention for http://gt.qq.com/
# reference doc http://gt.qq.com/docs/a/UseGtWithBroadcast.txt
#
# Experimental, maybe change in the future
# Created by <hzsunshx> 2016-06-12

import functools


class GT(object):
    def __init__(self, d):
        self.d = d
        self._broadcast = functools.partial(self.d.adb_device.shell, 'am', 'broadcast', '-a')
        self._package_name = None

    def start_test(self, package_name, cpu=True, net=True, pss=True):
        self._package_name = package_name

        broadcast = self._broadcast
        # 1. start app
        self.quit() # reset gt
        self.d.start_app('com.tencent.wstt.gt')#, 'com.tencent.wstt.gt.activity.GTMainActivity')
        # 2. set test package name
        broadcast('com.tencent.wstt.gt.baseCommand.startTest', '--es', 'pkgName', package_name)
        # 3. set collect params
        if cpu:
            broadcast('com.tencent.wstt.gt.baseCommand.sampleData', '--ei', 'cpu', '1')
        if net:
            broadcast('com.tencent.wstt.gt.baseCommand.sampleData', '--ei', 'net', '1')
        if pss:
            broadcast('com.tencent.wstt.gt.baseCommand.sampleData', '--ei', 'pss', '1')

        # 4. switch back to app
        self.d.start_app(package_name)

    def stop_and_save(self):
        self._broadcast('com.tencent.wstt.gt.baseCommand.endTest', '--es', 'saveFolderName', self._package_name,
            '--es', 'desc', 'Result_of_GT')
        print 'Run\n$ adb pull /sdcard/GT/GW/{pkgname}/{version}/{pkgname}'.format(pkgname=self._package_name, version='unknow')

    def quit(self):
        self._broadcast('com.tencent.wstt.gt.baseCommand.exitGT')
