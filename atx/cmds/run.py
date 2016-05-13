#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# parse and run atx.yml
#
# from __future__ import print_function

import os
import sys
import json
from argparse import Namespace

import yaml
import subprocess32 as subprocess


CONFIG_FILE = 'atx.yml'


def json2obj(data):
    return json.loads(json.dumps(data), object_hook=lambda d: Namespace(**d))


def install(src):
    print src


def runtest(scripts):
    print scripts


def notify_popo(users, message):
    print users, message


def main(config_file):
    if not os.path.exists(config_file):
        sys.exit('config file (%s) not found.' % config_file)

    with open(config_file, 'rb') as f:
        cfg = json2obj(yaml.load(f))
    
    if hasattr(cfg, 'installation'):
        install(cfg.installation)

    if hasattr(cfg, 'script'):
        if isinstance(cfg.script, basestring):
            scripts = [cfg.script]
        else:
            scripts = cfg.script
        runtest(scripts)

    if hasattr(cfg, 'notification'):
        if hasattr(cfg.notification, 'popo'):
            notify_popo(cfg.notification.popo, 'hi')


if __name__ == '__main__':
    main('atx.yml')