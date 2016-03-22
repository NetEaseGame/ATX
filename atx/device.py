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

import cv2
import numpy as np
import aircv as ac
from uiautomator import device as d
from uiautomator import Device as UiaDevice
from uiautomator import AutomatorDeviceObject
from PIL import Image

from atx import consts
from atx import errors
from atx import patch
from atx import base
from atx import logutils
from atx import imutils
from atx import adb


log = logutils.getLogger('atx')
log.setLevel(logging.INFO)

FindPoint = collections.namedtuple('FindPoint', ['pos', 'confidence', 'method', 'matched'])

__dir__ = os.path.dirname(os.path.abspath(__file__))
__boundstuple = collections.namedtuple('Bounds', ['left', 'top', 'right', 'bottom'])

class Bounds(__boundstuple):
    def __init__(self, *args, **kwargs):
        super(Bounds, self).__init__(*args, **kwargs)
        self._area = None

    def is_inside(self, x, y):
        v = self
        return x > v.left and x < v.right and y > v.top and y < v.bottom

    @property
    def area(self):
        if not self._area:
            v = self
            self._area = (v.right-v.left) * (v.bottom-v.top)
        return self._area

    @property
    def center(self):
        v = self
        return (v.left+v.right)/2, (v.top+v.bottom)/2


class Pattern(object):
    def __init__(self, image, offset=(0, 0), anchor=0, rsl=None, resolution=None):
        """
        Args:
            image: image filename or image URL
            offset: offset of image center
            anchor: not supported
            resolution: image origin screen resolution
            rsl: alias of resolution
        """
        self._name = None
        self._image = imutils.open(image)
        self._offset = offset
        self._resolution = rsl or resolution
        
        if isinstance(image, basestring):
            self._name = image

    def __str__(self):
        return 'Pattern(name: {}, offset: {})'.format(self._name, self.offset)
    
    @property
    def image(self):
        return self._image

    @property
    def offset(self):
        return self._offset

    @property
    def resolution(self):
        return self._resolution
    
    
class Watcher(object):
    ACTION_CLICK = 1 <<0
    ACTION_TOUCH = 1 <<0
    ACTION_QUIT = 1 <<1

    Handler = collections.namedtuple('Handler', ['selector', 'action'])
    Event = collections.namedtuple('Event', ['selector', 'pos'])

    def __init__(self, device, name=None, timeout=None):
        self._events = []
        self._dev = device
        self._run = False
        self._stored_selector = None

        self.name = name
        self.touched = {}
        self.timeout = timeout

    def on(self, image=None, text=None):
        """Trigger when some object exists
        Args:
            image: image filename or Pattern
            text: For uiautomator

        Returns:
            None
        """
        if isinstance(image, basestring):
            self._stored_selector = Pattern(image)
        elif isinstance(image, Pattern):
            self._stored_selector = image
        elif text:
            self._stored_selector = self._dev(text=text)
        else:
            raise SyntaxError("unsupported type: %s", image)
            
        return self

    def touch(self):
        return self.click()

    def click(self):
        """Touch"""
        self._events.append(Watcher.Handler(self._stored_selector, Watcher.ACTION_CLICK))
        return self

    def quit(self):
        self._events.append(Watcher.Handler(self._stored_selector, Watcher.ACTION_QUIT))

    def do(self, func):
        """Trigger with function call
        Args:
            func: function which will called when object found. For example.

            def foo(event):
                print event.pos # (x, y) position
            
            w.on('kitty.png').do(foo)
        
        Returns:
            Watcher object

        Raises:
            SyntaxError
        """
        if not callable(func):
            raise SyntaxError("%s should be a function" % func)
        self._events.append(Watcher.Handler(self._stored_selector, func))
        return self

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        self._run_watch()

    def _match(self, selector, screen):
        ''' returns position(x, y) or None'''
        if isinstance(selector, Pattern):
            ret = self._dev.exists(selector.image, screen=screen)
            log.debug('watch match: %s, confidence: %s', selector, ret)
            if ret is None:
                return None
            return ret.pos
        elif isinstance(selector, AutomatorDeviceObject):
            if not selector.exists:
                return None
            info = selector.info['bounds']
            x = (info['left'] + info['right']) / 2
            y = (info['bottom'] + info['top']) / 2
            return (x, y)

    def _hook(self, screen):
        for evt in self._events:
            pos = self._match(evt.selector, screen)
            if pos is None:
                continue

            if callable(evt.action):
                evt.action(Watcher.Event(evt.selector, pos))
            elif evt.action == Watcher.ACTION_CLICK:
                log.info('trigger watch click: %s', pos)
                self._dev.click(*pos)
            elif evt.action == Watcher.ACTION_QUIT:
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
                sys.stdout.write("Watching %4.1fs left: %4.1fs\r" %(self.timeout, self.timeout-time.time()+start_time))
                sys.stdout.flush()
        sys.stdout.write('\n')


class DeviceMixin(object):
    def __init__(self):
        self.image_match_method = consts.IMAGE_MATCH_METHOD_TMPL
        self.resolution = None
        self.image_match_threshold = 0.8
        self._bounds = None
        self._event_handlers = []

    def delay(self, secs):
        """Delay some seconds
        Args:
            secs: float seconds

        Returns:
            self
        """
        secs = int(secs)
        for i in reversed(range(secs)):
            sys.stdout.write('\r')
            sys.stdout.write("sleep %ds, left %2ds" % (secs, i+1))
            sys.stdout.flush()
            time.sleep(1)
        sys.stdout.write("\n")
        return self

    def exists(self, img, screen=None):
        """Check if image exists in screen

        Returns:
            If exists, return FindPoint, or
            return None if result.confidence < self.image_match_threshold
        """
        ret = self.match(img, screen)
        if ret is None:
            return None
        if not ret.matched:
            return None
        return ret

    def touch(self, x, y):
        """ Alias for click """
        self.click(x, y)

    def match(self, pattern, screen=None, threshold=None):
        """Check if image position in screen

        Args:
            pattern: Image file name or opencv image object
            screen: opencv image, optional, if not None, screenshot method will be called

        Returns:
            None or FindPoint, For example:

            FindPoint(pos=(20, 30), method='tmpl', confidence=0.801, matched=True)

            Only when confidence > self.image_match_threshold, matched will be True

        Raises:
            SyntaxError: when image_match_method is invalid
        """
        if not isinstance(pattern, Pattern):
            pattern = Pattern(pattern)
        search_img = pattern.image
        if screen is None:
            screen = self.screenshot()
        if threshold is None:
            threshold = self.image_match_threshold

        dx, dy = pattern.offset
        # image match
        screen = imutils.from_pillow(screen) # convert to opencv image
        if self.image_match_method == consts.IMAGE_MATCH_METHOD_TMPL:
            resolution = pattern.resolution or self.resolution
            if resolution is not None:
                ow, oh = resolution
                fx, fy = 1.0*self.display.width/ow, 1.0*self.display.height/oh
                # For horizontal screen, scale by Y
                # For vertical screen, scale by X
                # Offset scale by X and Y
                # FIXME(ssx): need test here, I never tried before.
                scale = fy if self.rotation in (1, 3) else fx
                search_img = cv2.resize(search_img, (0, 0), fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)
                dx, dy = int(dx*scale), int(dy*scale)

            ret = ac.find_template(screen, search_img)
        elif self.image_match_method == consts.IMAGE_MATCH_METHOD_SIFT:
            ret = ac.find_sift(screen, search_img, min_match_count=10)
        else:
            raise SyntaxError("Invalid image match method: %s" %(self.image_match_method,))

        if ret is None:
            return None
        (x, y) = ret['result']
        # fix by offset
        position = (x+dx, y+dy)
        confidence = ret['confidence']

        matched = True
        if self.image_match_method == consts.IMAGE_MATCH_METHOD_TMPL:
            if confidence < self.image_match_threshold:
                matched = False
        elif self.image_match_method == consts.IMAGE_MATCH_METHOD_SIFT:
            matches, total = confidence
            if 1.0*matches/total > 0.5: # FIXME(ssx): sift just write here
                matched = True
        return FindPoint(position, confidence, self.image_match_method, matched=matched)

    def region(self):
        """TODO"""
        return self

    def touch_image(self, *args, **kwargs):
        """ALias for click_image"""
        self.click_image(*args, **kwargs)

    def add_listener(self, fn, event_flags):
        """Listen event
        Args:
            fn: function call when event happends
            event_flags: for example
                EVENT_UIAUTO_CLICK | EVENT_UIAUTO_SWIPE

        Returns:
            None
        """
        self._event_handlers.append((fn, event_flags))

    def _trigger_event(self, event_flag, event):
        for (fn, flag) in self._event_handlers:
            if flag & event_flag:
                fn(event)

    def click_image(self, img, timeout=20.0, wait_change=False):
        """Simulate click according image position

        Args:
            img: filename or an opencv image object
            timeout: float, if image not found during this time, ImageNotFoundError will raise.
            wait_change: wait until background image changed.
        Returns:
            None

        Raises:
            ImageNotFoundError: An error occured when img not found in current screen.
        """
        search_img = imutils.open(img)
        log.info('click image: %s', img)
        start_time = time.time()
        found = False
        while time.time() - start_time < timeout:
            point = self.match(search_img)
            if point is None:
                sys.stdout.write('.')
                sys.stdout.flush()
                continue
            if not point.matched:
                log.debug('Ignore confidence: %s', point.confidence)
                continue
            log.debug('confidence: %s', point.confidence)
            self.touch(*point.pos)
            self._trigger_event(consts.EVENT_UIAUTO_CLICK, point)
            found = True
            break
        sys.stdout.write('\n')

        # wait until click area not same
        if found and wait_change:
            start_time = time.time()
            while time.time()-start_time < timeout:
                # screen_img = self.screenshot()
                ret = self.match(search_img)
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