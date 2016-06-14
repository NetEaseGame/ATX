#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import json
import time

from atx import consts

def record_operation(d, logdir='cloudtest', filename='operation.log'):
    """Record operation log to file for cloudtest
    Args:
        - d: atx device
        - logdir(string) : directory store pictures and log name
        - filename(string) : log file name

    Returns:
        function name
    """
    def listener(event):
        data = dict(
            action='screenshot',
            success=1,
            time=time.strftime('%Y-%m-%d %H:%M:%S'),
            content='截图',
            has_pic=False)
        log_path = os.path.join(logdir, filename)
        with open(log_path, 'a') as f:
            f.write(json.dumps(data)+'\n')

    if not os.path.isdir(logdir):
        os.makedirs(logdir)
    d.add_listener(listener, consts.EVENT_ALL)
