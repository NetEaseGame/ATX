#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import

import atexit
import os
import re
import json
import collections
import tempfile
from StringIO import StringIO

from PIL import Image
from atx import logutils


logger = logutils.getLogger(__name__)
_DISPLAY_RE = re.compile(
    r'.*DisplayViewport{valid=true, .*orientation=(?P<orientation>\d+), .*deviceWidth=(?P<width>\d+), deviceHeight=(?P<height>\d+).*')
_PROP_PATTERN = re.compile(r'\[(?P<key>.*?)\]:\s*\[(?P<value>.*)\]')

class Device(object):
    Display = collections.namedtuple('Display', ['width', 'height', 'rotation'])
    __minicap = '/data/local/tmp/minicap'

    def __init__(self, client, serial):
        self._client = client
        self._serial = serial
        self._screenshot_method = 'minicap'

    def raw_cmd(self, *args):
        args = ['-s', self._serial] + list(args)
        return self._client.raw_cmd(*args)

    def adb_cmd(self, *args):
        """
        Unix style output, already replace \r\n to \n
        """
        p = self.raw_cmd(*args)
        return p.communicate()[0].replace('\r\n', '\n')

    def adb_shell(self, *args):
        args = ['shell'] + list(args)
        return self.adb_cmd(*args)

    def keyevent(self, key):
        ''' Call: adb shell input keyevent $key '''
        self.adb_shell('input', 'keyevent', key)

    def remove(self, filename):
        ''' remove file '''
        self.adb_shell('rm', filename)

    def pull(self, source_file, target_file=None):
        if target_file is None:
            raise RuntimeError('Not supported now')
        self.adb_cmd('pull', source_file, target_file)

    @property
    def display(self):
        '''
        Return device width, height, rotation
        '''
        w, h = (0, 0)
        for line in self.adb_shell('dumpsys', 'display').splitlines():
            m = _DISPLAY_RE.search(line, 0)
            if not m:
                continue
            w = int(m.group('width'))
            h = int(m.group('height'))
            o = int(m.group('orientation'))
            w, h = min(w, h), max(w, h)
            return self.Display(w, h, o)

        output = self.adb_shell('LD_LIBRARY_PATH=/data/local/tmp', self.__minicap, '-i')
        try:
            data = json.loads(output)
            (w, h, o) = (data['width'], data['height'], data['rotation']/90)
            return self.Display(w, h, o)            
        except ValueError:
            pass

    def rotation(self):
        return self.display.rotation

    def _adb_screencap(self, scale=1.0):
        """
        capture screen with adb shell screencap
        """
        remote_file = tempfile.mktemp(dir='/data/local/tmp/', prefix='screencap-', suffix='.png')
        local_file = tempfile.mktemp(prefix='atx-screencap-', suffix='.png')
        self.adb_shell('screencap', '-p', remote_file)
        try:
            self.pull(remote_file, local_file)
            image = Image.open(local_file)
            image.load() # because Image is a lazy load function
            if scale is not None and scale != 1.0:
                image = image.resize([int(scale * s) for s in image.size], Image.BICUBIC)
            rotation = self.rotation()
            if rotation:
                method = getattr(Image, 'ROTATE_{}'.format(rotation*90))
                image = image.transpose(method)
            return image
        finally:
            self.remove(remote_file)
            os.unlink(local_file)

    def _adb_minicap(self, scale=1.0):
        remote_file = tempfile.mktemp(dir='/data/local/tmp/', prefix='minicap-', suffix='.jpg')
        local_file = tempfile.mktemp(prefix='atx-minicap-', suffix='.jpg')
        (w, h, r) = self.display
        params = '{x}x{y}@{rx}x{ry}/{r}'.format(x=w, y=h, rx=int(w*scale), ry=int(h*scale), r=r*90)
        try:
            self.adb_shell('LD_LIBRARY_PATH=/data/local/tmp', self.__minicap, '-s', '-P', params, '>', remote_file)
            self.pull(remote_file, local_file)
            with open(local_file, 'rb') as f:
                image = Image.open(StringIO(f.read()))
            return image
        finally:
            self.remove(remote_file)
            os.unlink(local_file)

    def screenshot(self, filename=None, scale=1.0, method=None):
        """
        take device screenshot
        """
        image = None
        method = method or self._screenshot_method
        if method == 'minicap':
            try:
                image = self._adb_minicap(scale)
            except Exception as e:
                logger.warn("use minicap failed, fallback to screencap. error detail: %s", e)
                self._screenshot_method = 'screencap'
                return self.screenshot(filename=filename, scale=scale)
        elif method == 'screencap':
            image = self._adb_screencap(scale)
        else:
            raise RuntimeError("No such method(%s)" % method)

        if filename:
            image.save(filename)
        return image
