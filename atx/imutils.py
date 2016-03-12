#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Some code reference
# https://github.com/jrosebr1/imutils
#

import sys
import cv2

import numpy as np
from PIL import Image

# import any special Python 2.7 packages
if sys.version_info.major == 2:
    from urllib import urlopen

# import any special Python 3 packages
elif sys.version_info.major == 3:
    from urllib.request import urlopen


def read_image(self, img):
    if isinstance(img, basestring):
        return cv2.imread(img)
    # FIXME(ssx): need support other types
    return img


def from_pillow(pil_image):
    """ Convert from pillow image to opencv """
    # convert PIL to OpenCV
    pil_image = pil_image.convert('RGB')
    cv2_image = np.array(pil_image)
    # Convert RGB to BGR 
    cv2_image = cv2_image[:, :, ::-1].copy()
    return cv2_image


def to_pillow(image):
    return Image.fromarray(image[:, :, ::-1])


def url_to_image(url, flag=cv2.IMREAD_COLOR):
    """ download the image, convert it to a NumPy array, and then read
    it into OpenCV format """
    resp = urlopen(url)
    image = np.asarray(bytearray(resp.read()), dtype="uint8")
    image = cv2.imdecode(image, flag)
    return image


def pil_to_opencv(pil_image):
    # convert PIL to OpenCV
    pil_image = pil_image.convert('RGB')
    cv2_image = np.array(pil_image)
    # Convert RGB to BGR 
    cv2_image = cv2_image[:, :, ::-1].copy()
    return cv2_image


if __name__ == '__main__':
    image = url_to_image('https://ss0.bdstatic.com/5aV1bjqh_Q23odCf/static/superman/img/logo/bd_logo1_31bdc765.png')
    cv2.imwrite('baidu.png', image)
    to_pillow(image).save('b2.png')
