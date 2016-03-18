#!/usr/bin/env python
# coding: utf-8

import logging


def getLogger(name):
    logger = logging.getLogger(name)
    if len(logger.handlers) == 0:
        ch = logging.StreamHandler()
        fmt = "%(asctime)s %(levelname)-8.8s [%(name)s:%(lineno)4s] %(message)s"
        formatter = logging.Formatter(fmt)
        ch.setFormatter(formatter)
        logger.addHandler(ch)
    return logger


if __name__ == '__main__':
    log = getLogger('test')
    log.setLevel(logging.DEBUG)
    log.info("Hello")
    log.debug("dd Hello")
    log = getLogger('test')
    log.warn("dd Hello")