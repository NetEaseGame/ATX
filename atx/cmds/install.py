#! /usr/bin/env python
# -*- coding: utf-8 -*-

import atexit
import os
import re
import shutil
import sys
import time
import tempfile

import tqdm

from atx import logutils
from atx import adbkit
from atx.cmds import utils

try:
    import subprocess32 as subprocess
except:
    import subprocess


log = logutils.getLogger('install')
DEFAULT_REMOTE_PATH = '/data/local/tmp/_atx_tmp.apk'
__apks = {
    'utf7ime': 'http://o8oookdsx.qnssl.com/android_unicode_ime-debug.apk',
    'atx-assistant': 'https://o8oookdsx.qnssl.com/atx-assistant-1.0.4.apk',
}


def clean(tmpdir):
    log.info('Remove temp directory')
    shutil.rmtree(tmpdir)


def adb_pushfile(adb, filepath, remote_path):
    filesize = os.path.getsize(filepath)
    pb = tqdm.tqdm(unit='B', unit_scale=True, total=filesize)
    p = adb.raw_cmd('push', filepath, remote_path)

    while True:
        try:
            p.wait(0.5)
        except subprocess.TimeoutExpired:
            pb.n = get_file_size(adb, remote_path)
            pb.refresh()
            # log.info("Progress %dM/%dM", get_file_size(remote_path) >>20, filesize >>20)
            pass
        except (KeyboardInterrupt, SystemExit):
            p.kill()
            raise
        except:
            raise
        else:
            # log.info("Success pushed into device")
            break
    pb.close()


def get_file_size(adb, remote_path):
    try:
        output = adb.run_cmd('shell', 'ls', '-l', remote_path)
        m = re.search(r'\s(\d+)', output)
        if not m:
            return 0
        return int(m.group(1))
    except subprocess.CalledProcessError as e:
        log.warn("call error: %s", e)
        time.sleep(.1)
        return 0


def adb_remove(adb, path):
    p = adb.raw_cmd('shell', 'rm', path)
    stdout, stderr = p.communicate()
    if stdout or stderr:
        log.warn('%s\n%s', stdout, stderr)


def adb_install(adb, remote_path):
    stdout = adb.run_cmd('shell', 'pm', 'install', '-rt', remote_path)
    # stdout, _ = p.communicate()
    if stdout.find('Success') == -1:
        raise IOError("Adb install failed: %s" % stdout)


def adb_must_install(adb, remote_path, package_name):
    try:
        adb_install(adb, remote_path)
    except IOError:
        log.info("Remove already installed app: %s", package_name)
        adb.raw_cmd('uninstall', package_name).wait()
        adb_install(adb, remote_path)


def main(path, serial=None, host=None, port=None, start=False):
    adb = adbkit.Client(host, port).device(
        serial)  # adbutils.Adb(serial, host, port)

    # use qiniu paths
    if __apks.get(path):
        path = __apks.get(path)

    if re.match(r'^https?://', path):
        tmpdir = tempfile.mkdtemp(prefix='atx-install-')
        log.info("Create temp directory: %s", tmpdir)

        # FIXME(ssx): will not called when Ctrl+C pressed in windows git-bash
        atexit.register(clean, tmpdir)

        urlpath = path
        target = os.path.join(tmpdir, '_tmp.apk')
        path = target
        log.info("Download from: %s", urlpath)
        utils.http_download(urlpath, target)

    import atx.apkparse as apkparse
    manifest = apkparse.parse_apkfile(path)
    log.info("APK package name: %s", manifest.package_name)
    log.info("APK main activity: %s", manifest.main_activity)

    log.info("Push file to android device")
    adb_pushfile(adb, path, DEFAULT_REMOTE_PATH)

    log.info("Install ..., will take a few seconds")
    adb_must_install(adb, DEFAULT_REMOTE_PATH, manifest.package_name)
    log.info("Remove _tmp.apk")
    adb_remove(adb, DEFAULT_REMOTE_PATH)

    if start:
        log.info("Start app '%s'" % manifest.package_name)
        adb.raw_cmd('shell', 'am', 'start', '-n',
                    manifest.package_name+'/'+manifest.main_activity).wait()
    log.info("Success")
