#! /usr/bin/env python
# -*- coding: utf-8 -*-

import json
import atx


def main(serial, host, port):
    d = atx.connect(serial, host=host, port=port)
    props = d.properties
    (w, h) = d.display
    info = {
        'serial': d.serial,
        'product.model': props['ro.product.model'],
        'product.brand': props.get('ro.product.brand'),
        'sys.country': props.get('persist.sys.country'),
        'display': '%dx%d' % (w, h),
        'version.sdk': int(props.get('ro.build.version.sdk', 0)),
        'version.release': props.get('ro.build.version.release'),
        'product.cpu.abi': props.get('ro.product.cpu.abi'),
    }
    print(json.dumps(info, indent=4))
