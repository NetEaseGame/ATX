#!/usr/bin/env python
# -*- coding: utf-8 -*-

from atx.drivers import Pattern


def test_pattern_offset():
    pt = Pattern("mixin.L50B50.png")
    assert pt.offset == (-0.5, 0.5)

    pt = Pattern("mixin.T50R50.png")
    assert pt.offset == (0.5, -0.5)

    pt = Pattern("mixin.T50R50.png")
    assert pt.offset == (0.5, -0.5)
