#!/usr/bin/env python
# coding: utf-8

import logging


_inited = {}

def getLogger(name):
    logger = logging.getLogger(name)
    #name = name.split('.', 1)[0]
    if not _inited.get(name):
        ch = logging.StreamHandler()
        _inited[name] = ch
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

