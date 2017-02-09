#! /usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import atexit
import os
import subprocess
import tempfile
import logging
import shutil

from atx.cmds.utils import http_download


__alias = {
    '9.3': '9.3 (13E230)', # 2016-05-04
}

# Can also be found in directory
IMAGE_BASE_DIR = '/Applications/Xcode.app/Contents/Developer/Platforms/iPhoneOS.platform/DeviceSupport/'
IMAGE_BASE_URL = 'http://gohttp.nie.netease.com/tools/tools-ios/DeveloperImages/'
logger = logging.getLogger('ios')


def init():
    ch = logging.StreamHandler()
    fmt = "%(asctime)s [%(name)s:%(lineno)4s] %(message)s"
    formatter = logging.Formatter(fmt)
    ch.setFormatter(formatter)
    logger.addHandler(ch)
    logger.setLevel(logging.DEBUG)


def check_output(cmds, shell=False):
    try:
        output = subprocess.check_output(cmds, stderr=subprocess.STDOUT, shell=shell)
        return output
    except subprocess.CalledProcessError as e:
        logger.warn('Failed to run command: %s', ' '.join(cmds))
        logger.warn('Error output:\n%s', e.output)
        raise


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
        r'C:\Program Files\Quamotion\iMobileDevice',
        r'D:\Program Files\Quamotion\iMobileDevice',
        r'E:\Program Files\Quamotion\iMobileDevice',
    ]
    filepath = look_path(name+ext, search_paths)
    __execpath[name] = filepath
    return filepath


def idevice(name, *args):
    exec_name = 'idevice' + name
    exec_path = look_exec(exec_name)
    if not exec_path:
        raise EnvironmentError('Necessary binary ("%s") not found.' % exec_name)
    return check_output([exec_path] + list(args))


def devices():
    udids = [udid.strip() for udid in idevice('_id', '-l').splitlines() if udid.strip()]
    return {udid: idevice('name', '-u', udid).decode('utf-8').strip() for udid in udids}


def device_product_version(udid):
    return idevice('info', '-u', udid, '-k', 'ProductVersion').strip()


def download(filename, tmpdir, version, base_url=IMAGE_BASE_URL):
    if sys.platform == 'darwin':
        version = __alias.get(version, version)
        abs_path = os.path.join(IMAGE_BASE_DIR, version, filename)
        if os.path.exists(abs_path):
            return abs_path
    target_path = os.path.join(tmpdir, filename)
    source_url = base_url + '/'.join([version, filename])
    logger.info("Download %s/%s", version, filename)
    return http_download(source_url, target_path)


def select_device():
    devs = devices()
    if len(devs) == 0:
        raise EnvironmentError('iPhone device is not attached.')
    if len(devs) > 1:
        raise EnvironmentError('More than one iPhone device detected.')

    udid = devs.keys()[0]
    devname = devs[udid]
    return udid, devname


def is_mounted(udid):
    return 'ImagePresent: true' in idevice('imagemounter', '-l', '-u', udid)


def mount_image(udid, image_file, image_signature_file):
    if is_mounted(udid):
        logger.info("Developer image has already mounted.")
        return
    idevice('imagemounter', '-u', udid, image_file, image_signature_file)    
    logger.info("^_^ Developer image has been mounted.")


def check_enviroment():
    return look_exec('idevice_id') is not None
        

def main(udid=None):
    init()

    if not check_enviroment():
        sys.exit("No imobiledevice found in $PATH, but you can download from here\n\n    %s" %(
            "http://quamotion.mobi/iMobileDevice/Download",))

    logger.info("Make tmp dir ...")
    tmpdir = tempfile.mkdtemp(prefix='atx-ios-developer-')
    if not tmpdir:
        logger.warn("tmpdir create failed.")
        sys.exit(1)

    @atexit.register
    def _clean():
        logger.info("Cleaning tmp dir: %s", tmpdir)
        shutil.rmtree(tmpdir)

    udid, devname = select_device()
    long_version = device_product_version(udid)
    version = '.'.join(long_version.split('.')[:2])
    logger.info("Device udid is %s", udid)
    logger.info("Device name is %s", devname)
    logger.info("Device version is %s", long_version)
    
    if is_mounted(udid):
        logger.info("<O_O> Developer Image has already mounted.")
        return

    image_file = download('DeveloperDiskImage.dmg', tmpdir, version)
    image_signature_file = download('DeveloperDiskImage.dmg.signature', tmpdir, version)

    mount_image(udid, image_file, image_signature_file)
