#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# License under MIT

from __future__ import absolute_import

import collections
import copy
import functools
import inspect
import os
import sys
import time
import traceback
import warnings

import cv2
import aircv as ac
from uiautomator import AutomatorDeviceObject

from atx import base
from atx import consts
from atx import errors
from atx import imutils
from atx import logutils
from atx.base import nameddict
from atx.drivers import Pattern, Bounds, FindPoint


warnings.simplefilter('default')

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

    # blueprint upgrade plan
    - conditions
        pattern
    - hooks
        functions
    """
    def __init__(self, watcher, rule):
        self._w = watcher
        self._r = rule

    def on(self, pattern):
        """Trigger when pattern exists"""
        self._r['conditions'].append(_Condition(pattern, True))
        return self

    # def on_not(self, pattern):
    #     """Trigger when pattern not exists"""
    #     self._conditions.append(_Condition(pattern, False))
    #     return self

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
        self._r['actions'].append(func)
        return self

    def click(self, *args, **kwargs):
        def _inner(event):
            if len(args) or len(kwargs):
                self._w._dev.click(*args, **kwargs)
            else:
                self._w._dev.click(*event.pos)
        return self.do(_inner)

    def click_image(self, *args, **kwargs):
        """ async trigger click_image """
        def _inner(event):
            return self._w._dev.click_image(*args, **kwargs)

        return self.do(_inner)

    def quit(self):
        def _inner(event):
            self._w._done = True
        return self.do(_inner)

class Watcher(object):
    Handler = collections.namedtuple('Handler', ['selector', 'action'])
    Event = collections.namedtuple('Event', ['selector', 'pos'])

    def __init__(self, device, name=None, timeout=None, raise_errors=True):
        self.name = name
        self.timeout = timeout
        self.raise_errors = raise_errors
        
        self._dev = device
        self._done = False
        self._watches = []

    def on(self, pattern):
        w = dict(
            conditions=[_Condition(pattern, True)],
            actions=[],
        )
        self._watches.append(w)
        return WatcherItem(self, w)

    def on_ui(self, text):
        w = dict(
            conditions=[_Condition(self._dev(text=text), True)],
            actions=[],
        )
        self._watches.append(w)
        return WatcherItem(self, w)

    def _do_hook(self, screen):
        # patterns = set()
        for rule in self._watches:
            conditions = rule['conditions']
            actions = rule['actions']

            if not actions:
                continue

            ok = True
            last_pos = None
            for condition in conditions:
                pos = self._match(condition.pattern, screen)
                if pos:
                    log.info("watch match: %s", condition)
                if bool(pos) != condition.exists:
                    ok = False
                    break
                if condition.exists:
                    last_pos = pos
            if ok:
                for fn in actions:
                    fn(self.Event(None, last_pos))
                break # FIXME(ssx): maybe need fallthrough, but for now, just simplfy it

    def run(self):
        # self._run = True
        start_time = time.time()
        while not self._done:
            screen = self._dev.screenshot()
            self._do_hook(screen)

            if self.timeout is not None:
                if time.time() - start_time > self.timeout:
                    if self.raise_errors:
                        raise errors.WatchTimeoutError("[%s] watch timeout %s" % (self.name, self.timeout,))
                    break
                sys.stdout.write("[%s] watching %4.1fs left: %4.1fs\r" %(self.name, self.timeout, self.timeout-time.time()+start_time))
                sys.stdout.flush()
        sys.stdout.write('\n')

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        self.run()

    def _match(self, selector, screen):
        ''' Find position for AtxPattern or UIAutomator Object

        Return:
            position(x, y) or None
        '''
        if isinstance(selector, Pattern) or isinstance(selector, basestring):
            ret = self._dev.match(selector, screen=screen)
            if ret is None:
                return
            log.debug('watch match: %s, confidence: %s', selector, ret)
            if not ret.matched:
                return
            return ret.pos
        elif isinstance(selector, AutomatorDeviceObject):
            if not selector.exists:
                return None
            info = selector.info['bounds']
            x = (info['left'] + info['right']) / 2
            y = (info['bottom'] + info['top']) / 2
            return (x, y)


Traceback = collections.namedtuple('Traceback', ['stack', 'exception'])
HookEvent = nameddict('HookEvent', ['flag', 'args', 'kwargs', 'retval', 'traceback', 'depth', 'is_before'])

def hook_wrap(event_type):
    def wrap(fn):
        @functools.wraps(fn)
        def _inner(*args, **kwargs):
            func_args = inspect.getcallargs(fn, *args, **kwargs)
            self = func_args.get('self')
            self._depth += 1

            def trigger(event):
                for (f, event_flag) in self._listeners:
                    if event_flag & event_type:
                        event.args = args[1:]
                        event.kwargs = kwargs
                        event.flag = event_type
                        event.depth = self._depth
                        f(event)
            
            _traceback = None
            _retval = None
            try:
                trigger(HookEvent(is_before=True))
                _retval = fn(*args, **kwargs)
                return _retval
            except Exception as e:
                _traceback = Traceback(traceback.format_exc(), e)
                raise
            finally:
                trigger(HookEvent(is_before=False, retval=_retval, traceback=_traceback))
                self._depth -= 1
        return _inner
    return wrap

class DeviceMixin(object):
    def __init__(self):
        self.image_match_method = consts.IMAGE_MATCH_METHOD_TMPL
        self.image_match_threshold = 0.8
        self._resolution = None
        self._bounds = None
        self._listeners = []
        self._depth = 0 # used for hook_wrap
        self.image_path = ['.']
        self.__last_screen = None
        self.__keep_screen = False

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
    
    def _search_image(self, name, raise_error=True):
        image_path = base.search_image(name, self.image_path)
        if raise_error and image_path is None:
            raise IOError('image file not found: {}'.format(name))
        return image_path

    def pattern_open(self, image):
        if isinstance(image, Pattern):
            if image._image is None:
                image_path = self._search_image(image._name)
                image._image = imutils.open(image_path)
            return image
        elif isinstance(image, basestring):
            image_path = base.search_image(image, self.image_path)
            if image_path is None:
                raise IOError('image file not found: {}'.format(image))
            return Pattern(image_path, image=imutils.open(image_path))
        elif 'numpy' in str(type(image)):
            return Pattern('unknown', image=image)
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

    def exists(self, pattern, **match_kwargs):
        """Check if image exists in screen

        Returns:
            If exists, return FindPoint, or
            return None if result.confidence < self.image_match_threshold
        """
        ret = self.match(pattern, **match_kwargs)
        if ret is None:
            return None
        if not ret.matched:
            return None
        return ret

    def wait(self, pattern, timeout=10.0, safe=False, **match_kwargs):
        """Wait till pattern is found or time is out (default: 10s)."""
        t = time.time() + timeout
        while time.time() < t:
            ret = self.exists(pattern, **match_kwargs)
            if ret:
                return ret
            time.sleep(0.2)
        if not safe:
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
    
    def _match_auto(self, screen, search_img, threshold):
        """Maybe not a good idea
        """
        # 1. try template first
        ret = ac.find_template(screen, search_img)
        if ret and ret['confidence'] > threshold:
            return FindPoint(ret['result'], ret['confidence'], consts.IMAGE_MATCH_METHOD_TMPL, matched=True)

        # 2. try sift
        ret = ac.find_sift(screen, search_img, min_match_count=10)
        if ret is None:
            return None

        matches, total = ret['confidence']
        if 1.0*matches/total > 0.5: # FIXME(ssx): sift just write here
            return FindPoint(ret['result'], ret['confidence'], consts.IMAGE_MATCH_METHOD_SIFT, matched=True)
        return None

    def match(self, pattern, screen=None, rect=None, offset=None, threshold=None, method=None):
        """Check if image position in screen

        Args:
            - pattern: Image file name or opencv image object
            - screen (PIL.Image): optional, if not None, screenshot method will be called
            - threshold (float): it depends on the image match method
            - method (string): choices on <template | sift>

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
        threshold = threshold or pattern.threshold or self.image_match_threshold

        # handle offset if percent, ex (0.2, 0.8)
        dx, dy = offset or pattern.offset or (0, 0)
        dx = pattern.image.shape[1] * dx # opencv object width
        dy = pattern.image.shape[0] * dy # opencv object height
        dx, dy = int(dx*pattern_scale), int(dy*pattern_scale)

        # image match
        screen = imutils.from_pillow(screen) # convert to opencv image
        if rect and isinstance(rect, tuple) and len(rect) == 4:
            (x0, y0, x1, y1) = [v*pattern_scale for v in rect]
            (dx, dy) = dx+x0, dy+y0
            screen = imutils.crop(screen, x0, y0, x1, y1)
            #cv2.imwrite('cc.png', screen)

        match_method = method or self.image_match_method
        
        ret = None
        confidence = None
        matched = False
        position = None
        if match_method == consts.IMAGE_MATCH_METHOD_TMPL: #IMG_METHOD_TMPL
            ret = ac.find_template(screen, search_img)
            if ret is None:
                return None
            confidence = ret['confidence']
            if confidence > threshold:
                matched = True
            (x, y) = ret['result']
            position = (x+dx, y+dy) # fix by offset
        elif match_method == consts.IMAGE_MATCH_METHOD_SIFT:
            ret = ac.find_sift(screen, search_img, min_match_count=10)
            if ret is None:
                return None
            confidence = ret['confidence']
            matches, total = confidence
            if 1.0*matches/total > 0.5: # FIXME(ssx): sift just write here
                matched = True
            (x, y) = ret['result']
            position = (x+dx, y+dy) # fix by offset
        elif match_method == consts.IMAGE_MATCH_METHOD_AUTO:
            fp = self._match_auto(screen, search_img, threshold)
            if fp is None:
                return None
            (x, y) = fp.pos
            position = (x+dx, y+dy)
            return FindPoint(position, fp.confidence, fp.method, fp.matched)
        else:
            raise TypeError("Invalid image match method: %s" %(match_method,))

        (x, y) = ret['result']
        position = (x+dx, y+dy) # fix by offset
        if self.bounds:
            x, y = position
            position = (x+self.bounds.left, y+self.bounds.top)

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

    def keep_screen(self):
        """
        Freese screenshot, so all image functions will not take images, until call free_screen()
        """
        self.__last_screen = self.screenshot()
        self.__keep_screen = True
        return self
        
    def free_screen(self):
        """
        Unlock keep_screen()
        """
        self.__keep_screen = False
        return self

    def region_screenshot(self, filename=None):
        """ take part of the screenshot """
        screen = self.__last_screen if self.__keep_screen else self.screenshot()
        if self.bounds:
            screen = screen.crop(self.bounds)
        if filename:
            screen.save(filename)
        return screen

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

    @hook_wrap(consts.EVENT_ASSERT_EXISTS)
    def assert_exists(self, pattern, timeout=20.0, desc=None, **match_kwargs):
        """Assert if image exists
        Args:
            - image: image filename # not support pattern for now
            - timeout (float): seconds

        Returns:
            Find point

        Raises:
            AssertExistsError
        """
        pattern = self.pattern_open(pattern)
        search_img = pattern.image
        # search_img = imutils.open(image)
        log.info('assert exists image(%s): %s', desc or '', pattern)
        start_time = time.time()
        while time.time() - start_time < timeout:
            point = self.match(search_img, **match_kwargs)
            if point is None:
                sys.stdout.write('.')
                sys.stdout.flush()
                continue
            if not point.matched:
                log.debug('Ignore confidence: %s', point.confidence)
                continue
            log.debug('assert pass, confidence: %s', point.confidence)
            sys.stdout.write('\n')
            return point
        else:
            sys.stdout.write('\n')
            raise errors.AssertExistsError('image not found %s' %(pattern,))
            
    @hook_wrap(consts.EVENT_CLICK_IMAGE)
    def click_nowait(self, pattern, action='click', desc=None, **match_kwargs):
        """ Return immediately if no image found

        Args:
            - pattern (str or Pattern): filename or an opencv image object.
            - action (str): click or long_click

        Returns:
            Click point or None
        """
        point = self.match(pattern, **match_kwargs)
        if not point or not point.matched:
            return None

        func = getattr(self, action)
        func(*point.pos)
        return point

    @hook_wrap(consts.EVENT_CLICK_IMAGE)
    def click_image(self, pattern, timeout=20.0, action='click', safe=False, desc=None, delay=None, **match_kwargs):
        """Simulate click according image position

        Args:
            - pattern (str or Pattern): filename or an opencv image object.
            - timeout (float): if image not found during this time, ImageNotFoundError will raise.
            - action (str): click or long_click
            - safe (bool): if safe is True, Exception will not raise and return None instead.
            - method (str): image match method, choice of <template|sift>
            - delay (float): wait for a moment then perform click

        Returns:
            None

        Raises:
            ImageNotFoundError: An error occured when img not found in current screen.
        """
        pattern = self.pattern_open(pattern)
        log.info('click image:%s %s', desc or '', pattern)
        start_time = time.time()
        found = False
        point = None
        while time.time() - start_time < timeout:
            point = self.match(pattern, **match_kwargs)
            if point is None:
                sys.stdout.write('.')
                sys.stdout.flush()
                continue

            log.debug('confidence: %s', point.confidence)
            if not point.matched:
                log.info('Ignore confidence: %s', point.confidence)
                continue
            
            # wait for program ready
            if delay and delay > 0:
                self.delay(delay)

            func = getattr(self, action)
            func(*point.pos)

            found = True
            break
        sys.stdout.write('\n')

        if not found:
            if safe:
                log.info("Image(%s) not found, safe=True, skip", pattern)
                return None
            raise errors.ImageNotFoundError('Not found image %s' % pattern, point)

        # FIXME(ssx): maybe this function is too complex
        return point #collections.namedtuple('X', ['pattern', 'point'])(pattern, point)

    def watch(self, name='', timeout=None, raise_errors=True):
        """Return a new watcher
        Args:
            name: string watcher name
            timeout: watch timeout

        Returns:
            watcher object
        """
        warnings.warn("The 'watch' function was not recommend since v1.0.13.", DeprecationWarning, stacklevel=2)

        w = Watcher(self, name, timeout, raise_errors)
        w._dev = self
        return w


if __name__ == '__main__':
    b = Bounds(1, 2, 3, 4)
    print b
    print b * 1.0
