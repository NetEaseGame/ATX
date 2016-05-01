#!/usr/bin/env python
# -*- coding: utf-8 -*-

import subprocess32 as subprocess


class IOS(object):
    @classmethod
    def cmd(cls, *args):
        return subprocess.Popen(list(args), stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    @classmethod
    def devices(cls):
        p = cls.cmd('idevice_id', '-l')
        return p.communicate()[0].strip().split()


if __name__ == '__main__':
    print IOS.devices()
