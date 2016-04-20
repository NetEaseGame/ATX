# coding: utf-8

from __future__ import absolute_import

import collections

from atx import imutils
from atx import strutils


FindPoint = collections.namedtuple('FindPoint', ['pos', 'confidence', 'method', 'matched'])
Display = collections.namedtuple('Display', ['width', 'height'])


__boundstuple = collections.namedtuple('Bounds', ['left', 'top', 'right', 'bottom'])
class Bounds(__boundstuple):
    def __init__(self, *args, **kwargs):
        super(Bounds, self).__init__(*args, **kwargs)
        self._area = None

    def is_inside(self, x, y):
        v = self
        return x > v.left and x < v.right and y > v.top and y < v.bottom

    @property
    def area(self):
        if not self._area:
            v = self
            self._area = (v.right-v.left) * (v.bottom-v.top)
        return self._area

    @property
    def center(self):
        v = self
        return (v.left+v.right)/2, (v.top+v.bottom)/2

    def __mul__(self, mul):
        return Bounds(*(int(v*mul) for v in self))


class Pattern(object):
    def __init__(self, image, offset=(0, 0), anchor=0, rsl=None, resolution=None):
        """
        Args:
            image: image filename or image URL
            offset: offset of image center
            anchor: not supported
            resolution: image origin screen resolution
            rsl: alias of resolution
        """
        self._name = image if isinstance(image, basestring) else 'unknown'
        self._image = imutils.open(image)
        self._offset = offset
        self._resolution = rsl or resolution
        if isinstance(image, basestring):
            self._name = image

    def __str__(self):
        return 'Pattern(name: {}, offset: {})'.format(strutils.encode(self._name), self.offset)
    
    @property
    def image(self):
        return self._image

    @property
    def offset(self):
        return self._offset

    @property
    def resolution(self):
        return self._resolution