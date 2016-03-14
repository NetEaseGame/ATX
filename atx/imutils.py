#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Some code reference
# https://github.com/jrosebr1/imutils
#

import re
import os
import sys
import cv2

import numpy as np
from PIL import Image
from StringIO import StringIO

# import any special Python 2.7 packages
if sys.version_info.major == 2:
    from urllib import urlopen

# import any special Python 3 packages
elif sys.version_info.major == 3:
    from urllib.request import urlopen


__sys_open = open


def open(image):
    if isinstance(image, basestring):
        name = image
        if re.match(r'^https?://', name):
            return url_to_image(name)
        if os.path.isfile(name):
            img = cv2.imread(name)
            if img is None:
                raise IOError("Image format error: %s" % name)
            return img
        raise IOError("Open image(%s) not found" % name)

    return image

def open_as_pillow(filename):
    """ This way can delete file immediately """
    with __sys_open(filename, 'rb') as f:
        data = StringIO(f.read())
        return Image.open(data)


def from_pillow(pil_image):
    """ Convert from pillow image to opencv """
    # convert PIL to OpenCV
    pil_image = pil_image.convert('RGB')
    cv2_image = np.array(pil_image)
    # Convert RGB to BGR 
    cv2_image = cv2_image[:, :, ::-1].copy()
    return cv2_image


def to_pillow(image):
    return Image.fromarray(image[:, :, ::-1].copy())

    # There is another way
    # img_bytes = cv2.imencode('.png', image)[1].tostring()
    # return Image.open(StringIO(img_bytes))

def url_to_image(url, flag=cv2.IMREAD_COLOR):
    """ download the image, convert it to a NumPy array, and then read
    it into OpenCV format """
    resp = urlopen(url)
    image = np.asarray(bytearray(resp.read()), dtype="uint8")
    image = cv2.imdecode(image, flag)
    return image


def crop(image, left=0, top=0, right=None, bottom=None):
    (h, w) = image.shape[:2]
    if bottom is None:
        bottom = h
    if right is None:
        right = w
    return image[top:bottom, left:right]


if __name__ == '__main__':
    # image = open('https://ss0.bdstatic.com/5aV1bjqh_Q23odCf/static/superman/img/logo/bd_logo1_31bdc765.png')
    image = open('baidu.png')
    image = open(image)
    # cv2.imwrite('baidu.png', image)
    print image.shape
    image = crop(image, bottom=200, top=100, left=50, right=200)
    print image.shape
    cv2.imwrite('tmp.png', image)
    # to_pillow(image).save('b2.png')
