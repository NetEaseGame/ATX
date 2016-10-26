#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import

import base64
import json
import os
import time
import urlparse
from collections import namedtuple

import requests
from PIL import Image
from StringIO import StringIO

from atx.drivers.mixin import DeviceMixin, hook_wrap
from atx.drivers import Display
from atx import consts


DEBUG = False

def convert(dictionary):
    """
    Convert dict to namedtuple
    """
    return namedtuple('GenericDict', dictionary.keys())(**dictionary)


def urljoin(*urls):
    """
    The default urlparse.urljoin behavior look strange
    Standard urlparse.urljoin('http://a.com/foo', '/bar')
    Expect: http://a.com/foo/bar
    Actually: http://a.com/bar

    This function fix that.
    """
    return reduce(urlparse.urljoin, [u.strip('/')+'/' for u in urls if u.strip('/')], '').rstrip('/')


class WebDriverError(Exception):
    def __init__(self, status, value):
        self.status = status
        self.value = value

    def __str__(self):
        return 'WebDriverError(status=%d, value=%s)' % (self.status, self.value)


def httpdo(method, url, data=None):
    """
    Do HTTP Request
    """
    if isinstance(data, dict):
        data = json.dumps(data)
    if DEBUG:
        print "Shell: curl -X {method} -d '{data}' '{url}'".format(method=method, data=data or '', url=url)

    fn = dict(GET=requests.get, POST=requests.post, DELETE=requests.delete)[method]
    response = fn(url, data=data)
    retjson = response.json()
    if DEBUG:
        print 'Return:', json.dumps(retjson, indent=4)
    r = convert(retjson)
    if r.status != 0:
        raise WebDriverError(r.status, r.value)
    return r


class _Client(object):
    def __init__(self, device_url):
        self.__device_url = device_url

    def screenshot(self):
        """Take screenshot
        Return:
            PIL.Image
        """
        url = urljoin(self.__device_url, "screenshot")
        r = httpdo('GET', url)
        raw_image = base64.b64decode(r.value)
        return Image.open(StringIO(raw_image))


class WebDriver(DeviceMixin):
    def __init__(self, device_url):
        DeviceMixin.__init__(self)
        self.__display = None
        self._ymc = _Client(device_url)

    @hook_wrap(consts.EVENT_SCREENSHOT)
    def screenshot(self, filename=None):
        """ Take a screenshot """
        # screen size: 1280x720
        screen = self._ymc.screenshot()
        if filename:
            screen.save(filename)
        return screen

    def start_app(self, bundle_id):
        pass

    def click(self, x, y):
        pass
