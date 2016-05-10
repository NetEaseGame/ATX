#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# License under MIT


from __future__ import absolute_import

import collections
import os
import re
import sys
import subprocess
import time
import tempfile
import warnings
import logging
import xml.dom.minidom

from uiautomator import Device as UiaDevice
from uiautomator import AutomatorDeviceObject
from PIL import Image

from atx import consts
from atx import errors
from atx import patch
from atx import base
from atx import imutils
from atx import adb
from atx import strutils
from atx.device import Bounds
from atx import logutils
from atx.device.mixin import DeviceMixin, hook_wrap


DISPLAY_RE = re.compile(
    r'.*DisplayViewport{valid=true, .*orientation=(?P<orientation>\d+), .*deviceWidth=(?P<width>\d+), deviceHeight=(?P<height>\d+).*')

PROP_PATTERN = re.compile(
    r'\[(?P<key>.*?)\]:\s*\[(?P<value>.*)\]')

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


def getenv(name, default_value=None, type=str):
    value = os.getenv(name)
    return type(value) if value else default_value

class AndroidMixin(object):
    def __init__(self, serialno=None):
        pass

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
        serialno = serialno or getenv('ATX_ADB_SERIALNO', None)
        self._host = kwargs.get('host', getenv('ATX_ADB_HOST', '127.0.0.1'))
        self._port = kwargs.get('port', getenv('ATX_ADB_PORT', 5037, type=int))
        self._adb = adb.Adb(serialno, self._host, self._port)
        serialno = self._adb.device_serial()

        kwargs['adb_server_host'] = kwargs.pop('host', self._host)
        kwargs['adb_server_port'] = kwargs.pop('port', self._port)
        UiaDevice.__init__(self, serialno, **kwargs)
        DeviceMixin.__init__(self)

        self._randid = base.id_generator(5)
        self._serial = serialno
        self._uiauto = super(AndroidDevice, self)

        self.screen_rotation = None
        self.screenshot_method = consts.SCREENSHOT_METHOD_AUTO
        self.last_screenshot = None

    @property
    def serial(self):
        """ Android Device Serial Number """
        return self._serial
    
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
        port = self._adb.forward(device_port, local_port)
        return (self._host, port)

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
    @patch.run_once
    def display(self):
        """Virtual keyborad may get small d.info['displayHeight']
        """
        w, h = (0, 0)
        for line in self.adb_shell('dumpsys display').splitlines():
            m = DISPLAY_RE.search(line, 0)
            if not m:
                continue
            w = int(m.group('width'))
            h = int(m.group('height'))
            # o = int(m.group('orientation'))
            w, h = min(w, h), max(w, h)
            return collections.namedtuple('Display', ['width', 'height'])(w, h)

        w, h = self.info['displayWidth'], self.info['displayHeight']
        w, h = min(w, h), max(w, h)
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
        return self.info['displayRotation']
    
    def _minicap_params(self):
        """
        Used about 0.1s
        uiautomator d.info is now well working with device which has virtual menu.
        """
        rotation = self.screen_rotation 
        if self.screen_rotation is None:
            rotation = self.rotation

        # rotation not working on SumSUNG 9502
        return '{x}x{y}@{x}x{y}/{r}'.format(
            x=self.display.width,
            y=self.display.height,
            r=rotation*90)
    
    def _screenshot_minicap(self):
        phone_tmp_file = '/data/local/tmp/_atx_screen-{}.jpg'.format(self._randid)
        local_tmp_file = tempfile.mktemp(prefix='atx-tmp-', suffix='.jpg')
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
            # remove_force(local_tmp_file)
            self.adb_shell(['rm', phone_tmp_file])

    def _screenshot_uiauto(self):
        tmp_file = tempfile.mktemp(prefix='atx-tmp-', suffix='.jpg')
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

        if filename:
            save_dir = os.path.dirname(filename) or '.'
            if not os.path.exists(save_dir):
                os.makedirs(save_dir)
            screen.save(filename)

        self.last_screenshot = screen
        return screen

    def adb_cmd(self, command):
        '''
        Run adb command, for example: adb(['pull', '/data/local/tmp/a.png'])

        Args:
            command: string or list of string

        Returns:
            command output
        '''
        cmds = ['adb']
        if self._serial:
            cmds.extend(['-s', self._serial])
        cmds.extend(['-H', self._host, '-P', str(self._port)])

        if isinstance(command, list) or isinstance(command, tuple):
            cmds.extend(list(command))
        else:
            cmds.append(command)
        # print cmds
        output = subprocess.check_output(cmds, stderr=subprocess.STDOUT)
        return output.replace('\r\n', '\n')

    def adb_shell(self, command):
        '''
        Run adb shell command

        Args:
            command: string or list of string

        Returns:
            command output
        '''
        if isinstance(command, list) or isinstance(command, tuple):
            return self.adb_cmd(['shell'] + list(command))
        else:
            return self.adb_cmd(['shell'] + [command])

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
            m = PROP_PATTERN.match(line)
            if m:
                props[m.group('key')] = m.group('value')
        return props

    def start_app(self, package_name):
        '''
        Start application

        Args:
            package_name: string like com.example.app1

        Returns:
            None
        '''
        self.adb_shell(['monkey', '-p', package_name, '-c', 'android.intent.category.LAUNCHER', '1'])
        return self

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

    def _escape_text(self, s):
        return s.replace(' ', '%s')

    def keyevent(self, keycode):
        """call adb shell input keyevent ${keycode}

        Args:
            - keycode(string): for example, KEYCODE_ENTER

        keycode need reference:
        http://developer.android.com/reference/android/view/KeyEvent.html
        """
        self.adb_shell(['input', 'keyevent', keycode])

    def type(self, text, enter=False):
        """Input some text, this method has been tested not very stable on some device.
        "Hi world" maybe spell into "H iworld"

        Args:
            - text: string (text to input)
            - enter(bool): input enter at last

        The android source code show that
        space need to change to %s
        insteresting thing is that if want to input %s, it is really unconvinent.
        android source code can be found here.
        https://android.googlesource.com/platform/frameworks/base/+/android-4.4.2_r1/cmds/input/src/com/android/commands/input/Input.java#159
        """
        first = True
        for s in text.split('%s'):
            if s == '':
                continue
            estext = self._escape_text(s)
            if first:
                first = False
            else:
                self.adb_shell(['input', 'text', '%'])
                estext = 's' + estext
            self.adb_shell(['input', 'text', estext])

        if enter:
            self.keyevent('KEYCODE_ENTER')
