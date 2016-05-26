#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import


class Device(object):
    def __init__(self, client, serial):
        self._client = client
        self._serial = serial

    def raw_cmd(self, *args):
        args = ['-s', self._serial] + list(args)
        return self._client.raw_cmd(*args)

    def run_cmd(self, *args):
        p = self.raw_cmd(*args)
        return p.communicate()[0]

    def keyevent(self, key):
        ''' Call: adb shell input keyevent $key '''
        self.run_cmd('shell', 'input', 'keyevent', key)
