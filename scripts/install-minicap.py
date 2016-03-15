#! /usr/bin/env python
# -*- coding: utf-8 -*-
#
# Description: minicap setup scripts,
# Usage: python minicap_setup.py -s serialno -H host -P port
# Author: ydbn2153
# Created: 2016-03-15 ydbn2153

import argparse
import os
import sys
import shutil
import subprocess
import tempfile
import urllib
import functools


def log(msg):
    print '>>> ' + msg


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
    return check_output(cmdline, shell=False)


def minicap_setup(serialno=None, host=None, port=None):
    log("Minicap install started!")
    
    adb = functools.partial(run_adb, serialno=serialno, host=host, port=port)

    # Figure out which ABI and SDK
    log("Get device basic information ...")
    abi = adb('shell', 'getprop', 'ro.product.cpu.abi').strip()
    sdk = adb('shell', 'getprop', 'ro.build.version.sdk').strip()
    tmpdir = tempfile.mkdtemp(prefix='ins-minicap-')
    log("Make temp dir ...")
    print tmpdir
    try:
        log("Downloading minicap.so ....")
        url = "https://github.com/openstf/stf/raw/master/vendor/minicap/shared/android-"+sdk+"/"+abi+"/minicap.so"
        target_path = os.path.join(tmpdir, 'minicap.so')
        download(url, target_path)
        log("Push data to device ....")
        adb('push', target_path, '/data/local/tmp')
        
        log("Downloading minicap ....")
        url = "https://github.com/openstf/stf/raw/master/vendor/minicap/bin/"+abi+"/minicap"
        target_path = os.path.join(tmpdir, 'minicap')
        download(url, target_path)
        log("Push data to device ....")
        adb('push', target_path, '/data/local/tmp')
        adb('shell', 'chmod', '0755', '/data/local/tmp/minicap')

        log("Checking [dump device info] ...")
        print adb('shell', 'LD_LIBRARY_PATH=/data/local/tmp /data/local/tmp/minicap -i')
        log("Minicap install finished !")
    finally:
        if tmpdir:
            log("Cleaning temp dir")
            shutil.rmtree(tmpdir)


def download(url, target_path):
    return urllib.urlretrieve(url, target_path)
    

if __name__ == "__main__":
    parser = argparse.ArgumentParser("cli")
    parser.add_argument("-s", "--serialno", help="serialno of device", default=None)
    parser.add_argument("-H", "--host", help="host of remote device", default=None)
    parser.add_argument("-P", "--port", help="port of remote device", default=None)
    args = parser.parse_args(sys.argv[1:])
    minicap_setup(serialno=args.serialno, host=args.host, port=args.port)