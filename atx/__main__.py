#!/usr/bin/env python
# -*- coding: utf-8 -*-

# USAGE
# python -matx -s ESLKJXX gui

import argparse
import functools
import json

from atx.cmds import tkgui, minicap, tcpproxy, webide, run
import atx.androaxml as apkparse

def _gui(args):
    tkgui.main(args.serial, host=args.host)


def _minicap(args):
    minicap.install(args.serial, host=args.host, port=args.port)


def _tcpproxy(args):
    tcpproxy.main(local_port=args.forward, listen_port=args.listen)


def _webide(args):
    webide.main(open_browser=(not args.no_browser), port=args.web_port)


def _apkparse(args):
    (pkg_name, activity) = apkparse.parse_apk(args.filename)
    print json.dumps({
        'package_name': pkg_name,
        'main_activity': activity,
    }, indent=4)


def _run(args):
    run.main(args.filename)


def main():
    ap = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    ap.add_argument("-s", "--serial", required=False, help="Android SerialNo")
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

    parser_webide = add_parser('web')
    parser_webide.add_argument('--no-browser', dest='no_browser', action='store_true', help='Not open browser')
    parser_webide.add_argument('--port', dest='web_port', default=None, type=int, help='web listen port')
    parser_webide.set_defaults(func=_webide)
    
    parser_webide = add_parser('apkparse')
    parser_webide.add_argument('filename', help='Apk filename')
    parser_webide.set_defaults(func=_apkparse)

    parser_webide = add_parser('run')
    parser_webide.add_argument('filename', help='Python script filename')
    parser_webide.set_defaults(func=_run)

    args = ap.parse_args()
    args.func(args)


if __name__ == '__main__':
    main()
