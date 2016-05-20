#!/usr/bin/env python
# -*- coding: utf-8 -*-

# USAGE
# python -matx -s ESLKJXX gui

import argparse
import functools
import json

import atx.androaxml as apkparse

from atx.cmds import run
from atx.cmds import iosdeveloper
from atx.cmds import install


def parser(name=None, debug=False):
    return wrap


def make_parser(debug=False):
    m = {}

    def wrap(fn):
        @functools.wraps(fn)
        def _inner(*args, **kwargs):
            try:
                return fn(*args, **kwargs)
            except Exception as e:
                if debug:
                    raise
                print 'ERROR: %s' % e
                raise SystemExit(1)

        m[fn.__name__] = _inner
        return _inner
    return (m, wrap)


funcs, wrap = make_parser(debug=True)


# serial, host, port, other args
# args: {serial: 'EFSF', host: '127.0.0.1', port: 5037, path: 'demo.apk'}
# name: gui
def parser_gui(serial, host, port, path):
    pass


def _gui(args):
    from atx.cmds import tkgui
    tkgui.main(args.serial, host=args.host)


def _minicap(args):
    from atx.cmds import minicap
    minicap.install(args.serial, host=args.host, port=args.port)


def _tcpproxy(args):
    from atx.cmds import tcpproxy
    tcpproxy.main(local_port=args.forward, listen_port=args.listen)


def _webide(args):
    from atx.cmds import webide
    webide.main(open_browser=(not args.no_browser), port=args.web_port, adb_host=args.host, adb_port=args.port)


def _monkey(args):
    from atx.cmds import monkey
    monkey.main(args.serial, args.host, args.port)


def _apk_parse(args):
    (pkg_name, activity) = apkparse.parse_apk(args.filename)
    print json.dumps({
        'package_name': pkg_name,
        'main_activity': activity,
    }, indent=4)


def _apk_install(args):
    install.main(args.path, serial=args.serial, host=args.host, port=args.port, start=args.start)


def _iosdeveloper(args):
    iosdeveloper.main(args)

def _record(args):
    # because record contains win32api which not working on unix system
    from atx.cmds import record
    record.main()

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
    parser_gui = add_parser('gui')
    parser_gui.set_defaults(func=_gui)

    parser_minicap = add_parser('minicap')
    parser_minicap.set_defaults(func=_minicap)

    parser_tcpproxy = add_parser('tcpproxy')
    parser_tcpproxy.add_argument('-l', '--listen', default=5555, type=int, help='Listen port')
    parser_tcpproxy.add_argument('-f', '--forward', default=26944, type=int, help='Forwarded port')
    parser_tcpproxy.set_defaults(func=_tcpproxy)

    parser_web = add_parser('web')
    parser_web.add_argument('--no-browser', dest='no_browser', action='store_true', help='Not open browser')
    parser_web.add_argument('--port', dest='web_port', default=None, type=int, help='web listen port')
    parser_web.set_defaults(func=_webide)
    
    parser_apk = add_parser('apkparse')
    parser_apk.add_argument('filename', help='Apk filename')
    parser_apk.set_defaults(func=_apk_parse)

    parser_ins = add_parser('install')
    parser_ins.add_argument('path', help='<apk file path | apk url path> (only support android for now)')
    parser_ins.add_argument('--start', action='store_true', help='Start app when app success installed')
    parser_ins.set_defaults(func=_apk_install)

    parser_run = add_parser('run')
    parser_run.add_argument('-f', dest='config_file', default='atx.yml', help='config file')
    parser_run.set_defaults(func=_run)

    parser_ios = add_parser('iosdeveloper')
    parser_ios.add_argument('-u', '--udid', required=False, help='iOS udid')
    parser_ios.set_defaults(func=_iosdeveloper)

    parse_record = add_parser('record')
    parse_record.set_defaults(func=_record)

    parse_monkey = add_parser('monkey')
    parse_monkey.set_defaults(func=_monkey)

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

    args = ap.parse_args()
    args.func(args)


if __name__ == '__main__':
    main()
