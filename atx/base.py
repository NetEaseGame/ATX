#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import subprocess
import random
import string
import time
import logging
import threading

random.seed(time.time())

def id_generator(n=5):
    return ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(n))


def dirname(name):
    if os.path.isabs(name):
        return os.path.dirname(name)
    return os.path.dirname(os.path.abspath(name))


def exec_cmd(*cmds, **kwargs):
    '''
    @arguments env=None, timeout=3
    may raise Error
    '''
    env = os.environ.copy()
    env.update(kwargs.get('env', {}))
    envcopy = {}
    for key in env: 
        try:
            envcopy[key] = str(env[key]).encode('utf-8') # fix encoding
        except:
            print 'IGNORE BAD ENV KEY:', repr(key)
    env = envcopy

    timeout = kwargs.get('timeout', 120)
    shell = kwargs.get('shell', False)
    try:
        import sh
        # log.debug('RUN(timeout=%ds): %s'%(timeout, ' '.join(cmds)))
        if shell:
            cmds = list(cmds)
            cmds[:0] = ['bash', '-c']
        c = sh.Command(cmds[0])
        try:
            r = c(*cmds[1:], _err_to_out=True, _out=sys.stdout, _env=env, _timeout=timeout)
        except:
            # log.error('EXEC_CMD error, cmd: %s'%(' '.join(cmds)))
            raise
    except ImportError:
        # log.debug('RUN(timeout=XX): %s'%(' '.join(cmds)))
        if shell:
            cmds = ' '.join(cmds)
        r = subprocess.Popen(cmds, env=env, stdout=sys.stdout, stderr=sys.stderr, shell=shell)
        return r.wait()
    return 0


def random_name(name):
    out = []
    for c in name:
        if c == 'X':
            c = random.choice(string.ascii_lowercase)
        out.append(c)
    return ''.join(out)


def remove_force(name):
    if os.path.isfile(name):
        os.remove(name)


SYSTEM_ENCODING = 'gbk' if os.name == 'nt' else 'utf-8'
VALID_IMAGE_EXTS = ['.jpg', '.jpeg', '.png', '.bmp']


def auto_decode(s, encoding='utf-8'):
    return s if isinstance(s, unicode) else unicode(s, encoding)

def list_images(path=['.']):
    """ Return list of image files """
    for image_dir in set(path):
        if not os.path.isdir(image_dir):
            continue
        for filename in os.listdir(image_dir):
            bname, ext = os.path.splitext(filename)
            if ext not in VALID_IMAGE_EXTS:
                continue

            filepath = os.path.join(image_dir, filename)
            yield auto_decode(filepath, SYSTEM_ENCODING)


def search_image(name=None, path=['.']):
    """
    look for the image real path, if name is None, then return all images under path.
    FIXME(ssx): this code is just looking wired.
    """
    name = auto_decode(name)

    for image_dir in path:
        if not os.path.isdir(image_dir):
            continue
        image_path = os.path.join(auto_decode(image_dir), name)
        if os.path.isfile(image_path):
            return image_path.encode(SYSTEM_ENCODING)
    return None


if __name__ == '__main__':
    print search_image('你好.png')
    print search_image('oo')
    print search_image()
