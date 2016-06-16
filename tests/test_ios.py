#!/usr/bin/env python
# coding: utf-8

import atx


def test_ios_screenshot():
	d = atx.connect(platform='ios')
	d.screen_rotation = 1
	print d.screenshot().save("yes.png")


if __name__ == '__main__':
	test_ios_screenshot()