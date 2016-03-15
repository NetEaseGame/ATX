#!/usr/bin/env python

# USAGE
# python -matx -s ESLKJXX

# import the necessary packages
# import threading
# import Tkinter as Tk
# from Queue import Queue
import argparse

from atx import tkgui


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("-s", "--serial", required=False, help="Android serialno")
    ap.add_argument("-H", "--host", required=False, default='127.0.0.1', help="Android serialno")
    args = ap.parse_args()
    tkgui.main(args.serial, host=args.host)

if __name__ == '__main__':
    main()
