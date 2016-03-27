#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import time


code = ''
lineno = 0

def interpreter(*args):
    print 'I:', args
    time.sleep(0.5)

for line in open('simple-tcp-proxy.py'):
    lineno += 1
    contain_code = False
    if line.strip() and not line.strip().startswith('#'):
        contain_code = True
    if contain_code:
        code += 'interpreter({}, {})\n'.format(lineno, json.dumps(line.strip()))
    code += line

print code
exec(code, {'interpreter': interpreter})

# print line.rstrip()
