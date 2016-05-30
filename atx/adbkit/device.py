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


_DISPLAY_RE = re.compile(
    r'.*DisplayViewport{valid=true, .*orientation=(?P<orientation>\d+), .*deviceWidth=(?P<width>\d+), deviceHeight=(?P<height>\d+).*')

_PROP_PATTERN = re.compile(
    r'\[(?P<key>.*?)\]:\s*\[(?P<value>.*)\]')

class Device(object):
    Display = collections.namedtuple('Display', ['width', 'height', 'rotation'])
    __minicap = '/data/local/tmp/minicap'

    def __init__(self, client, serial):
        self._client = client
        self._serial = serial

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
        self.adb_shell('screencap', '-p', remote_file)
        local_file = tempfile.mktemp(prefix='atx-screencap-', suffix='.png')
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

    def screenshot(self, filename=None, scale=1.0):
        """
        take device screenshot
        """
        image = self._adb_screencap(scale)
        if filename:
            image.save(filename)
        return image

    # def screenshot_minicap(self, filename='screenshot.png', format='pil', scale=1.0):
    #     binary = '/data/local/tmp/minicap'
    #     if not is_file_exists(binary):
    #         raise EnvironmentError('minicap not available')

    #     out = _adb_output('shell', 'LD_LIBRARY_PATH=/data/local/tmp', binary, '-i')
    #     m = re.search('"width": (\d+).*"height": (\d+).*"rotation": (\d+)', out, re.S)
    #     w, h, r = map(int, m.groups())
    #     w, h = min(w, h), max(w, h)
    #     params = '{x}x{y}@{x}x{y}/{r}'.format(x=w, y=h, r=r)
    #     temp = '/data/local/tmp/minicap_screen.png'
    #     _adb_call('shell', 'LD_LIBRARY_PATH=/data/local/tmp', binary, '-s', '-P', params, '>', temp)
    #     pull(temp, filename)
    #     return image_file_reform(filename, format, scale)
