#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""This module is to make mobile test more easily
"""

import sys
import signal

import patch
import device
import pkg_resources
try:
    version = pkg_resources.get_distribution("atx").version
except pkg_resources.DistributionNotFound:
    version = 'unknown'

from atx.consts import *
from atx.errors import *
from atx.device import Pattern
from atx import imutils


def connect(*args, **kwargs):
    """Connect to a device, and return its object
    Args:
        platform: string one of <android|ios|windows>

    Returns:
        None

    Raises:
        SyntaxError
    """
    serialno = None
    if len(args) == 1:
        serialno = args[0]
    elif len(args) > 1:
        raise SyntaxError("Too many serial numbers")

    platform = kwargs.pop('platform', 'android')
    devclss = {
        'android': device.AndroidDevice,
    }
    cls = devclss.get(platform)
    if cls is None:
        raise SyntaxError('Platform not exists')
    return cls(serialno, **kwargs)


# def _sig_handler(signum, frame):
#     print >>sys.stderr, 'Signal INT catched !!!'
#     sys.exit(1)
# signal.signal(signal.SIGINT, _sig_handler)


# class Device(object):
#     '''
#     Create a new device instance and use this instance to control device
#     '''
#     def __init__(self, addr, logfile=None):
#         '''
#         @addr: eg: android://<serialno> or ios://127.0.0.1
#         '''
#         from . import devsuit
#         module, loc, p = _parse_addr(addr)
#         if p.path and p.netloc:
#             serialno = p.path.lstrip('/')
#             addr = p.netloc
#         else:
#             serialno = p.netloc
#             addr = ''
#         dev = module.Device(serialno, addr) # FIXME(ssx): may not fit well with ios
#         self._m = devsuit.DeviceSuit(p.scheme, dev, logfile=logfile)

#     def __getattr__(self, key):
#         if hasattr(self._m, key):
#             return getattr(self._m, key)
#         raise AttributeError('Monitor object has no attribute "%s"' % key)


# def getDevices(device='android'):
#     ''' 
#     @return devices list 
#     '''
#     subprocess.call(['adb', 'start-server'])
#     output = subprocess.check_output(['adb', 'devices'])
#     result = []
#     for line in str(output).splitlines()[1:]:
#         ss = line.strip().split()
#         if len(ss) == 2:
#             (devno, state) = ss
#             result.append((devno, state))
#     return result
