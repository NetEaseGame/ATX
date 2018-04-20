#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# License under MIT

from __future__ import absolute_import
from __future__ import print_function

import collections
import contextlib
import base64
import os
import re
import sys
import subprocess
import time
import tempfile
import warnings
import logging
import uuid
import six
import xml.dom.minidom

import uiautomator2
from PIL import Image

from atx import consts
from atx import errors
from atx import patch
from atx import base
from atx import imutils
from atx import strutils
from atx.drivers import Bounds
from atx import logutils
from atx.drivers.mixin import DeviceMixin, hook_wrap
from atx import adbkit


_DISPLAY_RE = re.compile(
    r'.*DisplayViewport{valid=true, .*orientation=(?P<orientation>\d+), .*deviceWidth=(?P<width>\d+), deviceHeight=(?P<height>\d+).*')

_PROP_PATTERN = re.compile(
    r'\[(?P<key>.*?)\]:\s*\[(?P<value>.*)\]')

_INPUT_METHOD_RE = re.compile(
    r'mCurMethodId=([-_./\w]+)')

_DEFAULT_IME = 'com.netease.atx.assistant/.ime.Utf7ImeService'

UINode = collections.namedtuple('UINode', [
    'xml',
    'bounds',
    'selected', 'checkable', 'clickable', 'scrollable', 'focusable', 'enabled', 'focused', 'long_clickable',
    'password',
    'class_name',
    'index', 'resource_id',
    'text', 'content_desc',
    'package'])

log = logutils.getLogger(__name__)


def getenvs(*names):
    for name in names:
        if os.getenv(name):
            return os.getenv(name)


class AndroidDevice(DeviceMixin):
    def __init__(self, serial=None, **kwargs):
        """Initial AndroidDevice
        Args:
            serial (str): serial or wlan ip

        Returns:
            AndroidDevice object

        Raises:
            EnvironmentError
        """
        self.__display = None
        serial = serial or getenvs('ATX_ADB_SERIALNO', 'ANDROID_SERIAL')
        self._host = kwargs.get('host') or getenvs(
            'ATX_ADB_HOST', 'ANDROID_ADB_SERVER_HOST') or '127.0.0.1'
        self._port = int(kwargs.get('port') or getenvs(
            'ATX_ADB_PORT', 'ANDROID_ADB_SERVER_PORT') or 5037)

        self._adb_client = adbkit.Client(self._host, self._port)
        self._adb_device = self._adb_client.device(serial)
        # self._adb_shell_timeout = 30.0 # max adb shell exec time

        # uiautomator2
        self._uiauto = uiautomator2.connect_usb(serial)
        if not self._uiauto.alive:
            self._uiauto.healthcheck(unlock=False)

        DeviceMixin.__init__(self)
        self._randid = base.id_generator(5)

        self.screen_rotation = None

        # inherts from atx-uiautomator
        self.swipe = self._uiauto.swipe
        self.drag = self._uiauto.drag
        self.press = self._uiauto.press
        self.long_click = self._uiauto.long_click
        self.dump = self._uiauto.dump_hierarchy

    @property
    def info(self):
        return self._uiauto.info

    @property
    def uiautomator(self):
        """
        Returns:
            uiautomator: Device object describes in https://github.com/openatx/atx-uiautomator
        """
        return self._uiauto

    def __call__(self, *args, **kwargs):
        return self._uiauto(*args, **kwargs)

    @property
    def serial(self):
        """ Android Device Serial Number """
        return self._uiauto.serial

    @property
    def adb_device(self):
        return self._adb_device

    @property
    def wlan_ip(self):
        """ Wlan IP """
        return self.adb_shell(['getprop', 'dhcp.wlan0.ipaddress']).strip()

    def forward(self, device_port, local_port=None):
        """Forward device port to local
        Args:
            device_port: port inside device
            local_port: port on PC, if this value is None, a port will random pick one.

        Returns:
            tuple, (host, local_port)
        """
        port = self._adb_device.forward(device_port, local_port)
        return (self._host, port)

    def current_app(self):
        """Get current app (package, activity)
        Returns:
            Return: dict(package, activity, pid?)

        Raises:
            RuntimeError
        """
        return self._uiauto.current_app()

    @property
    def current_package_name(self):
        return self.info['currentPackageName']

    def is_app_alive(self, package_name):
        """ Deprecated: use current_package_name instaed.
        Check if app in running in foreground """
        return self.info['currentPackageName'] == package_name

    # def sleep(self, secs=None):
    #     """Depreciated. use delay instead."""
    #     if secs is None:
    #         self._uiauto.sleep()
    #     else:
    #         self.delay(secs)

    @property
    def display(self):
        """Virtual keyborad may get small d.info['displayHeight']
        """
        for line in self.adb_shell('dumpsys display').splitlines():
            m = _DISPLAY_RE.search(line, 0)
            if not m:
                continue
            w = int(m.group('width'))
            h = int(m.group('height'))
            return collections.namedtuple('Display', ['width', 'height'])(w, h)
        else:
            w, h = self.info['displayWidth'], self.info['displayHeight']
            return collections.namedtuple('Display', ['width', 'height'])(w, h)

    @property
    def rotation(self):
        """
        Rotaion of the phone

        0: normal
        1: home key on the right
        2: home key on the top
        3: home key on the left
        """
        if self.screen_rotation in range(4):
            return self.screen_rotation
        return self.adb_device.rotation() or self.info['displayRotation']

    @rotation.setter
    def rotation(self, r):
        if not isinstance(r, int):
            raise TypeError("r must be int")
        self.screen_rotation = r

    def _mktemp(self, suffix='.jpg'):
        prefix = 'atx-tmp-{}-'.format(uuid.uuid1())
        return tempfile.mktemp(prefix=prefix, suffix='.jpg')

    # @hook_wrap(consts.EVENT_CLICK)
    def do_tap(self, x, y):
        """
        Touch specify position

        Args:
            x, y: int

        Returns:
            None
        """
        return self._uiauto.click(x, y)

    def _take_screenshot(self):
        return self._uiauto.screenshot()

    def raw_cmd(self, *args, **kwargs):
        '''
        Return subprocess.Process instance
        '''
        return self.adb_device.raw_cmd(*args, **kwargs)

    def adb_cmd(self, command, **kwargs):
        '''
        Run adb command, for example: adb(['pull', '/data/local/tmp/a.png'])

        Args:
            command: string or list of string

        Returns:
            command output
        '''
        kwargs['timeout'] = kwargs.get('timeout', self._adb_shell_timeout)
        if isinstance(command, list) or isinstance(command, tuple):
            return self.adb_device.run_cmd(*list(command), **kwargs)
        return self.adb_device.run_cmd(command, **kwargs)

    def adb_shell(self, *args):
        '''
        Run adb shell command

        Args:
            args: string or list of string

        Returns:
            command output
        '''
        return self._uiauto.adb_shell(*args)

    @property
    def properties(self):
        '''
        Android Properties, extracted from `adb shell getprop`

        Returns:
            dict of props, for
            example:

                {'ro.bluetooth.dun': 'true'}
        '''
        props = {}
        for line in self.adb_shell(['getprop']).splitlines():
            m = _PROP_PATTERN.match(line)
            if m:
                props[m.group('key')] = m.group('value')
        return props

    def start_app(self, package_name, activity=None, stop=False):
        '''
        Start application

        Args:
            - package_name (string): like com.example.app1
            - activity (string): optional, activity name

        Returns time used (unit second), if activity is not None

        Document: usage: adb shell am start
            -D: enable debugging
            -W: wait for launch to complete
            --start-profiler <FILE>: start profiler and send results to <FILE>
            --sampling INTERVAL: use sample profiling with INTERVAL microseconds
                between samples (use with --start-profiler)
            -P <FILE>: like above, but profiling stops when app goes idle
            -R: repeat the activity launch <COUNT> times.  Prior to each repeat,
                the top activity will be finished.
            -S: force stop the target app before starting the activity
            --opengl-trace: enable tracing of OpenGL functions
            --user <USER_ID> | current: Specify which user to run as; if not
                specified then run as the current user.
        '''
        _pattern = re.compile(r'TotalTime: (\d+)')
        if activity is None:
            self.adb_shell(['monkey', '-p', package_name, '-c',
                            'android.intent.category.LAUNCHER', '1'])
        else:
            args = ['-W']
            if stop:
                args.append('-S')
            output = self.adb_shell(
                ['am', 'start'] + args + ['-n', '%s/%s' % (package_name, activity)])
            m = _pattern.search(output)
            if m:
                return int(m.group(1))/1000.0

    def stop_app(self, package_name, clear=False):
        '''
        Stop application

        Args:
            package_name: string like com.example.app1
            clear: bool, remove user data

        Returns:
            None
        '''
        if clear:
            self.adb_shell(['pm', 'clear', package_name])
        else:
            self.adb_shell(['am', 'force-stop', package_name])
        return self

    def _parse_xml_node(self, node):
        # ['bounds', 'checkable', 'class', 'text', 'resource_id', 'package']
        __alias = {
            'class': 'class_name',
            'resource-id': 'resource_id',
            'content-desc': 'content_desc',
            'long-clickable': 'long_clickable',
        }

        def parse_bounds(text):
            m = re.match(r'\[(\d+),(\d+)\]\[(\d+),(\d+)\]', text)
            if m is None:
                return None
            return Bounds(*map(int, m.groups()))

        def str2bool(v):
            return v.lower() in ("yes", "true", "t", "1")

        def convstr(v):
            return v.encode('utf-8')

        parsers = {
            'bounds': parse_bounds,
            'text': convstr,
            'class_name': convstr,
            'resource_id': convstr,
            'package': convstr,
            'checkable': str2bool,
            'scrollable': str2bool,
            'focused': str2bool,
            'clickable': str2bool,
            'enabled': str2bool,
            'selected': str2bool,
            'long_clickable': str2bool,
            'focusable': str2bool,
            'password': str2bool,
            'index': int,
            'content_desc': convstr,
        }
        ks = {}
        for key, value in node.attributes.items():
            key = __alias.get(key, key)
            f = parsers.get(key)
            if value is None:
                ks[key] = None
            elif f:
                ks[key] = f(value)
        for key in parsers.keys():
            ks[key] = ks.get(key)
        ks['xml'] = node

        return UINode(**ks)

    def dump_nodes(self):
        """Dump current screen UI to list
        Returns:
            List of UINode object, For
            example:

            [UINode(
                bounds=Bounds(left=0, top=0, right=480, bottom=168),
                checkable=False,
                class_name='android.view.View',
                text='',
                resource_id='',
                package='com.sonyericsson.advancedwidget.clock')]
        """
        xmldata = self._uiauto.dump()
        dom = xml.dom.minidom.parseString(xmldata.encode('utf-8'))
        root = dom.documentElement
        nodes = root.getElementsByTagName('node')
        ui_nodes = []
        for node in nodes:
            ui_nodes.append(self._parse_xml_node(node))
        return ui_nodes

    def dump_view(self):
        """Current Page XML
        """
        warnings.warn("deprecated, source() instead", DeprecationWarning)
        return self._uiauto.dump()

    def source(self, *args, **kwargs):
        """
        Dump page xml
        """
        return self._uiauto.dump(*args, **kwargs)

    def keyevent(self, keycode):
        """call adb shell input keyevent ${keycode}

        Args:
            - keycode(string): for example, KEYCODE_ENTER

        keycode need reference:
        http://developer.android.com/reference/android/view/KeyEvent.html
        """
        self.adb_shell(['input', 'keyevent', keycode])

    def type(self, s, enter=False, clear=False):
        """Input some text, this method has been tested not very stable on some device.
        "Hi world" maybe spell into "H iworld"

        Args:
            - s: string (text to input), better to be unicode
            - enter(bool): input enter at last
            - next(bool): perform editor action Next
            - clear(bool): clear text before type
            - ui_select_kwargs(**): tap then type

        The android source code show that
        space need to change to %s
        insteresting thing is that if want to input %s, it is really unconvinent.
        android source code can be found here.
        https://android.googlesource.com/platform/frameworks/base/+/android-4.4.2_r1/cmds/input/src/com/android/commands/input/Input.java#159
        app source see here: https://github.com/openatx/android-unicode
        """

        if clear:
            self.clear_text()

        self._uiauto.send_keys(s)

        if enter:
            self.keyevent('KEYCODE_ENTER')
        # if next:
        #     # FIXME(ssx): maybe KEYCODE_NAVIGATE_NEXT
        #     self.adb_shell(['am', 'broadcast', '-a', 'ADB_EDITOR_CODE', '--ei', 'code', '5'])

    def clear_text(self, count=100):
        """Clear text
        Args:
            - count (int): send KEY_DEL count
        """
        self._uiauto.clear_text()

    def input_methods(self):
        """
        Get all input methods

        Return example: ['com.sohu.inputmethod.sogou/.SogouIME', 'android.unicode.ime/.Utf7ImeService']
        """
        imes = []
        for line in self.adb_shell(['ime', 'list', '-s', '-a']).splitlines():
            line = line.strip()
            if re.match('^.+/.+$', line):
                imes.append(line)
        return imes

    def current_ime(self):
        ''' Get current input method '''
        dumpout = self.adb_shell(['dumpsys', 'input_method'])
        m = _INPUT_METHOD_RE.search(dumpout)
        if m:
            return m.group(1)

        # Maybe no need to raise error
        # raise RuntimeError("Canot detect current input method")
