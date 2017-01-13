#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import absolute_import
from __future__ import unicode_literals

import inspect
import logging
import os
import sys
import time
import threading
import datetime

from atx import strutils


class Logger(object):
    __alias = {
        'WARNING': 'WARN',
        'CRITICAL': 'FATAL'
    }

    def __init__(self, name=None, level=logging.INFO):
        if name is None:
            name = '-'
        self._name = name
        self._level = level
        self._lock = threading.Lock()

    def _write(self, s):
        self._lock.acquire()
        sys.stdout.write(s.rstrip() + '\n')
        self._lock.release()

    def setLevel(self, level):
        '''
        set format level

        Args:
            - level: for example, logging.INFO

        '''
        self._level = level
        return self

    def _level_write(self, level, str_format, *args):
        if level < self._level:
            return

        levelname = logging.getLevelName(level)
        message = str_format % args if args else str_format
        message = strutils.decode(message)
        frame, filename, line_number, function_name, lines, index = inspect.stack()[2]
        props = dict(
            asctime=datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3],
            name=self._name,
            filename=os.path.basename(filename),
            lineno=line_number,
            message=message,
        )
        props['levelname'] = Logger.__alias.get(levelname, levelname)
        output = u'{asctime} {levelname:<5s} [{name}:{lineno:>4}] {message}'.format(**props)
        self._write(output)

    def debug(self, *args, **kwargs):
        self._level_write(logging.DEBUG, *args, **kwargs)

    def info(self, *args, **kwargs):
        self._level_write(logging.INFO, *args, **kwargs)

    def warn(self, *args, **kwargs):
        self._level_write(logging.WARN, *args, **kwargs)

    def error(self, *args, **kwargs):
        self._level_write(logging.ERROR, *args, **kwargs)

    def fatal(self, *args, **kwargs):
        self._level_write(logging.FATAL, *args, **kwargs)
        raise SystemExit(1)


def getLogger(name, level=logging.INFO):
    # logger = logging.getLogger(name)
    # ch = logging.StreamHandler()
    # fmt = "%(asctime)s %(levelname)-8.8s [%(name)s:%(lineno)4s] %(message)s"
    # ch.setFormatter(logging.Formatter(fmt))
    # ch.setLevel(level)
    # logger.handlers = [ch]
    return Logger(name, level=level)


if __name__ == '__main__':
    log = getLogger('test')
    log.debug("Should not see it.")
    log.setLevel(logging.DEBUG)
    log.setLevel(logging.DEBUG)
    log.info("This is info message")
    log.debug("This is debug message")
    log = getLogger('test')
    log.warn("This is warning message")
    log.error("This is error message")
    log.fatal("This is fatal message")
