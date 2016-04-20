#!/usr/bin/env python
# -*- coding: utf-8 -*-

from atx import base


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
    assert 'haima.png' in imgpath
    assert 'media' in imgpath
