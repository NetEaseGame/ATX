#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import unicode_literals
from __future__ import print_function

import os
import sys
import six
import platform


SYSTEM_ENCODING = 'gbk' if os.name == 'nt' else 'utf-8'

# if platform.system() in ('Linux', 'Darwin') and \
#         sys.stdout.encoding and sys.stdout.encoding.upper() != 'UTF-8':
#     print("""\033[93mWarning: System "{}" python's encoding is "{}".
# Chinese may not print normally, fix with the following command
#     export PYTHONIOENCODING=UTF-8\033[0m""".format(platform.system(), sys.stdout.encoding))


def encode(s, encoding=None, errors='ignore'):
    us = s if isinstance(s, six.text_type) else decode(s)
    return us.encode(encoding or SYSTEM_ENCODING, errors)


def decode(s, encodings=['utf-8', 'gbk', 'cp936']):
    if isinstance(s, six.text_type):
        return s

    for enc in encodings:
        try:
            return six.text_type(s, enc)
        except:
            pass
    raise UnicodeDecodeError(','.join(encodings), "", 0, len(s or ''), "string: '%s'" % repr(s))


if __name__ == '__main__':
    print('Hello 世界!')
    print(encode('Hello 世界!'))
    print(encode(u'Hello 世界!'))
    print(decode('Hello 世界!'))
    print(decode(u'Hello 世界!'))
