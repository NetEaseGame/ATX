#!/usr/bin/env python
# -*- coding: utf-8 -*-


import platform

from airtest import base

def test_exec_cmd():
    if platform.system() == 'Linux':
        base.exec_cmd('echo', 'hello')

def test_exec_cmd_shell():
    base.exec_cmd('echo hello', shell=True)

def test_check_output():
    output = base.check_output('echo hello')
    assert output.rstrip() == 'hello'

