#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import

import re
import json
import collections


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
        p = self.raw_cmd(*args)
        return p.communicate()[0]

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
            # return self.Display(w, h, o)

        output = self.adb_shell('LD_LIBRARY_PATH=/data/local/tmp', self.__minicap, '-i')
        try:
            data = json.loads(output)
            (w, h, o) = (data['width'], data['height'], data['rotation']/90)
            return self.Display(w, h, o)            
        except ValueError:
            pass

    def _adb_screencap(self):
        """ TODO(ssx): need to clean tmp file and fix rotation """
        tmp_screen = '/data/local/tmp/_tmp_screencap.png'
        self.adb_shell('screencap', '-p', tmp_screen)
        self.pull(tmp_screen, './_tmp.png')

    # def _screenshot_minicap(self):
    #     phone_tmp_file = '/data/local/tmp/_atx_screen-{}.jpg'.format(self._randid)
    #     local_tmp_file = tempfile.mktemp(prefix='atx-tmp-', suffix='.jpg')
    #     command = 'LD_LIBRARY_PATH=/data/local/tmp /data/local/tmp/minicap -P {} -s > {}'.format(
    #         self._minicap_params(), phone_tmp_file)
    #     try:
    #         self.adb_shell(command)
    #         self.adb_cmd(['pull', phone_tmp_file, local_tmp_file])
    #         image = imutils.open_as_pillow(local_tmp_file)

    #         # Fix rotation not rotate right.
    #         (width, height) = image.size
    #         if self.screen_rotation in [1, 3] and width < height:
    #             image = image.rotate(90, Image.BILINEAR, expand=True)
    #         return image
    #     except IOError:
    #         raise IOError("Screenshot use minicap failed.")
    #     finally:
    #         # remove_force(local_tmp_file)
    #         self.adb_shell(['rm', phone_tmp_file])

    def screenshot(self, filename=None, scale=1.0):
        pass

        # w, h = self.info['displayWidth'], self.info['displayHeight']
        # w, h = min(w, h), max(w, h)
        # return collections.namedtuple('Display', ['width', 'height'])(w, h)

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
