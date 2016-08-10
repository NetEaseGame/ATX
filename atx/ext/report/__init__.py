#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import

import atexit
import argparse
import os
import time
import json
import warnings

from atx import consts
from atx import errors
from atx.base import nameddict
from atx.ext.report import patch as pt


__dir__ = os.path.dirname(os.path.abspath(__file__))


class ExtDeprecationWarning(DeprecationWarning):
    pass

warnings.simplefilter('always', ExtDeprecationWarning)

def json2obj(data):
    data['this'] = data.pop('self', None)
    return nameddict('X', data.keys())(**data)

def center(bounds):
    x = (bounds['left'] + bounds['right'])/2
    y = (bounds['top'] + bounds['bottom'])/2
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
            screen_before = self._save_screenshot(self.last_screenshot)
            # FIXME: maybe need sleep for a while
            screen_after = self._save_screenshot()
            (x, y) = self.__uia_last_position
            self.add_step('click',
                screen_before=screen_before,
                screen_after=screen_after,
                position={'x': x, 'y': y})

    def add_step(self, action, **kwargs):
        kwargs['success'] = kwargs.pop('success', True)
        kwargs['time'] = round(kwargs.pop('time', time.time()-self.start_time), 1)
        kwargs['action'] = action
        self.steps.append(kwargs)

    def _save_screenshot(self, screen=None):
        if screen is None:
            screen = self.d.screenshot()
        abspath = 'images/before_%d.png' % time.time()
        relpath = os.path.join(self.save_dir, abspath)
        screen.save(relpath)
        return abspath

    def patch_uiautomator(self):
        """ record steps of uiautomator """
        import uiautomator
        uiautomator.add_listener('atx-report', self._uia_listener)

    def patch_wda(self):
        """ record steps of webdriveragent """
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

        atexit.register(self.close)

    def close(self):
        if self.__closed:
            return

        save_dir = self.save_dir
        data = json.dumps(self.result)
        tmpl_path = os.path.join(__dir__, 'index.tmpl.html')
        save_path = os.path.join(save_dir, 'index.html')
        json_path = os.path.join(save_dir, 'result.json')

        with open(tmpl_path) as f:
            html_content = f.read().replace('$$data$$', data)

        with open(json_path, 'wb') as f:
            f.write(json.dumps(self.result, indent=4))

        with open(save_path, 'wb') as f:
            f.write(html_content)
        self.__closed = True

    def info(self, text):
        self.steps.append({
            'time': '%.1f' % (time.time()-self.start_time,),
            'action': 'info',
            'message': text,
            'success': True,
        })

    def error(self, text, screenshot=None):
        step = {
            'time': '%.1f' % (time.time()-self.start_time,),
            'action': 'error',
            'message': text,
            'success': False,
        }   
        screen_path = 'images/error_%d.png' % time.time()
        if screenshot:
            screen_abspath = os.path.join(self.save_dir, screen_path)
            screenshot.save(screen_abspath)
            step['screenshot'] = screen_path
        self.steps.append(step)

    def _listener(self, evt):
        d = self.d
        screen_before = 'images/before_%d.png' % time.time()
        screen_before_abspath = os.path.join(self.save_dir, screen_before)

        # keep screenshot for every call
        if not evt.is_before and evt.flag == consts.EVENT_SCREENSHOT:
            self.__last_screenshot = evt.retval

        if evt.depth > 1: # base depth is 1
            return

        if evt.is_before: # call before function
            if evt.flag == consts.EVENT_CLICK:
                self.__last_screenshot = d.screenshot() # Maybe no need to set value here.
            return

        if evt.flag == consts.EVENT_CLICK:
            if self.last_screenshot: # just in case
                self.last_screenshot.save(screen_before_abspath)
            screen_after = 'images/after_%d.png' % time.time()
            d.screenshot(os.path.join(self.save_dir, screen_after))

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
            # not record if image not found
            if evt.retval is None and evt.traceback is None:
                return
            
            if self.last_screenshot:
                self.last_screenshot.save(screen_before_abspath)
                kwargs['screen_before'] = screen_before
            if evt.traceback is None or not isinstance(evt.traceback.exception, IOError):
                target = 'images/target_%d.png' % time.time()
                target_abspath = os.path.join(self.save_dir, target)
                pattern = d.pattern_open(evt.args[0])
                pattern.save(target_abspath)
                kwargs['target'] = target
            if evt.traceback is None:
                screen_after = 'images/after_%d.png' % time.time()
                d.screenshot(os.path.join(self.save_dir, screen_after))
                kwargs['screen_after'] = screen_after
                kwargs['confidence'] = evt.retval.confidence
                (x, y) = evt.retval.pos
                kwargs['position'] = {'x': x, 'y': y}
            self.add_step('click_image', **kwargs)


def listen(d, save_dir='report'):
    ''' Depreciated '''
    warnings.warn(
        "Using report.listen is deprecated, use report.Report(d, save_dir) instead.", 
        ExtDeprecationWarning, stacklevel=2
    )
    Report(d, save_dir)