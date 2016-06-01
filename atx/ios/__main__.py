#!/usr/bin/env python
# -*- coding: utf-8 -*-

import argparse
import sys
import inspect
from contextlib import contextmanager

from PIL import Image
from atx import ioskit


def inject(func, kwargs):
    """ Allow call func with more arguments """
    args = []
    for name in inspect.getargspec(func).args:
        args.append(kwargs.get(name))
    return func(*args)


def load_main(module_name):
    def _inner(parser_args):
        __import__(module_name)
        mod = sys.modules[module_name]
        pargs = vars(parser_args)
        print pargs
        return inject(mod.main, pargs)
    return _inner


def _screencap(args):
    dev = ioskit.Device(args.udid)
    image = dev.screenshot()
    if args.rotate:
        method = getattr(Image, 'ROTATE_{}'.format(args.rotate))
        image = image.transpose(method)
    image.save(args.output)
    print 'Screenshot saved to "%s"' % args.output


def main():
    ap = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    ap.add_argument("-u", "--udid", required=False, help="iPhone udid")

    subp = ap.add_subparsers()

    @contextmanager
    def add_parser(name):
        yield subp.add_parser(name, formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    
    with add_parser('developer') as p:
        p.set_defaults(func=load_main('atx.cmds.iosdeveloper'))

    with add_parser('screencap') as p:
        p.add_argument('-o', '--output', default='screenshot.png', help='take iPhone screenshot')
        p.add_argument('-r', '--rotate', type=int, choices=[0, 90, 180, 270], default=0, help='screen rotation')
        p.set_defaults(func=_screencap)

    args = ap.parse_args()
    args.func(args)


if __name__ == '__main__':
    main()
