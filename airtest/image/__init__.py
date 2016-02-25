#!/usr/bin/env python
# -*- coding: utf-8 -*-

# import auto
# import template
# import sift

import cv2

_sift = cv2.SIFT()

def _cv2open(filename, arg=1):
    if isinstance(filename, basestring):
        obj = cv2.imread(filename, arg)
    else:
        obj = filename
    return obj

def sift_point_count(image_file):
    im = _cv2open(image_file)
    if im == None:
        return 0
    kp_sch, des_sch = _sift.detectAndCompute(im, None)
    return len(kp_sch)

# def find(img, template, rect=None, method='auto'):
#     '''
#     @return rect, ratio 
#     '''
#     pass

def _testmain():
    print sift_point_count('testdata/hand.png')

if __name__ == '__main__':
    _testmain()