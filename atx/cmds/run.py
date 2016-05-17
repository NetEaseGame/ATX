#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# parse and run atx.yml
#
# # example of atx.yml
# #
# installation: http://example.com/demo.apk
# script:
# - python test1.py
# - python test2.py
# notification:
#   popo:
#   - someone@example.com
#
from __future__ import absolute_import

import os
import sys
import json
from argparse import Namespace

import yaml
import subprocess32 as subprocess


def json2obj(data):
    return json.loads(json.dumps(data), object_hook=lambda d: Namespace(**d))


def prompt(message):
    print '>>>', message


def must_exec(*cmds, **kwargs):
    prompt("Exec %s" % cmds)
    shell = kwargs.get('shell', False)
    cmdline = cmds[0] if shell else subprocess.list2cmdline(cmds)
    ret = os.system(cmdline)
    if ret != 0:
        raise SystemExit("Execute '%s' error" % cmdline)


def install(src):
    prompt("Install")
    must_exec('python', '-matx', 'install', src)


def runtest(scripts):
    prompt("Run scripts")
    for script in scripts:
        must_exec(script, shell=True)


def notify_popo(users, message):
    prompt("Notify popo users")
    print 'Skip, todo'
    for user in users:
        pass
    # maybe should not put code here
    # print users, message


def main(config_file):
    if not os.path.exists(config_file):
        sys.exit('config file (%s) not found.' % config_file)

    with open(config_file, 'rb') as f:
        cfg = json2obj(yaml.load(f))
    
    try:
        if hasattr(cfg, 'installation'):
            install(cfg.installation)

        if hasattr(cfg, 'script'):
            if isinstance(cfg.script, basestring):
                scripts = [cfg.script]
            else:
                scripts = cfg.script
            runtest(scripts)
    finally:
        if hasattr(cfg, 'notification'):
            if hasattr(cfg.notification, 'popo'):
                notify_popo(cfg.notification.popo, 'hi')


if __name__ == '__main__':
    main('atx.yml')