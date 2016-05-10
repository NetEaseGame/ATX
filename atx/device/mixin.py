#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# License under MIT

from __future__ import absolute_import

import collections
import copy
import os
import re
import sys
import subprocess
import time
import tempfile
import warnings
import functools
import logging
import uuid
import inspect
import xml.dom.minidom

import cv2
import numpy as np
import aircv as ac
from uiautomator import AutomatorDeviceObject
from PIL import Image

from atx import consts
from atx import errors
from atx import patch
from atx import base
from atx import logutils
from atx import imutils
from atx import adb
from atx.device import Pattern, Bounds, FindPoint


__dir__ = os.path.dirname(os.path.abspath(__file__))
log = logutils.getLogger(__name__)

_Condition = collections.namedtuple('WatchCondition', ['pattern', 'exists'])

class WatcherItem(object):
    """
    How to use, for
    example:

    with d.watch('xx') as w:
        w.on('button.png').on('enter.png').click()
        w.on('yes.png').on_not('exit.png').click()

    or

    w = d.watch('yy')
    w.on('button.png').on('enter.png').click()
    w.on('button.png').click('enter.png')
    w.run()
    """
    def __init__(self, dev, done, handler, pattern):
        self._dev = dev
        self._done = done # list
        self._handler = handler
        self._hooks = handler['hooks'] = []
        self._conditions = handler['conditions'] = [_Condition(pattern, True)]

    def on(self, pattern):
        """Trigger when pattern exists"""
        self._conditions.append(_Condition(pattern, True))
        return self

    def on_not(self, pattern):
        """Trigger when pattern not exists"""
        self._conditions.append(_Condition(pattern, False))
        return self

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
        self._hooks.append(func)
        return self

    def click(self, *args, **kwargs):
        def _inner(event):
            if len(args) or len(kwargs):
                self._dev.click(*args, **kwargs)
            else:
                self._dev.click(*event.pos)
        return self.do(_inner)

    def click_image(self, *args, **kwargs):
        """ async trigger click_image """
        def _inner(event):
            return self._dev.click_image(*args, **kwargs)

        return self.do(_inner)

    def quit(self):
        def _inner(event):
            self._done[0] = True
            # raise RuntimeError("Not finished yet.")
        return self.do(_inner)

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

        self._wids = [] # store orders
        self._handlers = {}
        self._done = [False]

        self.name = name
        self.touched = {}
        self.timeout = timeout

    def on(self, pattern):
        # TODO(ssx): maybe an array is just enough
        watch_id = str(uuid.uuid1())
        self._wids.append(watch_id)
        handler = self._handlers[watch_id] = {}
        return WatcherItem(self._dev, self._done, handler, pattern)

    def _do_hook(self, screen):
        patterns = set()
        for handler in self._handlers.values():
            for c in handler['conditions']:
                patterns.add(c.pattern)

        # TODO(ssx): here can have a better optimized way.
        # no need to match all pattern all the time
        matches = {}
        for pattern in patterns:
            matches[pattern] = self._match(pattern, screen)

        for wid in self._wids:
            hdlr = self._handlers[wid]
            # pos = self._match(handler.pattern)
            # if pos is None:
            #     continue

            last_pos = None
            ok = True
            for c in hdlr['conditions']:
                last_pos = matches[c.pattern]
                exists = last_pos is not None
                if exists != c.exists:
                    ok = False
                    break
            if ok:
                for fn in hdlr['hooks']:
                    fn(Watcher.Event(None, last_pos))

    def run(self):
        # self._run = True
        start_time = time.time()
        while not self._done[0]:
            screen = self._dev.screenshot()
            self._do_hook(screen)

            if self.timeout is not None:
                if time.time() - start_time > self.timeout:
                    raise errors.WatchTimeoutError("Watcher(%s) timeout %s" % (self.name, self.timeout,))
                sys.stdout.write("Watching %4.1fs left: %4.1fs\r" %(self.timeout, self.timeout-time.time()+start_time))
                sys.stdout.flush()
            sys.stdout.write('\n')

    # def on_old(self, pattern=None, text=None):
    #     """Trigger when some object exists
    #     Args:
    #         image: image filename or Pattern
    #         text: For uiautomator

    #     Returns:
    #         None

    #     Raises:
    #         TypeError
    #     """
    #     if text:
    #         self._stored_selector = self._dev(text=text)
    #     elif pattern is not None:
    #         selector = self._dev.pattern_open(pattern)
    #         if selector is None:
    #             raise IOError("Not found pattern: {}".format(pattern))
    #         self._stored_selector = selector
    #     else:
    #         raise TypeError("unsupported type: %s", pattern)
            
    #     return self

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
        # print self._handlers
        # self._run_watch()
        self.run()

    def _match(self, selector, screen):
        ''' Find position for AtxPattern or UIAutomator Object

        Return:
            position(x, y) or None
        '''
        if isinstance(selector, Pattern) or isinstance(selector, basestring):
            ret = self._dev.match(selector, screen=screen)
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

    # def _hook(self, screen):
    #     for evt in self._events:
    #         pos = self._match(evt.selector, screen)
    #         if pos is None:
    #             continue

    #         if callable(evt.action):
    #             evt.action(Watcher.Event(evt.selector, pos))
    #         elif evt.action == Watcher.ACTION_CLICK:
    #             log.info('Watch match %s, click: %s', evt.selector, pos)
    #             self._dev.click(*pos)
    #         elif evt.action == Watcher.ACTION_QUIT:
    #             self._run = False

    # def _run_watch(self):
    #     self._run = True
    #     start_time = time.time()
        
    #     while self._run:
    #         screen = self._dev.screenshot()
    #         self._hook(screen)
    #         if self.timeout is not None:
    #             if time.time() - start_time > self.timeout:
    #                 raise errors.WatchTimeoutError("Watcher(%s) timeout %s" % (self.name, self.timeout,))
    #             sys.stdout.write("Watching %4.1fs left: %4.1fs\r" %(self.timeout, self.timeout-time.time()+start_time))
    #             sys.stdout.flush()
    #     sys.stdout.write('\n')


HookEvent = collections.namedtuple('HookEvent', ['flag', 'args', 'kwargs'])

def hook_wrap(event_type):
    def wrap(fn):
        @functools.wraps(fn)
        def _inner(*args, **kwargs):
            func_args = inspect.getcallargs(fn, *args, **kwargs)
            self = func_args.get('self')
            if self and hasattr(self, '_listeners'):
                for (f, event_flag) in self._listeners:
                    if event_flag & event_type:
                        f(HookEvent(event_flag, args[1:], kwargs)) # remove self from args
            return fn(*args, **kwargs)
        return _inner
    return wrap

class DeviceMixin(object):
    def __init__(self):
        self.image_match_method = consts.IMAGE_MATCH_METHOD_TMPL
        self.image_match_threshold = 0.8
        self._resolution = None
        self._bounds = None
        self._listeners = []
        self.image_path = ['.']

    @property
    def resolution(self):
        return self._resolution

    @resolution.setter
    def resolution(self, value):
        if value is None:
            self._resolution = None
        else:
            if not isinstance(value, tuple) or len(value) != 2:
                raise TypeError("Value should be tuple, contains two values")
            self._resolution = tuple(sorted(value))
    
    def pattern_open(self, image):
        if isinstance(image, Pattern):
            return image
        elif isinstance(image, basestring):
            image_path = base.search_image(image, self.image_path)
            if image_path is None:
                raise IOError('image file not found: {}'.format(image))
            return Pattern(image_path)
        elif 'numpy' in str(type(image)):
            return Pattern(image)
        else:
            raise TypeError("Not supported image type: {}".format(type(image)))

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

    def exists(self, pattern, screen=None):
        """Check if image exists in screen

        Returns:
            If exists, return FindPoint, or
            return None if result.confidence < self.image_match_threshold
        """
        ret = self.match(pattern, screen)
        if ret is None:
            return None
        if not ret.matched:
            return None
        return ret

    def wait(self, pattern, timeout=10.0):
        """Wait till pattern is found or time is out (default: 10s)."""
        t = time.time() + timeout
        while time.time() < t:
            ret = self.exists(pattern)
            if ret:
                return ret
            time.sleep(0.2)
        raise errors.ImageNotFoundError('Not found image %s' %(pattern,))

    def touch(self, x, y):
        """ Alias for click """
        self.click(x, y)

    def _cal_scale(self, pattern=None):
        scale = 1.0
        resolution = (pattern and pattern.resolution) or self.resolution
        if resolution is not None:
            ow, oh = sorted(resolution)
            dw, dh = sorted(self.display)
            fw, fh = 1.0*dw/ow, 1.0*dh/oh
            # For horizontal screen, scale by Y (width)
            # For vertical screen, scale by X (height)
            scale = fw if self.rotation in (1, 3) else fh
        return scale

    @property
    def bounds(self):
        if self._bounds is None:
            return None
        return self._bounds * self._cal_scale()
    
    def match(self, pattern, screen=None, threshold=None):
        """Check if image position in screen

        Args:
            - pattern: Image file name or opencv image object
            - screen: opencv image, optional, if not None, screenshot method will be called

        Returns:
            None or FindPoint, For example:

            FindPoint(pos=(20, 30), method='tmpl', confidence=0.801, matched=True)

            Only when confidence > self.image_match_threshold, matched will be True

        Raises:
            TypeError: when image_match_method is invalid
        """
        pattern = self.pattern_open(pattern)
        search_img = pattern.image

        pattern_scale = self._cal_scale(pattern)
        if pattern_scale != 1.0:
            search_img = cv2.resize(search_img, (0, 0), 
                fx=pattern_scale, fy=pattern_scale,
                interpolation=cv2.INTER_CUBIC)
        
        screen = screen or self.region_screenshot()
        threshold = threshold or self.image_match_threshold

        dx, dy = pattern.offset
        dx, dy = int(dx*pattern_scale), int(dy*pattern_scale)

        # image match
        screen = imutils.from_pillow(screen) # convert to opencv image
        match_method = self.image_match_method
        ret = None
        if match_method == consts.IMAGE_MATCH_METHOD_TMPL:
            ret = ac.find_template(screen, search_img)
        elif match_method == consts.IMAGE_MATCH_METHOD_SIFT:
            ret = ac.find_sift(screen, search_img, min_match_count=10)
        else:
            raise TypeError("Invalid image match method: %s" %(match_method,))

        if ret is None:
            return None
        (x, y) = ret['result']
        # fix by offset
        position = (x+dx, y+dy)
        if self.bounds:
            x, y = position
            position = (x+self.bounds.left, y+self.bounds.top)
        confidence = ret['confidence']

        matched = True
        if match_method == consts.IMAGE_MATCH_METHOD_TMPL:
            if confidence < threshold:
                matched = False
        elif match_method == consts.IMAGE_MATCH_METHOD_SIFT:
            matches, total = confidence
            if 1.0*matches/total > 0.5: # FIXME(ssx): sift just write here
                matched = True
        return FindPoint(position, confidence, match_method, matched=matched)

    def region(self, bounds):
        """Set region of the screen area
        Args:
            bounds: Bounds object

        Returns:
            A new AndroidDevice object

        Raises:
            TypeError
        """
        if not isinstance(bounds, Bounds):
            raise TypeError("region param bounds must be isinstance of Bounds")
        _d = copy.copy(self)
        _d._bounds = bounds
        return _d

    def region_screenshot(self, filename=None):
        if self._bounds is None:
            return self.screenshot(filename)
        screen = self.screenshot()
        screen_crop = screen.crop(self.bounds)
        if filename:
            screen_crop.save(filename)
        return screen_crop

    def touch_image(self, *args, **kwargs):
        """ALias for click_image"""
        self.click_image(*args, **kwargs)

    def add_listener(self, fn, event_flags):
        """Listen event
        Args:
            - fn: function call when event happends
            - event_flags: for example
                EVENT_UIAUTO_CLICK | EVENT_UIAUTO_SWIPE

        Returns:
            None
        """
        self._listeners.append((fn, event_flags))

    def _trigger_event(self, event_flag, event):
        for (fn, flag) in self._listeners:
            if flag & event_flag:
                fn(event)

    def assert_exists(self, pattern, timeout=20.0):
        """Assert if image exists
        Args:
            - image: image filename # not support pattern for now
            - timeout (float): seconds

        Returns:
            self

        Raises:
            AssertExistsError
        """
        pattern = self.pattern_open(pattern)
        search_img = pattern.image
        # search_img = imutils.open(image)
        log.info('assert exists image: %s', pattern)
        start_time = time.time()
        while time.time() - start_time < timeout:
            point = self.match(search_img)
            if point is None:
                sys.stdout.write('.')
                sys.stdout.flush()
                continue
            if not point.matched:
                log.debug('Ignore confidence: %s', point.confidence)
                continue
            log.debug('assert pass, confidence: %s', point.confidence)
            sys.stdout.write('\n')
            break
        else:
            sys.stdout.write('\n')
            raise errors.AssertExistsError('image not found %s' %(pattern,))

    @hook_wrap(consts.EVENT_CLICK_IMAGE)
    def click_image(self, pattern, timeout=20.0, wait_change=False):
        """Simulate click according image position

        Args:
            - pattern (str or Pattern): filename or an opencv image object.
            - timeout (float): if image not found during this time, ImageNotFoundError will raise.
            - wait_change (bool): wait until background image changed.

        Returns:
            None

        Raises:
            ImageNotFoundError: An error occured when img not found in current screen.
        """
        pattern = self.pattern_open(pattern)
        log.info('click image: %s', pattern)
        start_time = time.time()
        found = False
        while time.time() - start_time < timeout:
            point = self.match(pattern)
            if point is None:
                sys.stdout.write('.')
                sys.stdout.flush()
                continue
            if not point.matched:
                log.info('Ignore confidence: %s', point.confidence)
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
                ret = self.match(pattern)
                if ret is None:
                    break
        if not found:
            raise errors.ImageNotFoundError('Not found image %s' %(pattern,))

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

if __name__ == '__main__':
    b = Bounds(1, 2, 3, 4)
    print b
    print b * 1.0