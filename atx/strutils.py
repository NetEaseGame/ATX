#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import absolute_import

import os


SYSTEM_ENCODING = 'gbk' if os.name == 'nt' else 'utf-8'

def encode(s, encoding=None, errors='ignore'):
    us = s if isinstance(s, unicode) else decode(s)
    return us.encode(encoding or SYSTEM_ENCODING, errors)


def decode(s, encodings=['utf-8', 'gbk']):
    if isinstance(s, unicode):
        return s
    for enc in encodings:
        try:
            return unicode(s, enc)
        except:
            pass
    raise UnicodeDecodeError("string: %s not in encodings: %s" % (repr(s), encodings))


if __name__ == '__main__':
    print encode('Hello')