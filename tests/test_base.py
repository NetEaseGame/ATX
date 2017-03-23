#!/usr/bin/env python
# -*- coding: utf-8 -*-

from atx import base
from atx import strutils


def test_list_all_image():
    images = base.list_all_image('media')
    images = list(images)
    assert len(images) > 0
    #print list(images)
    #assert 'media/haima.png' in images or 'media\\haima.png' in images


def test_image_name_match():
    match = base.image_name_match
    assert match('foo.png', 'foo.png')
    assert match('./foo.png', 'foo.png')
    assert match('.//foo.png', './foo.png')
    assert match('foo', 'foo.png')
    assert match('foo', 'foo.PNG')
    assert match('foo', 'foo.jpg')
    assert match('foo', 'bar/foo.png')
    assert match('foo', 'bar/./foo.png')
    assert match('foo', 'foo@rsl(1280x720).png')
    assert match('foo', 'bar/foo@rsl(1280x720).png')
    assert match('./foo', 'bar/foo@rsl(1280x720).png')
    assert not match('foo.txt', 'foo.png')
    assert not match('foo.jpg', 'foo.png')
    assert not match('bar/foo', 'foo.jpg')


def test_search_image():
    imgpath = base.search_image('haima', path=['media'])
    assert imgpath is not None
    assert strutils.encode('haima.png') in imgpath
    assert strutils.encode('media') in imgpath


def test_filename_match():
    # @auto is supported
    assert base.filename_match('fight@auto.png', 'fight@4x3.png', 4, 3) == True
    assert base.filename_match('fight@auto.png', 'fight@4x3.png', 3, 4) == True
    assert base.filename_match('fight@auto.png', 'fight.4x3.png', 3, 4) == True
    assert base.filename_match('fight@auto.png', 'fight.3x4.png', 3, 4) == True

    assert base.filename_match('fight@auto.png', 'fight.16x9.png', 3, 4) == False
    assert base.filename_match('fight@auto.png', 'fight@16x9.png', 0, 0) == False

    # not support @wxh now
    assert base.filename_match('fight@3x4.png', 'fight@3x4.png', 3, 4) == True

    # normal
    assert base.filename_match('fight.png', 'fight.png', 3, 4) == True
    assert base.filename_match('fight.png', 'fight.png', 0, 0) == True
    assert base.filename_match('fight.png', 'fight.jpg', 0, 0) == False
    # assert base.filename_match('fight.3x4.png', 'fight.3x4.png', 3, 4) == True
    # assert base.filename_match('fight@auto.png', 'fight@4x3.png', 15, 20) == False


if __name__ == '__main__':
    test_filename_match()
