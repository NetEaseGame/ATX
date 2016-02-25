#!/usr/bin/env python
# -*- coding: utf-8 -*-

import cv2
from airtest.image import toolbox

DEBUG = False

def _cv2open(filename, arg=1):
    if isinstance(filename, basestring):
        obj = cv2.imread(filename, arg)
    else:
        obj = filename
    if obj == None:
        raise IOError('cv2 read file error:'+filename)
    return obj

def find(search_file, image_file, threshold=0.8):
    '''
    Locate image position

    same as findall, except without arg maxcnt
    '''
    point = findall(search_file, image_file, threshold, maxcnt=1)
    return point[0] if point else None

def findall(search_file, image_file, threshold=0.8, maxcnt = 0, rgb=False, bgremove=False):
    '''
    Locate image position with cv2.templateFind

    Use pixel match to find pictures.

    Args:
        search_file(string): filename of search object
        image_file(string): filename of image to search on
        threshold: optional variable, to ensure the match rate should >= threshold
        maxcnt: maximun count of searched points

    Returns:
        A tuple of found points ((x, y), ...)

    Raises:
        IOError: when file read error
    '''
    # method = cv2.TM_CCORR_NORMED
    # method = cv2.TM_SQDIFF_NORMED
    method = cv2.TM_CCOEFF_NORMED

    search = _cv2open(search_file)
    image_  = _cv2open(image_file)
    if rgb:
        s_bgr = cv2.split(search) # Blue Green Red
        i_bgr = cv2.split(image_)
        weight = (0.3, 0.3, 0.4)
        resbgr = [0, 0, 0]
        for i in range(3): # bgr
            resbgr[i] = cv2.matchTemplate(i_bgr[i], s_bgr[i], method)
        res = resbgr[0]*weight[0] + resbgr[1]*weight[1] + resbgr[2]*weight[2]
    else:
        s_gray = cv2.cvtColor(search, cv2.COLOR_BGR2GRAY)
        i_gray = cv2.cvtColor(image_, cv2.COLOR_BGR2GRAY)
        if bgremove:
            s_gray = cv2.Canny(s_gray, 100, 200)
            i_gray = cv2.Canny(i_gray, 100, 200)
        if DEBUG:
            toolbox.showImage(s_gray)
            toolbox.showImage(i_gray)

        res = cv2.matchTemplate(i_gray, s_gray, method)
    # toolbox.showImage(res)
    w, h = search.shape[1], search.shape[0]

    points = []
    while True:
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)
        if method in [cv2.TM_SQDIFF, cv2.TM_SQDIFF_NORMED]:
            top_left = min_loc
        else:
            top_left = max_loc

        print 'templmatch_value(thresh:%.1f) = %.3f' %(threshold, max_val) # not show debug
        if max_val < threshold:
            break
        middle_point = (top_left[0]+w/2, top_left[1]+h/2)
        points.append(middle_point)
        if maxcnt and len(points) >= maxcnt:
            break
        # floodfill the already found area
        cv2.floodFill(res, None, max_loc, (-1000,), max_val-threshold+0.1, 1, flags=cv2.FLOODFILL_FIXED_RANGE)
    return points


if __name__ == '__main__':
    search_file, image_file = 'imgs/me2.png', 'imgs/timer.png'
    search_file, image_file = 'imgs/hand.png', 'imgs/hand_map.png'
    search_file, image_file = 'imgs/back.png', 'imgs/back_map.png'
    search_file, image_file = 'imgs/plus.png', 'imgs/back_map.png'
    search_file, image_file = 'imgs/minus.png', 'imgs/back_map.png'
    search_file, image_file = 'imgs/minus_add.png', 'imgs/back_map.png'

    # dst = cv2.resize(sf, (0, 0), fx = 4, fy=4)
    
    threshold = 0.7
    positions = findall(search_file, image_file, threshold, maxcnt=9)
    print 'point_count =', len(positions or []), positions
    if positions:
        w, h = cv2.imread(search_file, 0).shape[::-1]
        img = cv2.imread(image_file)

        for (x, y) in positions: 
            img = toolbox.markPoint(img, (x, y))
        toolbox.showImage(img)
    else:
        print 'No points founded'
