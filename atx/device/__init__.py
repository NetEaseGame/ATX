# coding: utf-8

from __future__ import absolute_import

import collections

import cv2
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
    def __init__(self, name, image=None, offset=(0, 0), anchor=0, rsl=None, resolution=None, th=None, threshold=None):
        """
        Args:
            name: image filename
            image: opencv image object
            offset: offset of image center
            anchor: not supported
            resolution: image origin screen resolution
            rsl: alias of resolution
            threshold: image match threshold, usally (0, 1]
            th: alias of threshold
        """
        self._name = name # better to be the image path
        self._image = image # if image is None, it will delay to pattern_open function
        self._offset = offset
        self._resolution = rsl or resolution
        self._threshold = th or threshold
        if isinstance(image, basestring):
            self._name = image

    def __str__(self):
        return 'Pattern(name: {}, offset: {})'.format(strutils.encode(self._name), self.offset)

    def save(self, path):
        """ save image to path """
        cv2.imwrite(path, self._image)
    
    @property
    def image(self):
        return self._image

    @property
    def offset(self):
        return self._offset

    @property
    def resolution(self):
        return self._resolution

    @property
    def threshold(self):
        return self._threshold
