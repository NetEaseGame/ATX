#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# License under MIT


from __future__ import absolute_import

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
import xml.dom.minidom

from uiautomator import Device as UiaDevice
from uiautomator import AutomatorDeviceObject
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


class AndroidDevice(DeviceMixin, UiaDevice):
    def __init__(self, serialno=None, **kwargs):
        """Initial AndroidDevice
        Args:
            serialno: string specify which device

        Returns:
            AndroidDevice object

        Raises:
            EnvironmentError
        """
        self.__display = None
        serialno = serialno or getenvs('ATX_ADB_SERIALNO', 'ANDROID_SERIAL')
        self._host = kwargs.get('host') or getenvs('ATX_ADB_HOST', 'ANDROID_ADB_SERVER_HOST') or '127.0.0.1'
        self._port = int(kwargs.get('port') or getenvs('ATX_ADB_PORT', 'ANDROID_ADB_SERVER_PORT') or 5037)

        self._adb_client = adbkit.Client(self._host, self._port)
        self._adb_device = self._adb_client.device(serialno)
        self._adb_shell_timeout = 30.0 # max adb shell exec time

        kwargs['adb_server_host'] = kwargs.pop('host', self._host)
        kwargs['adb_server_port'] = kwargs.pop('port', self._port)
        UiaDevice.__init__(self, serialno, **kwargs)
        DeviceMixin.__init__(self)

        self._randid = base.id_generator(5)
        self._uiauto = super(AndroidDevice, self)

        self.screen_rotation = None
        self.screenshot_method = consts.SCREENSHOT_METHOD_AUTO
        self.last_screenshot = None

    @property
    def serial(self):
        """ Android Device Serial Number """
        return self._adb_device.serial

    @property
    def adb_server_host(self):
        return self._host

    @property
    def adb_server_port(self):
        return self._port

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
            namedtuple ['package', 'activity', 'pid']
            activity, pid maybe None

        Raises:
            RuntimeError
        """
        AppInfo = collections.namedtuple('AppInfo', ['package', 'activity', 'pid'])
        try:
            ai = self._adb_device.current_app()
            return AppInfo(ai['package'], ai['activity'], ai.get('pid'))
        except RuntimeError:
            return AppInfo(self.info['currentPackageName'], None, None)

    @property
    def current_package_name(self):
        return self.info['currentPackageName']

    def is_app_alive(self, package_name):
        """ Deprecated: use current_package_name instaed.
        Check if app in running in foreground """
        return self.info['currentPackageName'] == package_name

    def sleep(self, secs=None):
        """Depreciated. use delay instead."""
        if secs is None:
            self._uiauto.sleep()
        else:
            self.delay(secs)

    @property
    def display(self):
        """Virtual keyborad may get small d.info['displayHeight']
        """
        if self.__display:
            return self.__display
        w, h = (0, 0)
        for line in self.adb_shell('dumpsys display').splitlines():
            m = _DISPLAY_RE.search(line, 0)
            if not m:
                continue
            w = int(m.group('width'))
            h = int(m.group('height'))
            # o = int(m.group('orientation'))
            w, h = min(w, h), max(w, h)
            self.__display = collections.namedtuple('Display', ['width', 'height'])(w, h)
            return self.__display

        w, h = self.info['displayWidth'], self.info['displayHeight']
        w, h = min(w, h), max(w, h)
        self.__display = collections.namedtuple('Display', ['width', 'height'])(w, h)
        return self.__display
    
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
    
    def _minicap_params(self):
        """
        Used about 0.1s
        uiautomator d.info is now well working with device which has virtual menu.
        """
        rotation = self.rotation 

        # rotation not working on SumSUNG 9502
        return '{x}x{y}@{x}x{y}/{r}'.format(
            x=self.display.width,
            y=self.display.height,
            r=rotation*90)
    
    def _mktemp(self, suffix='.jpg'):
        prefix= 'atx-tmp-{}-'.format(uuid.uuid1())
        return tempfile.mktemp(prefix=prefix, suffix='.jpg')

    def _screenshot_minicap(self):
        phone_tmp_file = '/data/local/tmp/_atx_screen-{}.jpg'.format(self._randid)
        local_tmp_file = self._mktemp()
        command = 'LD_LIBRARY_PATH=/data/local/tmp /data/local/tmp/minicap -P {} -s > {}'.format(
            self._minicap_params(), phone_tmp_file)
        try:
            self.adb_shell(command)
            self.adb_cmd(['pull', phone_tmp_file, local_tmp_file])
            image = imutils.open_as_pillow(local_tmp_file)
            # Fix rotation not rotate right.
            (width, height) = image.size
            if self.screen_rotation in [1, 3] and width < height:
                image = image.rotate(90, Image.BILINEAR, expand=True)
            return image
        except IOError:
            raise IOError("Screenshot use minicap failed.")
        finally:
            self.adb_shell(['rm', phone_tmp_file])
            base.remove_force(local_tmp_file)

    def _screenshot_uiauto(self):
        tmp_file = self._mktemp()
        self._uiauto.screenshot(tmp_file)
        try:
            return imutils.open_as_pillow(tmp_file)
        except IOError:
            raise IOError("Screenshot use uiautomator failed.")
        finally:
            base.remove_force(tmp_file)

    @hook_wrap(consts.EVENT_CLICK)
    def click(self, x, y):
        """
        Touch specify position

        Args:
            x, y: int

        Returns:
            None
        """
        return self._uiauto.click(x, y)

    def _take_screenshot(self):
        screen = None
        if self.screenshot_method == consts.SCREENSHOT_METHOD_UIAUTOMATOR:
            screen = self._screenshot_uiauto()
        elif self.screenshot_method == consts.SCREENSHOT_METHOD_MINICAP:
            screen = self._screenshot_minicap()
        elif self.screenshot_method == consts.SCREENSHOT_METHOD_AUTO:
            try:
                screen = self._screenshot_minicap()
                self.screenshot_method = consts.SCREENSHOT_METHOD_MINICAP
            except IOError:
                screen = self._screenshot_uiauto()
                self.screenshot_method = consts.SCREENSHOT_METHOD_UIAUTOMATOR
        else:
            raise TypeError('Invalid screenshot_method')
        return screen

    @hook_wrap(consts.EVENT_SCREENSHOT)
    def screenshot(self, filename=None):
        """
        Take screen snapshot

        Args:
            filename: filename where save to, optional

        Returns:
            PIL.Image object

        Raises:
            TypeError, IOError
        """
        try:
            screen = self._take_screenshot()
        except IOError:
            # try taks screenshot again
            screen = self._take_screenshot()

        if filename:
            save_dir = os.path.dirname(filename) or '.'
            if not os.path.exists(save_dir):
                os.makedirs(save_dir)
            screen.save(filename)

        self.last_screenshot = screen
        return screen

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

    def adb_shell(self, command, **kwargs):
        '''
        Run adb shell command

        Args:
            command: string or list of string

        Returns:
            command output
        '''
        if isinstance(command, list) or isinstance(command, tuple):
            return self.adb_cmd(['shell'] + list(command), **kwargs)
        else:
            return self.adb_cmd(['shell'] + [command], **kwargs)

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

    def start_app(self, package_name, activity=None):
        '''
        Start application

        Args:
            - package_name (string): like com.example.app1
            - activity (string): optional, activity name

        Returns time used (unit second), if activity is not None
        '''
        _pattern = re.compile(r'TotalTime: (\d+)')
        if activity is None:
            self.adb_shell(['monkey', '-p', package_name, '-c', 'android.intent.category.LAUNCHER', '1'])
        else:
            output = self.adb_shell(['am', 'start', '-W', '-n', '%s/%s' % (package_name, activity)])
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

    def takeSnapshot(self, filename):
        '''
        Deprecated, use screenshot instead.
        '''
        warnings.warn("deprecated, use snapshot instead", DeprecationWarning)
        return self.screenshot(filename)

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
        return self._uiauto.dump()

    def _escape_text(self, s, utf7=False):
        s = s.replace(' ', '%s')
        if utf7:
            s = s.encode('utf-7')
        return s

    def keyevent(self, keycode):
        """call adb shell input keyevent ${keycode}

        Args:
            - keycode(string): for example, KEYCODE_ENTER

        keycode need reference:
        http://developer.android.com/reference/android/view/KeyEvent.html
        """
        self.adb_shell(['input', 'keyevent', keycode])

    def enable_ime(self, ime):
        """
        Enable input methods

        Args:
            - ime(string): for example "android.unicode.ime/.Utf7ImeService"
        """
        self.adb_shell(['ime', 'enable', ime])
        self.adb_shell(['ime', 'set', ime])

    def _is_utf7ime(self, ime=None):
        if ime is None:
            ime = self.current_ime()
        return ime in [
            'android.unicode.ime/.Utf7ImeService',
            'com.netease.atx.assistant/.ime.Utf7ImeService',
            'com.netease.nie.yosemite/.ime.ImeService']

    def _prepare_ime(self):
        if self._is_utf7ime():
            return True

        for ime in self.input_methods():
            if self._is_utf7ime(ime):
                self.enable_ime(ime)
                return True
        return False
        # raise RuntimeError("Input method for programers not detected.\n" +
        #     "\tInstall with: python -m atx install atx-assistant")

    def _shell_type(self, text):
        first = True
        for s in text.split('%s'):
            if first:
                first = False
            else:
                self.adb_shell(['input', 'text', '%'])
                s = 's' + s
            if s == '':
                continue
            estext = self._escape_text(s)
            self.adb_shell(['input', 'text', estext])

    def type(self, text, enter=False, next=False):
        """Input some text, this method has been tested not very stable on some device.
        "Hi world" maybe spell into "H iworld"

        Args:
            - text: string (text to input), better to be unicode
            - enter(bool): input enter at last
            - next(bool): perform editor action Next

        The android source code show that
        space need to change to %s
        insteresting thing is that if want to input %s, it is really unconvinent.
        android source code can be found here.
        https://android.googlesource.com/platform/frameworks/base/+/android-4.4.2_r1/cmds/input/src/com/android/commands/input/Input.java#159
        app source see here: https://github.com/openatx/android-unicode
        """
        if self._prepare_ime():
            estext = base64.b64encode(text.encode('utf-7'))
            self.adb_shell(['am', 'broadcast', '-a', 'ADB_INPUT_TEXT', '--es', 'format', 'base64', '--es', 'msg', estext])
        else:
            self._shell_type(text)

        if enter:
            self.keyevent('KEYCODE_ENTER')
        if next:
            # FIXME(ssx): maybe KEYCODE_NAVIGATE_NEXT
            self.adb_shell(['am', 'broadcast', '-a', 'ADB_EDITOR_CODE', '--ei', 'code', '5'])

    def clear_text(self, count=100):
        """Clear text
        Args:
            - count (int): send KEY_DEL count
        """
        self._prepare_ime()
        self.keyevent('KEYCODE_MOVE_END')
        self.adb_shell(['am', 'broadcast', '-a', 'ADB_INPUT_CODE', '--ei', 'code', '67', '--ei', 'repeat', str(count)])

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
