#!/usr/bin/env python
# -*- coding: utf-8 -*-

# USAGE
# python -matx -s ESLKJXX gui

from __future__ import absolute_import
from __future__ import unicode_literals
from __future__ import print_function

import argparse
import functools
import json
import sys
import six
import inspect
from contextlib import contextmanager

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


def _apk_parse(args):
    if six.PY2:
        raise EnvironmentError(
            "Command \"apkparse\" only available in Python 3.4+")

    from atx import apkparse
    manifest = apkparse.parse_apkfile(args.filename)
    print(json.dumps({
        'package_name': manifest.package_name,
        'main_activity': manifest.main_activity,
        'version': {
            'code': manifest.version_code,
            'name': manifest.version_name,
        }
    }, indent=4))


def _version(args):
    import atx
    print(atx.version)


def _deprecated(args):
    print('Deprecated')


def main():
    ap = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    ap.add_argument("-s", "--serial", "--udid", required=False,
                    help="Android serial or iOS unid")
    ap.add_argument("-H", "--host", required=False,
                    default='127.0.0.1', help="Adb host")
    ap.add_argument("-P", "--port", required=False,
                    type=int, default=5037, help="Adb port")

    subp = ap.add_subparsers()

    @contextmanager
    def add_parser(name):
        yield subp.add_parser(name, formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    with add_parser('tcpproxy') as p:
        p.description = 'A very simple tcp proxy'
        p.add_argument('-l', '--listen', default=5555,
                       type=int, help='Listen port')
        p.add_argument('-f', '--forward', default=26944,
                       type=int, help='Forwarded port')
        p.add_argument('--host', default='127.0.0.1',
                       type=str, help='Forwarded host')
        p.set_defaults(func=load_main('tcpproxy'))

    with add_parser('gui') as p:
        p.description = 'GUI tool to help write test script'
        p.add_argument('-p', '--platform', default='auto',
                       choices=('auto', 'android', 'ios'), help='platform')
        p.add_argument('-s', '--serial', default=None, type=str,
                       help='android serial or WDA device url')
        p.add_argument('--scale', default=0.5, type=float, help='scale size')
        p.set_defaults(func=load_main('tkgui'))

    # Remove because of unstable
    # with add_parser('record') as p:
    #     p.add_argument('-d', '--workdir', default='.', help='workdir where case & frame files are saved.')
    #     p.add_argument('-e', '--edit', action='store_true', dest='edit_mode', help='edit old records.')
    #     p.add_argument('-a', '--nonui-activity', action='append', dest='nonui_activities',
    #         required=False, help='nonui-activities for which the recorder will analyze screen image instead of uixml.')
    #     p.set_defaults(func=load_main('record'))

    with add_parser('minicap') as p:
        p.description = 'install minicap to phone'
        p.set_defaults(func=load_main('minicap'))

    with add_parser('apkparse') as p:
        p.description = 'parse package-name and main-activity from apk'
        p.add_argument('filename', help='Apk filename')
        p.set_defaults(func=_apk_parse)

    with add_parser('monkey') as p:
        p.set_defaults(func=load_main('monkey'))

    with add_parser('install') as p:
        p.description = 'install apk to phone'
        p.add_argument(
            'path', help='<apk file path | apk url path> (only support android for now)')
        p.add_argument('--start', action='store_true',
                       help='Start app when app success installed')
        p.set_defaults(func=load_main('install'))

    with add_parser('screen') as p:
        p.add_argument('--scale', required=False, type=float,
                       default=0.5, help='image scale')
        p.add_argument('--simple', action='store_true',
                       help='disable interact controls')
        p.set_defaults(func=load_main('screen'))

    with add_parser('screencap') as p:
        p.description = 'take screenshot'
        p.add_argument('--scale', required=False, type=float,
                       default=1.0, help='image scale')
        p.add_argument('-o', '--out', required=False,
                       default='screenshot.png', help='output path')
        p.add_argument('-m', '--method', required=False, default='minicap',
                       choices=('minicap', 'screencap'), help='screenshot method')
        p.set_defaults(func=load_main('screencap'))

    with add_parser('screenrecord') as p:
        p.description = 'record video (require minicap)'
        p.add_argument('-o', '--output', default='out.avi',
                       help='video output path')
        p.add_argument('--overwrite', action='store_true',
                       help='overwrite video output file.')
        p.add_argument('--scale', type=float, default=0.5,
                       help='image scale for video')
        p.add_argument('-q', '--quiet', dest='verbose',
                       action='store_false', help='display screen while recording.')
        p.add_argument('--portrait', action='store_true',
                       help='set video framesize to portrait instead of landscape.')
        p.set_defaults(func=load_main('screenrecord'))

    with add_parser('web') as p:
        p.description = 'not maintained this func, try with: pip install atx-webide'
        p.set_defaults(func=_deprecated)

    with add_parser('run') as p:
        p.add_argument('-f', dest='config_file',
                       default='atx.yml', help='config file')
        p.set_defaults(func=load_main('run'))

    with add_parser('version') as p:
        p.set_defaults(func=_version)

    with add_parser('info') as p:
        p.set_defaults(func=load_main('info'))

    with add_parser('doctor') as p:
        p.set_defaults(func=load_main('doctor'))

    args = ap.parse_args()
    if not hasattr(args, 'func'):
        print(' '.join(sys.argv) + ' -h for more help')
        return
    args.func(args)


if __name__ == '__main__':
    main()
