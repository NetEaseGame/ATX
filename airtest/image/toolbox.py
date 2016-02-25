#!/usr/bin/env python
# -*- coding: utf-8 -*-

import cv2
import numpy

def _readImage(FI, flag=cv2.IMREAD_COLOR):
    ''' FI can be cv2image or filename '''
    img = None
    if isinstance(FI, numpy.ndarray):
        img = FI.copy()
    if isinstance(FI, basestring):
        img = cv2.imread(FI, flag)
    assert img != None
    return img

def markPoint(image, (x, y)):
    img = _readImage(image)
    # cv2.rectangle(img, (x, y), (x+10, y+10), 255, 1, lineType=cv2.CV_AA)
    radius = 20
    cv2.circle(img, (x, y), radius, 255, thickness=2)
    cv2.line(img, (x-radius, y), (x+radius, y), 100) # x line
    cv2.line(img, (x, y-radius), (x, y+radius), 100) # y line
    return img

def markRectangle(image, left_top, (w, h)):
    img = _readImage(image)
    x, y = left_top
    cv2.rectangle(img, (x, y), (x+w, y+h), 255, 1, lineType=cv2.CV_AA)
    return img
    
def showImage(image):
    img = _readImage(image)
    cv2.imshow('image', img)
    cv2.waitKey(0)
    cv2.destroyAllWindows()

def _shape(image):
    ''' @return width and height or a image '''
    img = _readImage(image)
    w, h = img.shape[0], img.shape[1]
    return (w, h)

def markAndShow(image, (x, y), maxheight=500):
    img = markPoint(image, (x, y))
    w, h = _shape(img)
    if h > maxheight:
        scale = float(maxheight)/h
    img = cv2.resize(img, (0,0), fx=scale, fy=scale)
    showImage(img)

if __name__ == '__main__':
    img = _readImage('timer.png')
    # cv2.floodFill(img, None, (0, 0), (255, 255, 2), 0.1) 
    img = markPoint(img, (100, 100))
    img = markRectangle(img, (100, 100), (50, 50))
    showImage(img)