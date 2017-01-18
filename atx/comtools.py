#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import absolute_import
from __future__ import unicode_literals


import time


class CountdownTimer(object):
    def __init__(self, timeout):
        self._timeout = timeout
        self._timeend = time.time() + timeout
    
    def reset(self, timeout=None):
        if timeout:
            self._timeout = timeout
        self._timeend = time.time() + self._timeout
        
    def ticking(self):
        return time.time() < self._timeend