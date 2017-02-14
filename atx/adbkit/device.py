#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import

import atexit
import os
import re
import json
import collections
import tempfile

from PIL import Image
from atx import logutils, imutils


logger = logutils.getLogger(__name__)

_DISPLAY_RE = re.compile(
    r'.*DisplayViewport{valid=true, .*orientation=(?P<orientation>\d+), .*deviceWidth=(?P<width>\d+), deviceHeight=(?P<height>\d+).*')
_PROP_PATTERN = re.compile(r'\[(?P<key>.*?)\]:\s*\[(?P<value>.*)\]')


class Device(object):
    Display = collections.namedtuple('Display', ['width', 'height', 'rotation'])
    Package = collections.namedtuple('Package', ['name', 'path'])
    __minicap = '/data/local/tmp/minicap'

    def __init__(self, client, serial):
        ''' TODO: client change to host, port '''
        self._client = client
        self._serial = serial
        self._screenshot_method = 'minicap'

    @property
    def serial(self):
        return self._serial
    
    def raw_cmd(self, *args, **kwargs):
        args = ['-s', self._serial] + list(args)
        return self._client.raw_cmd(*args, **kwargs)

    def run_cmd(self, *args, **kwargs):
        """
        Unix style output, already replace \r\n to \n

        Args:
            - timeout (float): timeout for a command exec
        """
        timeout = kwargs.pop('timeout', None)
        p = self.raw_cmd(*args, **kwargs)
        return p.communicate(timeout=timeout)[0].decode('utf-8').replace('\r\n', '\n')

    def shell(self, *args, **kwargs):
        """
        Run command `adb shell`
        """
        args = ['shell'] + list(args)
        return self.run_cmd(*args, **kwargs)

    def keyevent(self, key):
        ''' Call: adb shell input keyevent $key '''
        self.shell('input', 'keyevent', key)

    def remove(self, filename):
        """ 
        Remove file from device
        """
        output = self.shell('rm', filename)
        # any output means rm failed.
        return False if output else True

    def install(self, filename):
        """
        TOOD(ssx): Install apk into device, show progress

        Args:
            - filename(string): apk file path
        """
        return self.run_cmd('install', '-rt', filename)

    def uninstall(self, package_name, keep_data=False):
        """
        Uninstall package

        Args:
            - package_name(string): package name ex: com.example.demo
            - keep_data(bool): keep the data and cache directories
        """
        if keep_data:
            return self.run_cmd('uninstall', '-k', package_name)
        else:
            return self.run_cmd('uninstall', package_name)

    def pull(self, source_file, target_file=None):
        if target_file is None:
            raise RuntimeError('Not supported now')
        self.run_cmd('pull', source_file, target_file)

    @property
    def display(self):
        '''
        Return device width, height, rotation
        '''
        w, h = (0, 0)
        for line in self.shell('dumpsys', 'display').splitlines():
            m = _DISPLAY_RE.search(line, 0)
            if not m:
                continue
            w = int(m.group('width'))
            h = int(m.group('height'))
            o = int(m.group('orientation'))
            w, h = min(w, h), max(w, h)
            return self.Display(w, h, o)

        output = self.shell('LD_LIBRARY_PATH=/data/local/tmp', self.__minicap, '-i')
        try:
            data = json.loads(output)
            (w, h, o) = (data['width'], data['height'], data['rotation']/90)
            return self.Display(w, h, o)            
        except ValueError:
            pass

    def rotation(self):
        """
        Android rotation
        Return:
            - int [0-4]
        """
        return self.display.rotation
    
    def properties(self):
        '''
        Android Properties, extracted from `adb shell getprop`

        Returns:
            dict of props, for
            example:
                {'ro.bluetooth.dun': 'true'}
        '''
        props = {}
        for line in self.shell(['getprop']).splitlines():
            m = _PROP_PATTERN.match(line)
            if m:
                props[m.group('key')] = m.group('value')
        return props

    def packages(self):
        """
        Show all packages
        """
        pattern = re.compile(r'package:(/[^=]+\.apk)=([^\s]+)')
        packages = []
        for line in self.shell('pm', 'list', 'packages', '-f').splitlines():
            m = pattern.match(line)
            if not m:
                continue
            path, name = m.group(1), m.group(2)
            packages.append(self.Package(name, path))
        return packages

    def _adb_screencap(self, scale=1.0):
        """
        capture screen with adb shell screencap
        """
        remote_file = tempfile.mktemp(dir='/data/local/tmp/', prefix='screencap-', suffix='.png')
        local_file = tempfile.mktemp(prefix='atx-screencap-', suffix='.png')
        self.shell('screencap', '-p', remote_file)
        try:
            self.pull(remote_file, local_file)
            image = imutils.open_as_pillow(local_file)
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
        """
        capture screen with minicap

        https://github.com/openstf/minicap
        """
        remote_file = tempfile.mktemp(dir='/data/local/tmp/', prefix='minicap-', suffix='.jpg')
        local_file = tempfile.mktemp(prefix='atx-minicap-', suffix='.jpg')
        (w, h, r) = self.display
        params = '{x}x{y}@{rx}x{ry}/{r}'.format(x=w, y=h, rx=int(w*scale), ry=int(h*scale), r=r*90)
        try:
            self.shell('LD_LIBRARY_PATH=/data/local/tmp', self.__minicap, '-s', '-P', params, '>', remote_file)
            self.pull(remote_file, local_file)
            image = imutils.open_as_pillow(local_file)
            return image
        finally:
            self.remove(remote_file)
            os.unlink(local_file)

    def screenshot(self, filename=None, scale=1.0, method=None):
        """
        Take device screenshot

        Args:
            - filename(string): optional, save int filename
            - scale(float): scale size
            - method(string): one of minicap,screencap

        Return:
            PIL.Image
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

    def click(self, x, y):
        '''
        same as adb -s ${SERIALNO} shell input tap x y
        FIXME(ssx): not tested on horizontal screen
        '''
        self.shell('input', 'tap', str(x), str(y))

    def forward(self, local_port, remote_port):
        '''
        adb port forward. return local_port
        TODO: not tested
        '''
        return self._client.forward(self.serial, local_port, remote_port)

    def is_locked(self):
        """
        Returns:
            - lock state(bool)
        Raises:
            RuntimeError
        """
        _lockScreenRE = re.compile('mShowingLockscreen=(true|false)')
        m = _lockScreenRE.search(self.shell('dumpsys', 'window', 'policy'))
        if m:
            return (m.group(1) == 'true')
        raise RuntimeError("Couldn't determine screen lock state")

    def is_screen_on(self):
        '''
        Checks if the screen is ON.
        Returns:
            True if the device screen is ON
        Raises:
            RuntimeError
        '''

        _screenOnRE = re.compile('mScreenOnFully=(true|false)')
        m = _screenOnRE.search(self.shell('dumpsys', 'window', 'policy'))
        if m:
            return (m.group(1) == 'true')
        raise RuntimeError("Couldn't determine screen ON state")

    def wake(self):
        """
        Wake up device if device locked
        """
        if not self.is_screen_on():
            self.keyevent('POWER')

    def is_keyboard_shown(self):
        dim = self.shell('dumpsys', 'input_method')
        if dim:
            # FIXME: API >= 15 ?
            return "mInputShown=true" in dim
        return False

    def current_app(self):
        """
        Return: dict(package, activity, pid?)
        Raises:
            RuntimeError
        """
        # try: adb shell dumpsys activity top
        _activityRE = re.compile(r'ACTIVITY (?P<package>[^/]+)/(?P<activity>[^/\s]+) \w+ pid=(?P<pid>\d+)')
        m = _activityRE.search(self.shell('dumpsys', 'activity', 'top'))
        if m:
            return dict(package=m.group('package'), activity=m.group('activity'), pid=int(m.group('pid')))

        # try: adb shell dumpsys window windows
        _focusedRE = re.compile('mFocusedApp=.*ActivityRecord{\w+ \w+ (?P<package>.*)/(?P<activity>.*) .*')
        m = _focusedRE.search(self.shell('dumpsys', 'window', 'windows'))
        if m:
            return dict(package=m.group('package'), activity=m.group('activity'))
        raise RuntimeError("Couldn't get focused app")
