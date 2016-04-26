#! /usr/bin/env python
# -*- coding: utf-8 -*-

import atexit
import tempfile
import subprocess32 as subprocess
import shutil
import urllib2
import re
import os

import atx.androaxml as apkparse

from atx import logutils
from atx.cmds import cmdutils


log = logutils.getLogger('install')
DEFAULT_REMOTE_PATH = '/data/local/tmp/_atx_ins_tmp.apk'


def clean(tmpdir):
    log.info('Remove temp directory')
    shutil.rmtree(tmpdir)


def adb_pushfile(filepath, remote_path):
    filesize = os.path.getsize(filepath)
    p = subprocess.Popen(['adb', 'push', filepath, remote_path],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    while True:
        try:
            p.wait(0.5)
        except subprocess.TimeoutExpired:
            log.info("Progress %dM/%dM", get_file_size(remote_path) >>20, filesize >>20)
            pass
        except KeyboardInterrupt:
            p.kill()
            raise
        except:
            raise
        else:
            log.info("Success pushed into device")
            break


def get_file_size(remote_path):
    output = subprocess.check_output(['adb', 'shell', 'ls', '-l', remote_path])
    m = re.search(r'(\d+)', output)
    if not m:
        return 0
    return int(m.group(1))


def adb_cmd(*args):
    cmd_args = ['adb'] + list(args)
    p = subprocess.Popen(cmd_args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return p


def adb_remove(path):
    status, output = adb_call('shell', 'rm', path)
    if output:
        log.warn('%s', output)


def adb_call(*args):
    p = adb_cmd(*args)
    exit_code = p.wait()
    output = p.stdout.read()
    return exit_code, output


def adb_install(remote_path):
    return cmdutils.run_cmd('adb', 'shell', 'pm', 'install', '-rt', remote_path, success_text='Success')


def main(args):
    path = args.path
    if re.match(r'^https?://', path):
        tmpdir = tempfile.mkdtemp(prefix='atx-install-')
        atexit.register(clean, tmpdir)
        log.info("Create temp directory: %s", tmpdir)

        urlpath = path
        target = os.path.join(tmpdir, '_tmp.apk')
        path = target
        log.info("Download from: %s", urlpath)
        cmdutils.http_download(urlpath, target)

    package_name, main_activity = apkparse.parse_apk(path)
    log.info("APK package name: %s", package_name)
    log.info("APK main activity: %s", main_activity)

    log.info("Push file to android device")
    adb_pushfile(path, DEFAULT_REMOTE_PATH)

    log.info("Install ..., will take a few seconds")
    adb_install(DEFAULT_REMOTE_PATH)
    log.info("Done")
    adb_remove(DEFAULT_REMOTE_PATH)
