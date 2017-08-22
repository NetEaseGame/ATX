#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import absolute_import
from __future__ import print_function

import os
import sys
import subprocess
import random
import string
import time
import logging
import threading

from atx import strutils


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
            print('IGNORE BAD ENV KEY: ' + repr(key))
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
    if not os.path.isfile(name):
        return
    try:
        os.unlink(name)
    except Exception as e:
        print("Warning: tempfile {} not deleted, Error {}".format(name, e))


SYSTEM_ENCODING = 'gbk' if os.name == 'nt' else 'utf-8'
VALID_IMAGE_EXTS = ['.jpg', '.jpeg', '.png', '.bmp']


# def auto_decode(s, encoding='utf-8'):
#     return s if isinstance(s, unicode) else unicode(s, encoding)


def list_images(path=['.']):
    """ Return list of image files """
    for image_dir in set(path):
        if not os.path.isdir(image_dir):
            continue
        for filename in os.listdir(image_dir):
            bname, ext = os.path.splitext(filename)
            if ext.lower() not in VALID_IMAGE_EXTS:
                continue

            filepath = os.path.join(image_dir, filename)
            yield strutils.decode(filepath)


def list_all_image(path, valid_exts=VALID_IMAGE_EXTS):
    """List all images under path

    @return unicode list
    """
    for filename in os.listdir(path):
        bname, ext = os.path.splitext(filename)
        if ext.lower() not in VALID_IMAGE_EXTS:
            continue
        filepath = os.path.join(path, filename)
        yield strutils.decode(filepath)


def image_name_match(name, target):
    if name == target:
        return True

    bn = os.path.normpath(name)
    bt = os.path.basename(target)

    if bn == bt:
        return True

    bn, ext = os.path.splitext(bn)
    if ext != '':
        return False

    for ext in VALID_IMAGE_EXTS:
        if bn+ext == bt or bn+ext.upper() == bt:
            return True

    if bt.find('@') != -1:
        if bn == bt[:bt.find('@')]:
            return True
    return False


def search_image(name=None, path=['.']):
    """
    look for the image real path, if name is None, then return all images under path.

    @return system encoded path string
    FIXME(ssx): this code is just looking wired.
    """
    name = strutils.decode(name)
    for image_dir in path:
        if not os.path.isdir(image_dir):
            continue
        image_dir = strutils.decode(image_dir)
        image_path = os.path.join(image_dir, name)
        if os.path.isfile(image_path):
            return strutils.encode(image_path)

        for image_path in list_all_image(image_dir):
            if not image_name_match(name, image_path):
                continue
            return strutils.encode(image_path)
    return None

def clean_path(filepath):
    return os.path.normpath(os.path.relpath(strutils.decode(filepath)))


def filename_match(fsearch, filename, width, height):
    '''
    <nickname>@({width}x{height}|auto).(png|jpg|jpeg)
    '''
    fsearch = clean_path(fsearch)
    filename = clean_path(filename)
    if fsearch == filename:
        return True

    if fsearch.find('@') == -1:
        return False
    basename, fileext = os.path.splitext(fsearch)
    nickname, extinfo = basename.split('@', 1)
    if extinfo == 'auto':
        valid_names = {}.fromkeys([
            nickname+'@{}x{}'.format(width, height)+fileext,
            nickname+'@{}x{}'.format(height, width)+fileext,
            nickname+'.{}x{}'.format(width, height)+fileext,
            nickname+'.{}x{}'.format(height, width)+fileext,
        ])
        if filename in valid_names:
            return True
    # if extinfo.find('x') != -1:
    #     cw, ch = extinfo.split('x', 1)
    #     if cw*width == ch*height or cw*height == ch*width:
    #         return True
    return False


def lookup_image(fsearch, width=0, height=0):
    dirname = os.path.dirname(fsearch) or "."
    for file in os.listdir(dirname):
        filepath = os.path.join(dirname, file)
        if filename_match(fsearch, filepath, width, height):
            return filepath


def nameddict(name, props):
    """
    Point = nameddict('Point', ['x', 'y'])
    pt = Point(x=1, y=2)
    pt.y = 3
    print pt
    """
    class NamedDict(object):
        def __init__(self, *args, **kwargs):
            self.__store = {}.fromkeys(props)
            if args:
                for i, k in enumerate(props[:len(args)]):
                    self[k] = args[i]
            for k, v in kwargs.items():
                self[k] = v

        def __getattr__(self, key):
            # print '+', key
            if key.startswith('_NamedDict__'):
                return self.__dict__[key]
            else:
                return self.__store[key]

        def __setattr__(self, key, value):
            # print '-', key
            if key.startswith('_NamedDict__'):
                object.__setattr__(self, key, value)
            else:
                self.__setitem__(key, value)
                # self.__store[key] = value

        def __getitem__(self, key):
            return self.__store[key]

        def __setitem__(self, key, value):
            if key not in props:
                raise AttributeError("NamedDict(%s) has no attribute %s, avaliables are %s" % (
                    name, key, props))
            self.__store[key] = value

        def __dict__(self):
            return self.__store

        def __str__(self):
            return 'NamedDict(%s: %s)' % (name, str(self.__store))

    return NamedDict


if __name__ == '__main__':
    # print search_image('你好.png')
    # print search_image('oo')
    # print search_image()

    Point = nameddict('Point', ['x', 'y'])
    print(Point(2, 3, 4))
