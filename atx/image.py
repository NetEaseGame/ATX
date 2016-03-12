#!/usr/bin/env python
# -*- coding: utf-8 -*-

import numpy as np
import aircv as ac
from PIL import Image


def read_image(self, img):
    if isinstance(img, basestring):
        return ac.imread(img)
    # FIXME(ssx): need support other types
    return img


def pil_to_opencv(pil_image):
    # convert PIL to OpenCV
    pil_image = pil_image.convert('RGB')
    cv2_image = np.array(pil_image)
    # Convert RGB to BGR 
    cv2_image = cv2_image[:, :, ::-1].copy()
    return cv2_image