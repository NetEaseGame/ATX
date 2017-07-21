#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division

import atexit
import argparse
import os
import time
import json
import warnings
import inspect
import codecs

import imageio

from atx import consts
from atx import errors
from atx import imutils
from atx.base import nameddict
from atx.ext.report import patch as pt
from PIL import Image


__dir__ = os.path.dirname(os.path.abspath(__file__))


class ExtDeprecationWarning(DeprecationWarning):
    pass

warnings.simplefilter('always', ExtDeprecationWarning)

def json2obj(data):
    data['this'] = data.pop('self', None)
    return nameddict('X', data.keys())(**data)

def center(bounds):
    x = (bounds['left'] + bounds['right'])//2
    y = (bounds['top'] + bounds['bottom'])//2
    return (x, y)


class Report(object):
    """
    Example usage:
    from atx.ext.report import Report

    Report(d)
    """
    def __init__(self, d, save_dir='report'):
        image_dir = os.path.join(save_dir, 'images')
        if not os.path.exists(image_dir):
            os.makedirs(image_dir)

        self.d = d
        self.save_dir = save_dir
        self.steps = []
        self.result = None

        self.__gif_path = os.path.join(save_dir, 'output.gif')
        self.__gif = imageio.get_writer(self.__gif_path, format='GIF', fps=2)
        self.__uia_last_position = None
        self.__last_screenshot = None
        self.__closed = False
        
        self.start_record()

    @property
    def last_screenshot(self):
        return self.__last_screenshot

    def _uia_listener(self, evtjson):
        evt = json2obj(evtjson)
        if evt.name != '_click':
            return
        if evt.is_before:
            self.d.screenshot()
            self.__uia_last_position = center(evt.this.bounds)
        else:
            (x, y) = self.__uia_last_position
            # self.last_screenshot
            cv_last_img = imutils.from_pillow(self.last_screenshot)
            cv_last_img = imutils.mark_point(cv_last_img, x, y)
            screen = imutils.to_pillow(cv_last_img)
            screen_before = self._save_screenshot(screen=screen, name_prefix='click-before')
            # FIXME: maybe need sleep for a while
            screen_after = self._save_screenshot(name_prefix='click-after')

            self.add_step('click',
                screen_before=screen_before,
                screen_after=screen_after,
                position={'x': x, 'y': y})

    def add_step(self, action, **kwargs):
        kwargs['success'] = kwargs.pop('success', True)
        kwargs['description'] = kwargs.get('description') or kwargs.get('desc')
        kwargs['time'] = round(kwargs.pop('time', time.time()-self.start_time), 1)
        kwargs['action'] = action
        self.steps.append(kwargs)

    def patch_uiautomator(self):
        """
        Record steps of uiautomator
        """
        import uiautomator
        uiautomator.add_listener('atx-report', self._uia_listener)

    def patch_wda(self):
        """
        Record steps of WebDriverAgent
        """
        import wda

        def _click(that):
            rawx, rawy = that.bounds.center
            x, y = self.d.scale*rawx, self.d.scale*rawy
            screen_before = self._save_screenshot()
            orig_click = pt.get_original(wda.Selector, 'click')
            screen_after = self._save_screenshot()
            self.add_step('click',
                screen_before=screen_before,
                screen_after=screen_after,
                position={'x': x, 'y': y})
            return orig_click(that)

        pt.patch_item(wda.Selector, 'click', _click)

    def start_record(self):
        self.start_time = time.time()

        w, h = self.d.display
        if self.d.rotation in (1, 3): # for horizontal
            w, h = h, w
        self.result = dict(device=dict(
            display=dict(width=w, height=h),
            serial=getattr(self.d, 'serial', ''),
            start_time=time.strftime("%Y-%m-%d %H:%M:%S"),
            start_timestamp=time.time(),
        ), steps=self.steps)

        self.d.add_listener(self._listener, consts.EVENT_ALL) # ^ consts.EVENT_SCREENSHOT)

        self.__closed = False
        atexit.register(self.close)

    def close(self):
        if self.__closed:
            return

        save_dir = self.save_dir
        data = json.dumps(self.result)
        tmpl_path = os.path.join(__dir__, 'index.tmpl.html')
        save_path = os.path.join(save_dir, 'index.html')
        json_path = os.path.join(save_dir, 'result.json')

        with codecs.open(tmpl_path, 'rb', 'utf-8') as f:
            html_content = f.read().replace('$$data$$', data)

        with open(json_path, 'wb') as f:
            f.write(json.dumps(self.result, indent=4).encode('utf-8'))

        with open(save_path, 'wb') as f:
            f.write(html_content.encode('utf-8'))

        self.__gif.close()
        self.__closed = True

    def info(self, text, screenshot=None):
        """
        Args:
            - text(str): description
            - screenshot: Bool or PIL.Image object
        """
        step = {
            'time': '%.1f' % (time.time()-self.start_time,),
            'action': 'info',
            'description': text,
            'success': True,
        }   
        if screenshot:
            step['screenshot'] = self._take_screenshot(screenshot, name_prefix='info')
        self.steps.append(step)

    def error(self, text, screenshot=None):
        """
        Args:
            - text(str): description
            - screenshot: Bool or PIL.Image object
        """
        step = {
            'time': '%.1f' % (time.time()-self.start_time,),
            'action': 'error',
            'description': text,
            'success': False,
        }   
        if screenshot:
            step['screenshot'] = self._take_screenshot(screenshot, name_prefix='error')
        self.steps.append(step)

    def _save_screenshot(self, screen=None, name=None, name_prefix='screen'):
        if screen is None:
            screen = self.d.screenshot()
        if name is None:
            name = 'images/%s_%d.jpg' % (name_prefix, time.time()*1000)
        relpath = os.path.join(self.save_dir, name)
        if hasattr(screen, 'convert'): # pillow image
            png = screen.convert("RGBA")
            bg = Image.new("RGB", png.size, (255, 255, 255))
            bg.paste(png, mask=png.split()[3]) # 3 is alpha channel
            bg.save(relpath, "JPEG", quality=80)
            self._add_to_gif(screen)
        else: # pattern
            screen.save(relpath)
        return name

    def _add_to_gif(self, image):
        half = 0.5
        out = image.resize([int(half*s) for s in image.size])
        cvimg = imutils.from_pillow(out)
        self.__gif.append_data(cvimg[:, :, ::-1])

    def _take_screenshot(self, screenshot=False, name_prefix='unknown'):
        """
        This is different from _save_screenshot.
        The return value maybe None or the screenshot path

        Args:
            screenshot: bool or PIL image
        """
        if isinstance(screenshot, bool):
            if not screenshot:
                return
            return self._save_screenshot(name_prefix=name_prefix)
        if isinstance(screenshot, Image.Image):
            return self._save_screenshot(screen=screenshot, name_prefix=name_prefix)

        raise TypeError("invalid type for func _take_screenshot: "+ type(screenshot))

    def _record_assert(self, is_success, text, screenshot=False, desc=None):
        step = {
            'time': '%.1f' % (time.time()-self.start_time,),
            'action': 'assert',
            'message': text,
            'description': desc,
            'success': is_success,
            'screenshot': self._take_screenshot(screenshot, name_prefix='assert'),
        }
        self.steps.append(step)

    def _add_assert(self, **kwargs):
        """
        if screenshot is None, only failed case will take screenshot
        """
        # convert screenshot to relative path from <None|True|False|PIL.Image>
        screenshot = kwargs.get('screenshot')
        is_success = kwargs.get('success')
        screenshot = (not is_success) if screenshot is None else screenshot
        kwargs['screenshot'] = self._take_screenshot(screenshot=screenshot, name_prefix='assert')
        action = kwargs.pop('action', 'assert')
        self.add_step(action, **kwargs)
        if not is_success:
            message = kwargs.get('message')
            frame, filename, line_number, function_name, lines, index = inspect.stack()[2]
            print('Assert [%s: %d] WARN: %s' % (filename, line_number, message))
            if not kwargs.get('safe', False):
                raise AssertionError(message)

    def assert_equal(self, v1, v2, **kwargs):#, desc=None, screenshot=False, safe=False):
        """ Check v1 is equals v2, and take screenshot if not equals
        Args:
            - desc (str): some description
            - safe (bool): will omit AssertionError if set to True
            - screenshot: can be type <None|True|False|PIL.Image>
        """
        is_success = v1 == v2
        if is_success:
            message = "assert equal success, %s == %s" %(v1, v2)
        else:
            message = '%s not equal %s' % (v1, v2)
        kwargs.update({
            'message': message,
            'success': is_success,
        })
        self._add_assert(**kwargs)

    def assert_image_exists(self, pattern, timeout=20.0, **kwargs):
        """
        Assert if image exists
        Args:
            - pattern: image filename # not support pattern for now
            - timeout (float): seconds
            - safe (bool): not raise assert error even throung failed.
        """
        pattern = self.d.pattern_open(pattern)
        match_kwargs = kwargs.copy()
        match_kwargs.pop('safe', None)
        match_kwargs.update({
            'timeout': timeout,
            'safe': True,
        })
        res = self.d.wait(pattern, **match_kwargs)
        is_success = res is not None
        message = 'assert image exists'
        if res:
            x, y = res.pos
            kwargs['position'] = {'x': x, 'y': y}
            message = 'image exists\npos %s\nconfidence=%.2f\nmethod=%s' % (res.pos, res.confidence, res.method)
        else:
            res = self.d.match(pattern)
            if res is None:
                message = 'Image not found'
            else:
                th = kwargs.get('threshold') or pattern.threshold or self.image_match_threshold
                message = 'Matched: %s\nPosition: %s\nConfidence: %.2f\nThreshold: %.2f' % (
                    res.matched, res.pos, res.confidence, th)

        kwargs['target'] = self._save_screenshot(pattern, name_prefix='target')
        kwargs['screenshot'] = self.last_screenshot
        kwargs.update({
            'action': 'assert_image_exists',
            'message': message,
            'success': is_success,
        })
        self._add_assert(**kwargs)

    def assert_ui_exists(self, ui, **kwargs):
        """ For Android & IOS
        Args:
            - ui: need have property "exists"
            - desc (str): description
            - safe (bool): will omit AssertionError if set to True
            - screenshot: can be type <None|True|False|PIL.Image>
            - platform (str, default:android): android | ios
        """
        is_success = ui.exists
        if is_success:
            if kwargs.get('screenshot') is not None:
                if self.d.platform == 'android':
                    bounds = ui.info['bounds'] # For android only.
                    kwargs['position'] = {
                        'x': (bounds['left']+bounds['right'])//2,
                        'y': (bounds['top']+bounds['bottom'])//2,
                    }
                elif self.d.platform == 'ios':
                    bounds = ui.bounds # For iOS only.
                    kwargs['position'] = {
                        'x': self.d.scale*(bounds.x+bounds.width//2),
                        'y': self.d.scale*(bounds.y+bounds.height//2),
                    }
            message = 'UI exists'
        else:
            message = 'UI not exists'
        kwargs.update({
            'message': message,
            'success': is_success,
        })
        self._add_assert(**kwargs)

    def _listener(self, evt):
        d = self.d

        # keep screenshot for every call
        if not evt.is_before and evt.flag == consts.EVENT_SCREENSHOT:
            self.__last_screenshot = evt.retval

        if evt.depth > 1: # base depth is 1
            return

        if evt.is_before: # call before function
            if evt.flag == consts.EVENT_CLICK:
                self.__last_screenshot = d.screenshot() # Maybe no need to set value here.
                (x, y) = evt.args
                cv_img = imutils.from_pillow(self.last_screenshot)
                cv_img = imutils.mark_point(cv_img, x, y)
                self.__last_screenshot = imutils.to_pillow(cv_img)
                self._add_to_gif(self.last_screenshot)
            return

        if evt.flag == consts.EVENT_CLICK:
            screen_before = self._save_screenshot(self.last_screenshot, name_prefix='before')
            screen_after = self._save_screenshot(name_prefix='after')

            (x, y) = evt.args
            self.add_step('click',
                screen_before=screen_before,
                screen_after=screen_after,
                position={'x': x, 'y': y})
        elif evt.flag == consts.EVENT_CLICK_IMAGE:
            kwargs = {
                'success': evt.traceback is None,
                'traceback': None if evt.traceback is None else evt.traceback.stack,
                'description': evt.kwargs.get('desc'),
            }
            # do not record if image not found and no trackback
            if evt.retval is None and evt.traceback is None:
                return
            
            # save before click image
            kwargs['screen_before'] = self._save_screenshot(self.last_screenshot, name_prefix='before')

            if evt.traceback is None or not isinstance(evt.traceback.exception, IOError):
                pattern = d.pattern_open(evt.args[0])
                kwargs['target'] = self._save_screenshot(pattern, name_prefix='target')
            if evt.traceback is None:
                # update image to add a click mark
                (x, y) = evt.retval.pos
                cv_img = imutils.from_pillow(self.last_screenshot)
                cv_img = imutils.mark_point(cv_img, x, y)
                self.__last_screenshot = imutils.to_pillow(cv_img)
                kwargs['screen_before'] = self._save_screenshot(self.last_screenshot, name=kwargs['screen_before'])

                kwargs['screen_after'] = self._save_screenshot(name_prefix='after')
                kwargs['confidence'] = evt.retval.confidence
                kwargs['position'] = {'x': x, 'y': y}
                
            self.add_step('click_image', **kwargs)
        # elif evt.flag == consts.EVENT_ASSERT_EXISTS: # this is image, not tested
        #     pattern = d.pattern_open(evt.args[0])
        #     target = 'images/target_%.2f.jpg' % time.time()
        #     self._save_screenshot(pattern, name=target)
        #     kwargs = {
        #         'target': target,
        #         'description': evt.kwargs.get('desc'),
        #         'screen': self._save_screenshot(name='images/screen_%.2f.jpg' % time.time()),
        #         'traceback': None if evt.traceback is None else evt.traceback.stack,
        #         'success': evt.traceback is None,
        #     }
        #     if evt.traceback is None:
        #         kwargs['confidence'] = evt.retval.confidence
        #         (x, y) = evt.retval.pos
        #         kwargs['position'] = {'x': x, 'y': y}
        #     self.add_step('assert_exists', **kwargs)


def listen(d, save_dir='report'):
    ''' Depreciated '''
    warnings.warn(
        "Using report.listen is deprecated, use report.Report(d, save_dir) instead.", 
        ExtDeprecationWarning, stacklevel=2
    )
    Report(d, save_dir)
