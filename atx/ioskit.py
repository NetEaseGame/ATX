#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import

import functools
import os
import sys
import subprocess32 as subprocess
import tempfile
import inspect
import plistlib

from PIL import Image
from atx import logutils


logger = logutils.getLogger(__name__)

def look_path(name, search_paths=[], env_path=True):
    os.pathsep
    if env_path:
        search_paths += os.getenv('PATH').split(os.pathsep)
    for directory in search_paths:
        if not os.path.isdir(directory):
            continue
        filepath = os.path.join(directory, name)
        if os.path.isfile(filepath):
            return filepath
    return None


__execpath = {}

def look_exec(name):
    if __execpath.get(name):
        return __execpath[name]

    ext = '.exe' if os.name == 'nt' else ''
    search_paths = [
        r'C:\Program Files (x86)\Quamotion\iMobileDevice',
        r'D:\Program Files (x86)\Quamotion\iMobileDevice',
        r'E:\Program Files (x86)\Quamotion\iMobileDevice',
        r'F:\Program Files (x86)\Quamotion\iMobileDevice',
        r'C:\Program Files\Quamotion\iMobileDevice',
        r'D:\Program Files\Quamotion\iMobileDevice',
        r'E:\Program Files\Quamotion\iMobileDevice',
        r'F:\Program Files\Quamotion\iMobileDevice',
    ]
    filepath = look_path(name+ext, search_paths)
    __execpath[name] = filepath
    return filepath


def must_look_exec(name):
    filepath = look_exec(name)
    if not filepath:
        raise EnvironmentError('No "%s" found.' % filepath)
    return filepath


def check_output(cmds, shell=False):
    try:
        output = subprocess.check_output(cmds, stderr=subprocess.STDOUT, shell=shell)
        return output
    except subprocess.CalledProcessError:
        # logger.warn('Failed to run command: %s', ' '.join(cmds))
        # logger.warn('Error output:\n%s', e.output)
        raise


def idevice(name, *args):
    exec_name = 'idevice' + name
    exec_path = look_exec(exec_name)
    if not exec_path:
        raise EnvironmentError('Necessary binary ("%s") not found.' % exec_name)

    cmds = [exec_path] + list(args)
    try:
        output = subprocess.check_output(cmds, stderr=subprocess.STDOUT, shell=False)
        return output
    except subprocess.CalledProcessError:
        raise

def devices():
    """
    Return device dict
    For example:
    {
        "1002038889199992134bad1234112312": "Tony's iPhone"
    }
    """
    udids = [udid.strip() for udid in idevice('_id', '-l').splitlines() if udid.strip()]
    return {udid: idevice('name', '-u', udid).decode('utf-8').strip() for udid in udids}

# def device_product_version(udid):
#     return idevice('info', '-u', udid, '-k', 'ProductVersion').strip()


def memory_last(fn):
    @functools.wraps(fn)
    def inner(*args, **kwargs):
        func_args = inspect.getcallargs(fn, *args, **kwargs)
        self = func_args.get('self')
        store_name = '__'+fn.__name__
        
        if hasattr(self, store_name):
            return getattr(self, store_name)
        ret = fn(*args, **kwargs)
        setattr(self, store_name, ret)
        return ret
    return inner


class Device(object):
    def __init__(self, udid=None):
        if not udid:
            devs = devices()
            if len(devs) == 0:
                raise EnvironmentError("No iOS devices connected.")
            elif len(devs) > 1:
                raise EnvironmentError("More than one device connected, need to specify udid")
            else:
                udid = devs.keys()[0]
        self._udid = udid
        self.__product_version = None

    @property
    def udid(self):
        return self._udid

    @property
    @memory_last
    def product_version(self):
        return idevice('info', '-u', self.udid, '-k', 'ProductVersion').strip()

    @property
    @memory_last
    def name(self):
        return idevice('name', '-u', self.udid).decode('utf-8').strip()

    @property
    @memory_last
    def info(self):
        return plistlib.readPlistFromString(idevice('info', '--xml', '--udid', self.udid))

    def screenshot(self, filename=None):
        """
        Return:
            PIL.Image
            
        Raises:
            EnvironmentError
        """
        tmpfile = tempfile.mktemp(prefix='atx-screencap-', suffix='.tiff')
        try:
            idevice("screenshot", "--udid", self.udid, tmpfile)
        except subprocess.CalledProcessError as e:
            sys.exit(e.message)

        try:
            image = Image.open(tmpfile)
            image.load()
            if filename:
                image.save(filename)
            return image
        finally:
            if os.path.exists(tmpfile):
                os.unlink(tmpfile)

    def start_app(self, bundle_id):
        '''
        Start app by bundle_id
        Args:
            - bundle_id(string): ex com.netease.my
        Returns:
            idevicedebug subprocess instance
        '''
        idevicedebug = must_look_exec('idevicedebug')

        # run in background
        kwargs = {'stdout': subprocess.PIPE, 'stderr': subprocess.PIPE}
        if sys.platform != 'darwin':
            kwargs['close_fds'] = True
        return subprocess.Popen([idevicedebug, "--udid", self.udid, 'run', bundle_id], **kwargs)

    def install(self, filepath):
        ''' TODO(ssx): not tested. '''
        if not os.path.exists(filepath):
            raise EnvironmentError('file "%s" not exists.' % filepath)

        ideviceinstaller = must_look_exec('ideviceinstaller')
        os.system(subprocess.list2cmdline([ideviceinstaller, '-u', self.udid, '-i', filepath]))


if __name__ == '__main__':
    devices()
    dev = Device()
    print dev.screenshot('i.png')
    print dev.product_version
    print dev.product_version
    print dev.name
