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
import base64

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


def _open_data_url(data, flag=cv2.IMREAD_COLOR):
    pos = data.find('base64,')
    if pos == -1:
        raise IOError("data url is invalid, head %s" % data[:20])

    pos += len('base64,')
    raw_data = base64.decodestring(data[pos:])
    image = np.asarray(bytearray(raw_data), dtype="uint8")
    image = cv2.imdecode(image, flag)
    return image


def open(image):
    '''
    Args:
        - image: support many type. filepath or url or data:image/png:base64
    Return:
        Pattern
    Raises
        IOError
    '''
    if isinstance(image, basestring):
        name = image
        if name.startswith('data:image/'):
            return _open_data_url(name)
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

def diff_rect(img1, img2, pos=None):
    """find counters include pos in differences between img1 & img2 (cv2 images)"""
    diff = cv2.absdiff(img1, img2)
    diff = cv2.GaussianBlur(diff, (3, 3), 0)
    edges = cv2.Canny(diff, 100, 200)
    _, thresh = cv2.threshold(edges, 0, 255, cv2.THRESH_BINARY)
    contours, _ = cv2.findContours(thresh, cv2.RETR_TREE, cv2.CHAIN_APPROX_NONE)
    if not contours:
        return None
    contours.sort(key=lambda c: len(c))
    # no pos provide, just return the largest different area rect
    if pos is None:
        cnt = contours[-1]
        x0, y0, w, h = cv2.boundingRect(cnt)
        x1, y1 = x0+w, y0+h
        return (x0, y0, x1, y1)
    # else the rect should contain the pos
    x, y = pos
    for i in range(len(contours)):
        cnt = contours[-1-i]
        x0, y0, w, h = cv2.boundingRect(cnt)
        x1, y1 = x0+w, y0+h
        if x0 <= x <= x1 and y0 <= y <= y1:
            return (x0, y0, x1, y1)

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
