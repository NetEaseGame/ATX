#!/usr/bin/env python
# -*- coding: utf-8 -*-

# USAGE
# python -matx -s ESLKJXX gui

import argparse
import functools
import json
import sys
import inspect
from contextlib import contextmanager

import atx.androaxml as apkparse

from atx.cmds import run
from atx.cmds import iosdeveloper
from atx.cmds import install


def inject(func, kwargs):
    '''
    This is a black techonology of python. like golang martini inject

    Usage:
    allargs = dict(name='foo', message='body')
    def func(name):
        print 'hi', name

    inject(func, allargs)
    # will output
    # hi foo
    '''
    args = []
    for name in inspect.getargspec(func).args:
        args.append(kwargs.get(name))
    return func(*args)


def load_main(module_name):
    def _inner(parser_args):
        module_path = 'atx.cmds.'+module_name
        __import__(module_path)
        mod = sys.modules[module_path]
        pargs = vars(parser_args)
        return inject(mod.main, pargs)
    return _inner


def _webide(args):
    from atx.cmds import webide
    webide.main(open_browser=(not args.no_browser), port=args.web_port, adb_host=args.host, adb_port=args.port)


def _apk_parse(args):
    (pkg_name, activity) = apkparse.parse_apk(args.filename)
    print json.dumps({
        'package_name': pkg_name,
        'main_activity': activity,
    }, indent=4)


def _run(args):
    run.main(args.config_file)

def _screen(args):
    from atx.cmds import screen
    screen.main(args.scale, args.controls)

def _screenrecord(args):
    from atx.cmds import screenrecord
    screenrecord.main(args.output, args.scale, args.portrait, args.overwrite, args.verbose)


def main():
    ap = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    ap.add_argument("-s", "--serial", "--udid", required=False, help="Android serial or iOS unid")
    ap.add_argument("-H", "--host", required=False, default='127.0.0.1', help="Adb host")
    ap.add_argument("-P", "--port", required=False, type=int, default=5037, help="Adb port")

    subparsers = ap.add_subparsers()
    add_parser = functools.partial(subparsers.add_parser, 
            formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    # TODO: need to change to with ... as p
    parser_web = add_parser('web')
    parser_web.add_argument('--no-browser', dest='no_browser', action='store_true', help='Not open browser')
    parser_web.add_argument('--port', dest='web_port', default=None, type=int, help='web listen port')
    parser_web.set_defaults(func=_webide)

    parser_run = add_parser('run')
    parser_run.add_argument('-f', dest='config_file', default='atx.yml', help='config file')
    parser_run.set_defaults(func=_run)

    parse_scr = add_parser('screen')
    parse_scr.add_argument('-s', '--scale', required=False, default=0.5, help='image scale, default is 0.5')
    parse_scr.add_argument('--simple', dest='controls', action='store_false', help='disable interact controls')
    parse_scr.set_defaults(func=_screen)

    parse_scrrec = add_parser('screenrecord')
    parse_scrrec.add_argument('-o', '--output', required=False, default='out.avi', help='video output path, default is out.avi')
    parse_scrrec.add_argument('--overwrite', action='store_true', help='overwrite video output file.')
    parse_scrrec.add_argument('-s', '--scale', required=False, default=0.5, help='image scale for video, default is 0.5')
    parse_scrrec.add_argument('-q', '--quiet', dest='verbose', action='store_false', help='display screen while recording.')
    parse_scrrec.add_argument('--portrait', action='store_true', help='set video framesize to portrait instead of landscape.')
    parse_scrrec.set_defaults(func=_screenrecord)

    @contextmanager
    def add_parser(name):
        yield subparsers.add_parser(name, formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    with add_parser('tcpproxy') as p:
        p.add_argument('-l', '--listen', default=5555, type=int, help='Listen port')
        p.add_argument('-f', '--forward', default=26944, type=int, help='Forwarded port')
        p.set_defaults(func=load_main('tcpproxy'))

    with add_parser('gui') as p:
        p.set_defaults(func=load_main('tkgui'))

    with add_parser('record') as p:
        p.set_defaults(func=load_main('record'))

    with add_parser('minicap') as p:
        p.set_defaults(func=load_main('minicap'))

    with add_parser('apkparse') as p:
        p.add_argument('filename', help='Apk filename')
        p.set_defaults(func=_apk_parse)

    with add_parser('monkey') as p:
        p.set_defaults(func=load_main('monkey'))

    with add_parser('iosdeveloper') as p:
        p.add_argument('-u', '--udid', required=False, help='iOS udid')
        p.set_defaults(func=load_main('iosdeveloper'))

    with add_parser('install') as p:
        p.add_argument('path', help='<apk file path | apk url path> (only support android for now)')
        p.add_argument('--start', action='store_true', help='Start app when app success installed')
        p.set_defaults(func=load_main('install'))

    args = ap.parse_args()
    args.func(args)

if __name__ == '__main__':
    main()
