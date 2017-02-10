#! /usr/bin/env python
# -*- coding: utf-8 -*-
#
# check symbols are from:
# http://www.i2symbol.com/symbols/check

import os
import subprocess

from colorama import init, Fore, Back, Style
init()


def print_info(message, success):
    fore_color = Fore.GREEN
    symbol = '✔' if os.name != 'nt' else '[GOOD]'
    if not success:
        fore_color = Fore.RED
        symbol = '✘' if os.name != 'nt' else '[FAIL]'

    print(fore_color + "{symbol} {message}".format(symbol=symbol, message=message) + Style.RESET_ALL)   


def main():
    # check if adb exists
    try:
        subprocess.call(['adb', 'version'])
        print_info("adb found in env PATH", True)
    except OSError:
        print_info("adb not found in env PATH", False)


if __name__ == '__main__':
    main()