#!/usr/bin/env python
# -*- coding: utf-8 -*-

import atexit
import os
import time
import json
import warnings

from atx import consts
from atx import errors


__dir__ = os.path.dirname(os.path.abspath(__file__))


class ExtDeprecationWarning(DeprecationWarning):
    pass

warnings.simplefilter('always', ExtDeprecationWarning)


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
        # listen(self.d, self.save_dir)
        self.start_record()

    def start_record(self):
        self.start_time = time.time()

        w, h = self.d.display
        if self.d.rotation in (1, 3): # for horizontal
            w, h = h, w
        self.result = dict(device=dict(
            display=dict(width=w, height=h),
            serial=self.d.serial,
            start_time=time.strftime("%Y-%m-%d %H:%M:%S"),
            start_timestamp=time.time(),
        ), steps=self.steps)

        self.d.add_listener(self.listener, consts.EVENT_ALL ^ consts.EVENT_SCREENSHOT)
        atexit.register(self._finish)

    def _finish(self):
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

    def listener(self, evt):
        d = self.d
        start_time = self.start_time
        screen_before = 'images/before_%d.png' % time.time()
        screen_before_abspath = os.path.join(self.save_dir, screen_before)

        if evt.flag == consts.EVENT_CLICK:
            if evt.depth > 1: # base depth is 1
                return
            if d.last_screenshot: # just in case
                d.last_screenshot.save(screen_before_abspath)
            screen_after = 'images/after_%d.png' % time.time()
            d.screenshot(os.path.join(self.save_dir, screen_after))

            (x, y) = evt.args
            self.steps.append({
                'time': '%.1f' % (time.time()-start_time,),
                'action': 'click',
                'screen_before': screen_before,
                'screen_after': screen_after,
                'position': {'x': x, 'y': y},
                'success': True,
            })
        elif evt.flag == consts.EVENT_CLICK_IMAGE:
            step = {
                'time': '%.1f' % (time.time()-start_time,),
                'action': 'click_image',
                'success': evt.traceback is None,
                'traceback': None if evt.traceback is None else evt.traceback.stack,
            }
            # not record if image not found
            if evt.retval is None and evt.traceback is None:
                return
            
            if d.last_screenshot:
                d.last_screenshot.save(screen_before_abspath)
                step['screen_before'] = screen_before
            if evt.traceback is None or not isinstance(evt.traceback.exception, IOError):
                target = 'images/target_%d.png' % time.time()
                target_abspath = os.path.join(self.save_dir, target)
                pattern = d.pattern_open(evt.args[0])
                pattern.save(target_abspath)
                step['target'] = target
            if evt.traceback is None:
                screen_after = 'images/after_%d.png' % time.time()
                d.screenshot(os.path.join(self.save_dir, screen_after))
                step['screen_after'] = screen_after
                step['confidence'] = evt.retval.confidence
                (x, y) = evt.retval.pos
                step['position'] = {'x': x, 'y': y}

            self.steps.append(step)


def listen(d, save_dir='report'):
    ''' Depreciated '''
    warnings.warn(
        "Using report.listen is deprecated, use report.Report(d, save_dir) instead.", 
        ExtDeprecationWarning, stacklevel=2
    )
    Report(d, save_dir)