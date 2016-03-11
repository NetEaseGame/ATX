#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# License under MIT

import collections
import json
import os
import platform
import re
import sys
import subprocess
import time
import threading
import warnings
import logging

import cv2
import numpy as np
import aircv as ac
from uiautomator import device as d
from uiautomator import Device as UiaDevice
from PIL import Image

from atx import consts
from atx import errors
from atx import patch
from atx import logutils


log = logutils.getLogger(__name__)
log.setLevel(logging.DEBUG)
FindPoint = collections.namedtuple('FindPoint', ['pos', 'confidence', 'method'])

__dir__ = os.path.dirname(os.path.abspath(__file__))
__tmp__ = os.path.join(__dir__, '__cache__')

DISPLAY_RE = re.compile(
    '.*DisplayViewport{valid=true, .*orientation=(?P<orientation>\d+), .*deviceWidth=(?P<width>\d+), deviceHeight=(?P<height>\d+).*')

class Watcher(object):
    ACTION_TOUCH = 1 <<0
    ACTION_QUIT = 1 <<1

    def __init__(self, device, name=None, timeout=None):
        self._events = {}
        self._dev = device
        self._run = False
        self.name = name
        self.touched = {}
        self.timeout = timeout

    def on(self, image, flags):
        """Trigger when some object exists
        Args:
            image: string location of an image
            flags: ACTION_TOUCH | ACTION_QUIT

        Returns:
            None
        """
        self._events[image] = flags

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        self._run_watch()

    def _hook(self, screen):
        for (img, flags) in self._events.items():
            ret = self._dev.exists(img, screen=screen)
            if ret is None:
                continue

            # FIXME(ssx): Image match confidence should can set
            exists = False
            if ret.method == consts.IMAGE_MATCH_METHOD_TMPL:
                if ret.confidence > 0.8:
                    exists = True
                # else:
                    # print("Skip confidence:", ret.confidence)
            elif ret.method == consts.IMAGE_MATCH_METHOD_SIFT:
                matches, total = ret.confidence
                if 1.0*matches/total > 0.5:
                    exists = True

            if exists:
                if flags & Watcher.ACTION_TOUCH:
                    log.debug('trigger watch click: %s', ret.pos)
                    self._dev.click(*ret.pos)
                    self.touched[img] = True

                if flags & Watcher.ACTION_QUIT:
                    self._run = False

    def _run_watch(self):
        self._run = True
        start_time = time.time()
        
        while self._run:
            screen = self._dev.screenshot()
            self._hook(screen)
            if self.timeout is not None:
                if time.time() - start_time > self.timeout:
                    raise errors.WatchTimeoutError("Watcher(%s) timeout %s" % (self.name, self.timeout,))
                sys.stdout.write("\rWatching %4.1fs left: %4.1fs\r" %(self.timeout, self.timeout-time.time()+start_time))
                sys.stdout.flush()
        sys.stdout.write('\n')


class CommonWrap(object):
    def __init__(self):
        self.image_match_method = consts.IMAGE_MATCH_METHOD_TMPL
        self.resolution = None

    def _read_img(self, img):
        if isinstance(img, basestring):
            return ac.imread(img)
        # FIXME(ssx): need support other types
        return img

    def sleep(self, secs):
        secs = int(secs)
        for i in reversed(range(secs)):
            sys.stdout.write('\r')
            sys.stdout.write("sleep %ds, left %2ds" % (secs, i+1))
            sys.stdout.flush()
            time.sleep(1)
        sys.stdout.write("\n")

    def exists(self, img, screen=None):
        """Check if image exists

        Args:
            img: string or opencv image
            screen: opencv image, optional, if not None, screenshot will be called

        Returns:
            None or FindPoint

        Raises:
            SyntaxError: when image_match_method is invalid
        """
        search_img = self._read_img(img)
        if screen is None:
            screen = self.screenshot()

        # image match
        screen = pil_to_opencv(screen) # convert to opencv image
        if self.image_match_method == consts.IMAGE_MATCH_METHOD_TMPL:
            if self.resolution is not None:
                ow, oh = self.resolution
                fx, fy = 1.0*self.display.width/ow, 1.0*self.display.height/oh
                search_img = cv2.resize(search_img, (0, 0), fx=fx, fy=fy, interpolation=cv2.INTER_CUBIC)
                # TODO(useless)
                # cv2.imwrite('resize-tmp.png', search_img)
                # cv2.imwrite('current-screen.png', screen)
            ret = ac.find_template(screen, search_img)
        elif self.image_match_method == consts.IMAGE_MATCH_METHOD_SIFT:
            ret = ac.find_sift(screen, search_img, min_match_count=10)
        else:
            raise SyntaxError("Invalid image match method: %s" %(self.image_match_method,))

        if ret is None:
            return None
        position = ret['result']
        confidence = ret['confidence']
        log.info('match confidence: %s', confidence)
        return FindPoint(position, confidence, self.image_match_method)

    def touch_image(self, img, timeout=20.0, wait_change=False):
        """Simulate touch according image position

        Args:
            img: filename or an opencv image object
            timeout: float, if image not found during this time, ImageNotFoundError will raise.
            wait_change: wait until background image changed.
        Returns:
            None

        Raises:
            ImageNotFoundError: An error occured when img not found in current screen.
        """
        search_img = self._read_img(img)
        log.info('touch image: %s', img)
        start_time = time.time()
        found = False
        while time.time() - start_time < timeout:
            point = self.exists(search_img)
            if point is None:
                sys.stdout.write('.')
                sys.stdout.flush()
                continue
            self._uiauto.click(*point.pos)
            found = True
            break
        sys.stdout.write('\n')

        # wait until click area not same
        if found and wait_change:
            start_time = time.time()
            while time.time()-start_time < timeout:
                screen_img = self.screenshot()
                ret = ac.find_template(screen_img, search_img)
                if ret is None:
                    break

        if not found:
            raise errors.ImageNotFoundError('Not found image %s' %(img,))

    def watch(self, name, timeout=None):
        """Return a new watcher
        Args:
            name: string watcher name
            timeout: watch timeout

        Returns:
            watcher object
        """
        w = Watcher(self, name, timeout)
        w._dev = self
        return w


def pil_to_opencv(pil_image):
    # convert PIL to OpenCV
    pil_image = pil_image.convert('RGB')
    cv2_image = np.array(pil_image)
    # Convert RGB to BGR 
    cv2_image = cv2_image[:, :, ::-1].copy()
    return cv2_image


class AndroidDevice(CommonWrap, UiaDevice):
    def __init__(self, serialno=None, **kwargs):
        self._host = kwargs.get('host', '127.0.0.1')
        self._port = kwargs.get('port', 5037)

        kwargs['adb_server_host'] = kwargs.pop('host', self._host)
        kwargs['adb_server_port'] = kwargs.pop('port', self._port)
        UiaDevice.__init__(self, serialno, **kwargs)
        CommonWrap.__init__(self)

        self._serial = serialno
        self._uiauto = super(AndroidDevice, self)
        self._minicap_params = None
        self.minicap_rotation = None
        self._watchers = {}

        self.screenshot_method = consts.SCREENSHOT_METHOD_UIAUTOMATOR
        # self._tmpdir = 'tmp'
        # self._click_timeout = 20.0 # if icon not found in this time, then panic
        # self._delay_after_click = 0.5 # when finished click, wait time
        # self._screen_resolution = None

        # self._snapshot_file = None
        # self._keep_capture = False # for func:keepScreen,releaseScreen
        # # self._logfile = logfile
        # self._loglock = threading.Lock()
        # self._operation_mark = False

        # # if self._logfile:
        # #     logdir = os.path.dirname(logfile) or '.'
        # #     if not os.path.exists(logdir):
        # #         os.makedirs(logdir)
        # #     if os.path.exists(logfile):
        # #         backfile = logfile+'.'+time.strftime('%Y%m%d%H%M%S')
        # #         os.rename(logfile, backfile)

        # # Only for android phone method=<adb|screencap>
        # def _snapshot_method(method):
        #     if method and self._devtype == 'android':
        #         self.dev._snapshot_method = method

        # self._snapshot_method = _snapshot_method
        #-- end of func setting

    def _tmp_filename(self, prefix='tmp-', ext='.png'):
        return '%s%s%s' %(prefix, time.time(), ext)

    @property
    def wlan_ip(self):
        return self.adb_shell(['getprop', 'dhcp.wlan0.ipaddress']).strip()

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

        w, h = d.info['displayWidth'], d.info['displayHeight']
        w, h = min(w, h), max(w, h)
        return collections.namedtuple('Display', ['width', 'height'])(w, h)
            
    def _get_minicap_params(self):
        """
        Used about 0.1s
        uiautomator d.info is now well working with device which has virtual menu.
        """
        rotation = self.minicap_rotation 
        if self.minicap_rotation is None:
            rotation = d.info['displayRotation']

        # rotation not working on SumSUNG 9502
        return '{x}x{y}@{x}x{y}/{r}'.format(
            x=self.display.width,
            y=self.display.height,
            r=rotation*90)
        
    def _minicap(self):
        phone_tmp_file = '/data/local/tmp/'+self._tmp_filename(ext='.jpg')
        local_tmp_file = os.path.join(__tmp__, self._tmp_filename(ext='.jpg'))
        command = 'LD_LIBRARY_PATH=/data/local/tmp /data/local/tmp/minicap -P {} -s > {}'.format(
            self._get_minicap_params(), phone_tmp_file)
        self.adb_shell(command)
        self.adbrun(['pull', phone_tmp_file, local_tmp_file])
        self.adb_shell(['rm', phone_tmp_file])

        pil_image = Image.open(local_tmp_file)
        os.remove(local_tmp_file)

        # Fix rotation not rotate right.
        (img_w, img_h) = pil_image.size
        if self.minicap_rotation in [1, 3] and img_w < img_h:
            pil_image = pil_image.rotate(90, Image.BILINEAR, expand=True)
        return pil_image

    def screenshot(self, filename=None):
        """
        Take screen snapshot

        Args:
            filename: filename where save to, optional

        Returns:
            PIL.Image object

        Raises:
            TypeError
        """
        screen = None
        if self.screenshot_method == consts.SCREENSHOT_METHOD_UIAUTOMATOR:
            tmp_file = os.path.join(__tmp__, self._tmp_filename())
            screen = Image.open(tmp_file)
            os.remove(tmp_file)
        elif self.screenshot_method == consts.SCREENSHOT_METHOD_MINICAP:
            screen = self._minicap()
        else:
            raise TypeError('Invalid screenshot_method')

        if filename:
            save_dir = os.path.dirname(filename) or '.'
            if not os.path.exists(save_dir):
                os.makedirs(save_dir)
            screen.save(filename)

        return screen

    def adbrun(self, command):
        '''
        Run adb command, for example: adbrun(['pull', '/data/local/tmp/a.png'])

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
            return self.adbrun(['shell'] + list(command))
        else:
            return self.adbrun(['shell'] + [command])

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

    # def safe_wait(self, img, seconds=20.0):
    #     '''
    #     Like wait, but don't raise RuntimeError

    #     return None when timeout
    #     return point if found
    #     '''
    #     warnings.warn("deprecated, use safe_wait instead", DeprecationWarning)
    #     try:
    #         return self.wait(img, seconds)
    #     except:
    #         return None        

    # def center(self):
    #     '''
    #     Center position
    #     '''
    #     w, h = self.shape()
    #     return w/2, h/2

    # def drag(self, fpt, tpt, duration=0.5):
    #     ''' 
    #     Drag from one place to another place

    #     @param fpt,tpt: filename or position
    #     @param duration: float (duration of the event in seconds)
    #     '''
    #     fpt = self._val_to_point(fpt)
    #     tpt = self._val_to_point(tpt)
    #     return self.dev.drag(fpt, tpt, duration)

    # def type(self, text):
    #     '''
    #     Input some text

    #     @param text: string (text want to type)
    #     '''
    #     self.dev.type(text)

    # def keyevent(self, event):
    #     '''
    #     Send keyevent (only support android and ios)

    #     @param event: string (one of MENU,BACK,HOME)
    #     @return nothing
    #     '''
    #     if hasattr(self.dev, 'keyevent'):
    #         return self.dev.keyevent(event)
    #     raise RuntimeError('keyevent not support')
