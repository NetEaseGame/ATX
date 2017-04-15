#!/usr/bin/env python
# -*- coding: utf-8 -*-

from atx import strutils
import six


def test_encode():
    v = strutils.encode('hello')
    assert not isinstance(v, six.text_type)

    v = strutils.encode(u'hello')
    assert not isinstance(v, six.text_type)


def test_to_string():
    v = strutils.to_string('hello')
    assert isinstance(v, str) # no matter py2 or py3
