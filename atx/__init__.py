#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""This module is to make mobile test more easily
"""

from __future__ import absolute_import
from __future__ import print_function

import os
import sys
import six

import pkg_resources
try:
    version = pkg_resources.get_distribution("atx").version
except pkg_resources.DistributionNotFound:
    version = 'unknown'

from atx.consts import *
from atx.errors import *
from atx.drivers import Pattern, Bounds, ImageCrop
import atx.adbkit.client


# make a global var for easily use
adb_client = atx.adbkit.client.Client()


def _connect_url(*args):
    if len(args) == 0:
        return os.getenv('ATX_CONNECT_URL')
    return args[0]


def _detect_platform(connect_url):
    if os.getenv('ATX_PLATFORM'):
        return os.getenv('ATX_PLATFORM')

    if not connect_url: # None or ""
        return 'android'
    elif connect_url.startswith('http://'): # WDA use http url as connect str
        return 'ios'
    else:
        return 'android'


def connect(*args, **kwargs):
    """Connect to a device, and return its object
    Args:
        platform: string one of <android|ios|windows>
        
    Returns:
        None

    Raises:
        SyntaxError, EnvironmentError
    """
    connect_url = _connect_url(*args)
    platform = kwargs.pop('platform', _detect_platform(connect_url))

    cls = None
    if platform == 'android':
        os.environ['JSONRPC_TIMEOUT'] = "60" # default is 90s which is too long.
        devcls = __import__('atx.drivers.android')
        cls = devcls.drivers.android.AndroidDevice
    elif platform == 'windows':
        devcls = __import__('atx.drivers.windows')
        cls = devcls.drivers.windows.WindowsDevice
    elif platform == 'ios':
        devcls = __import__('atx.drivers.ios_webdriveragent')
        cls = devcls.drivers.ios_webdriveragent.IOSDevice
    elif platform == 'webdriver':
        devcls = __import__('atx.drivers.webdriver')
        cls = devcls.drivers.webdriver.WebDriver
    elif platform == 'dummy': # for py.test use
        devcls = __import__('atx.drivers.dummy')
        cls = devcls.drivers.dummy.DummyDevice
    
    if cls is None:
        raise SyntaxError('Platform: %s not exists' % platform)

    c = cls(connect_url, **kwargs)
    c.platform = platform
    return c



# def _sig_handler(signum, frame):
#     print >>sys.stderr, 'Signal INT catched !!!'
#     sys.exit(1)
# signal.signal(signal.SIGINT, _sig_handler)
