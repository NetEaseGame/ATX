#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import pytest
import string

import cv2
from atx import imutils


def test_mark_point():
    im = cv2.imread('media/system-app.png')
    im = imutils.mark_point(im, 50, 50)
    cv2.imwrite('tmp.png', im)