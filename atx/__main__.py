#!/usr/bin/env python

# USAGE
# python -matx gui -s ESLKJXX

import argparse

from atx import tkgui

def gui(args):
    tkgui.main(args.serial, host=args.host)

def main():
    ap = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    ap.add_argument("-s", "--serial", required=False, help="Android serialno")
    ap.add_argument("-H", "--host", required=False, default='127.0.0.1', help="Android serialno")

    subparsers = ap.add_subparsers()
    parser_gui = subparsers.add_parser('gui')
    parser_gui.set_defaults(func=gui)

    args = ap.parse_args()
    args.func(args)


if __name__ == '__main__':
    main()
