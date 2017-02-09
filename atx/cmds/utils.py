#! /usr/bin/env python
# -*- coding: utf-8 -*-

import requests


def http_download(url, target_path):
    """Download file to local
    Args:
        - url(string): url request path
        - target_path(string): download destination
    """
    r = requests.get(url, stream=True)
    with open(target_path, 'wb') as f:
        # shutil.copyfileobj(resp, f)
        for chunk in r.iter_content(chunk_size=1024):
            if chunk:
                f.write(chunk)
    return target_path
