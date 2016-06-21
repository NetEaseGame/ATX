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
