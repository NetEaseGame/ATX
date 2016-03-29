#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# python simple interpreter
#
from __future__ import print_function

import json
import time


def interpreter(*args):
    print('TRACE:', args)
    time.sleep(0.5)


def main(filename):
    code = ''
    lineno = 0
    for line in open(filename):
        lineno += 1
        contain_code = False
        if line.strip() and not line.strip().startswith('#'):
            contain_code = True
        if line.strip().startswith('except'):
            contain_code = False
        if line.find('__future__') != -1:
            contain_code = False
        prefix = line[:len(line) - len(line.lstrip())]
        if contain_code:
            code += prefix+'interpreter({}, {})\n'.format(lineno, json.dumps(line.strip()))
        code += line

    exec(code, {'__name__': '__main__', 'interpreter': interpreter})

if __name__ == '__main__':
    main('tcpproxy.py')