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
    elif platform == 'windows':
        devcls = __import__('atx.windows_device')
        cls = devcls.windows_device.WindowsDevice
    
    if cls is None:
        raise SyntaxError('Platform: %s not exists' % platform)
    return cls(*args, **kwargs)


# def _sig_handler(signum, frame):
#     print >>sys.stderr, 'Signal INT catched !!!'
#     sys.exit(1)
# signal.signal(signal.SIGINT, _sig_handler)
