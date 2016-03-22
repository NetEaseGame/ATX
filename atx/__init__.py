#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""This module is to make mobile test more easily
"""

from __future__ import absolute_import

import sys
import signal

import pkg_resources
try:
    version = pkg_resources.get_distribution("atx").version
except pkg_resources.DistributionNotFound:
    version = 'unknown'

from atx.consts import *
from atx.errors import *
from atx.device import Pattern, Bounds


def connect(*args, **kwargs):
    """Connect to a device, and return its object
    Args:
        platform: string one of <android|ios|windows>

    Returns:
        None

    Raises:
        SyntaxError, EnvironmentError
    """
    platform = kwargs.pop('platform', 'android')

    cls = None
    if platform == 'android':
        devcls = __import__('atx.android_device')
        cls = devcls.android_device.AndroidDevice
    
    if cls is None:
        raise SyntaxError('Platform: %s not exists' % platform)
    return cls(*args, **kwargs)


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
