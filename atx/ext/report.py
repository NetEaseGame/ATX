#!/usr/bin/env python
# -*- coding: utf-8 -*-

import atexit
import os
import time
import json

from atx import consts
from atx import errors


__dir__ = os.path.dirname(os.path.abspath(__file__))

def listen(d, save_dir='report'):
    image_dir = os.path.join(save_dir, 'images')
    if not os.path.exists(image_dir):
        os.makedirs(image_dir)

    steps = []
    w, h = d.display
    if d.rotation in (1, 3): # for horizontal
        w, h = h, w
    result = dict(device=dict(
        display=dict(width=w, height=h),
        serial=d.serial,
        start_time=time.strftime("%Y-%m-%d %H:%M:%S"),
        start_timestamp=time.time(),
    ), steps=steps)
    start_time = time.time()

    def listener(evt):
        screen_before = 'images/before_%d.png' % time.time()
        screen_before_abspath = os.path.join(save_dir, screen_before)

        if evt.flag == consts.EVENT_CLICK:
            if evt.depth > 1: # base depth is 1
                return
            d.last_screenshot.save(screen_before_abspath)
            screen_after = 'images/after_%d.png' % time.time()
            d.screenshot(os.path.join(save_dir, screen_after))

            (x, y) = evt.args
            steps.append({
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
            if d.last_screenshot:
                d.last_screenshot.save(screen_before_abspath)
                step['screen_before'] = screen_before
            if evt.traceback is None or not isinstance(evt.traceback.exception, IOError):
                target = 'images/target_%d.png' % time.time()
                target_abspath = os.path.join(save_dir, target)
                pattern = d.pattern_open(evt.args[0])
                pattern.save(target_abspath)
                step['target'] = target
            if evt.traceback is None:
                screen_after = 'images/after_%d.png' % time.time()
                d.screenshot(os.path.join(save_dir, screen_after))
                step['screen_after'] = screen_after
                step['confidence'] = evt.retval.confidence
                (x, y) = evt.retval.pos
                step['position'] = {'x': x, 'y': y}

            steps.append(step)
            # screen_before = 'images/before_%d.png' % time.time()
            # screen_before_abspath = os.path.join(save_dir, screen_before)

        # print 'EVENT:', evt

    d.add_listener(listener, consts.EVENT_ALL ^ consts.EVENT_SCREENSHOT)

    def on_finish():
        data = json.dumps(result)
        tmpl_path = os.path.join(__dir__, 'index.tmpl.html')
        save_path = os.path.join(save_dir, 'index.html')
        json_path = os.path.join(save_dir, 'result.json')

        with open(tmpl_path) as f:
            html_content = f.read().replace('$$data$$', data)

        with open(json_path, 'wb') as f:
            f.write(json.dumps(result, indent=4))

        with open(save_path, 'wb') as f:
            f.write(html_content)

    atexit.register(on_finish)