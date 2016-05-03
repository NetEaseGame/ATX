#! /usr/bin/env python
# -*- coding: utf-8 -*-

import urllib2
import shutil
import os
import subprocess
import commands
import sys


def http_download(url, target_path):
    """Download file to local
    Args:
        - url(string): url request path
        - target_path(string): download destination

    Raises:
        IOError
        urllib2.URLError
    """
    try:
        resp = urllib2.urlopen(url)
    except urllib2.URLError, e:
        if not hasattr(e, 'code'):
            raise
        resp = e
    if resp.code != 200:
        raise IOError("Request url(%s) expect 200 but got %d" %(url, resp.code))

    with open(target_path, 'wb') as f:
        shutil.copyfileobj(resp, f)
    return target_path


# def run_cmd(*args, **kwargs):
#     """Run command and send stdout,stderr to console
#     Args:
#         ...command: ex   adb, devices
#         success_text(string): expect output must contains

#     Return:
#         exit code
#     """
#     output = subprocess.check_output(list(args))

#     success_text = kwargs.pop('success_text', None)
#     if success_text and output.find(success_text) == -1:
#         return 3
#     return 0
