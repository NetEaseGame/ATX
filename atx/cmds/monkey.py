#! /usr/bin/env python
# -*- coding: utf-8 -*-

import random

import atx
import cv2
from atx import imutils


# codeskyblue by 2016-05-03
# 过新手流程倒是挺容易的，不过还是有好多东西识别不出来，比如退出键，阴影下的属性切换键
# 还需要结合其他的方法继续去弄

def choose_point(frame):
    h, w = frame.shape[:2]
    framesize = h*w
    minarea = framesize/1000
    print 'minarea:', minarea

    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    cv2.imshow('hsv', hsv)
    H, S, V = cv2.split(hsv)
    V[V<200] = 0
    # cv2.imshow('H', H)
    # cv2.imshow('S', S)
    cv2.imshow('V', V)

    mask = V
    mask = cv2.dilate(mask, None, iterations=2)
    # mask = cv2.erode(mask, None, iterations=2)
    cv2.imshow('mask', mask)

    (cnts, _) = cv2.findContours(mask.copy(), cv2.RETR_EXTERNAL,
        cv2.CHAIN_APPROX_SIMPLE)

    points = []
    for c in cnts:
        # if the contour is too small, ignore it
        area = cv2.contourArea(c)
        print area
        if area < minarea:
            continue
        if area > framesize/2:
            continue
        # if cv2.contourArea(c) < minarea:
            # continue

        # compute the bounding box for the contour, draw it on the frame,
        # and update the text
        # 计算轮廓的边界框，在当前帧中画出该框
        (x, y, w, h) = cv2.boundingRect(c)
        points.append((x, y, w, h))
        cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
        # text = "Occupied"

    # random pick point
    if not points:
        return None
    pt = random.choice(points)
    (x, y, w, h) = pt
    cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 0, 255), 2)
    cv2.imshow('frame', frame)
    return (x+w/2, y+h/2)
    # cv2.waitKey(0)


def main(serial=None, host=None, port=None):
    d = atx.connect(serial, host=host, port=port)
    while True:
        pilimg = d.screenshot()
        cv2img = imutils.from_pillow(pilimg)
        # cv2img = cv2.imread('tmp.png')
        # cv2.imwrite('tmp.png', cv2img)
        cv2img = cv2.resize(cv2img, fx=0.5, fy=0.5, dsize=(0, 0))
        pt = choose_point(cv2img)
        print 'click:', pt
        if pt:
            x, y = pt
            d.click(2*x, 2*y)
        cv2.waitKey(100)
        # import time
        # time.sleep(0.1)