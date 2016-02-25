#!/usr/bin/env python
# -*- coding: utf-8 -*-

# export PYTHONPATH=/z/workspace/airtest

import airtest
import pytest

def test_android_getsysinfo():
    devs = airtest.getDevices()
    if not devs:
        pytest.skip('not devices detected')
    if devs:
        phoneNo, phoneType = devs[0]
    print phoneNo
    app = airtest.connect(phoneNo, device='android')
    print app.dev.getdevinfo()
