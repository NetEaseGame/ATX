#!/usr/bin/env python
# coding: utf-8

from androguard.core.bytecodes import apk


def parse_apk(filename):
    '''
    Returns:
        (package, activity)
    '''
    a = apk.APK(filename)
    
    return (a.get_package(), a.get_main_activity())