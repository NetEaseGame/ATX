#!/usr/bin/env python
# coding: utf-8

import logging


def getLogger(name, init=True, level=logging.INFO):
    logger = logging.getLogger(name)
    ch = logging.StreamHandler()
    fmt = "%(asctime)s %(levelname)-8.8s [%(name)s:%(lineno)4s] %(message)s"
    ch.setFormatter(logging.Formatter(fmt))
    ch.setLevel(level)
    logger.handlers = [ch]
    return logger


if __name__ == '__main__':
    log = getLogger('test')
    log.setLevel(logging.DEBUG)
    log.info("Hello")
    log.debug("dd Hello")
    log = getLogger('test')
    log.warn("dd Hello")