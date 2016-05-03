#! /usr/bin/env python
# -*- coding: utf-8 -*-
#
# Description: minicap setup scripts,
# Usage: python minicap_setup.py -s serialno -H host -P port
# Author: ydbn2153
# Created:  ydbn2153 <2016-03-15>
# Modified: hzsunshx <2016-03-19>

import argparse
import os
import sys
import shutil
import subprocess
import tempfile
import urllib
import functools

from atx import logutils
from atx.cmds.utils import http_download

logger = logutils.getLogger('minicap')


def log(*args):
    logger.info(*args)


def check_output(cmdstr, shell=True):
    output = subprocess.check_output(cmdstr, stderr=subprocess.STDOUT, shell=shell)
    return output


def run_adb(*args, **kwargs):
    cmds = ['adb']
    serialno = kwargs.get('serialno', None)
    if serialno:
        cmds.extend(['-s', serialno])
    host = kwargs.get('host')
    if host:
        cmds.extend(['-H', host])
    port = kwargs.get('port')
    if port:
        cmds.extend(['-P', str(port)])
    cmds.extend(args)
    cmds = map(str, cmds)
    cmdline = subprocess.list2cmdline(cmds)
    try:
        return check_output(cmdline, shell=False)
    except Exception, e:
        raise EnvironmentError('run cmd: {} failed. {}'.format(cmdline, e))


def install(serialno=None, host=None, port=None):
    logger.info("Minicap install started!")
    
    adb = functools.partial(run_adb, serialno=serialno, host=host, port=port)

    # Figure out which ABI and SDK
    logger.info("Make temp dir ...")
    tmpdir = tempfile.mkdtemp(prefix='ins-minicap-')
    logger.debug(tmpdir)
    try:
        logger.info("Retrive device information ...")
        abi = adb('shell', 'getprop', 'ro.product.cpu.abi').strip()
        sdk = adb('shell', 'getprop', 'ro.build.version.sdk').strip()

        logger.info("Downloading minicap.so ....")
        url = "https://github.com/openstf/stf/raw/master/vendor/minicap/shared/android-"+sdk+"/"+abi+"/minicap.so"
        target_path = os.path.join(tmpdir, 'minicap.so')
        http_download(url, target_path)
        logger.info("Push data to device ....")
        adb('push', target_path, '/data/local/tmp')
        
        logger.info("Downloading minicap ....")
        url = "https://github.com/openstf/stf/raw/master/vendor/minicap/bin/"+abi+"/minicap"
        target_path = os.path.join(tmpdir, 'minicap')
        http_download(url, target_path)
        logger.info("Push data to device ....")
        adb('push', target_path, '/data/local/tmp')
        adb('shell', 'chmod', '0755', '/data/local/tmp/minicap')

        logger.info("Checking [dump device info] ...")
        print adb('shell', 'LD_LIBRARY_PATH=/data/local/tmp /data/local/tmp/minicap -i')
        logger.info("Minicap install finished !")
    except Exception, e:
        logger.error(e)
    finally:
        if tmpdir:
            logger.info("Cleaning temp dir")
            shutil.rmtree(tmpdir)
    

if __name__ == "__main__":
    parser = argparse.ArgumentParser("cli")
    parser.add_argument("-s", "--serialno", help="serialno of device", default=None)
    parser.add_argument("-H", "--host", help="host of remote device", default=None)
    parser.add_argument("-P", "--port", help="port of remote device", default=None)
    args = parser.parse_args(sys.argv[1:])
    install(serialno=args.serialno, host=args.host, port=args.port)
