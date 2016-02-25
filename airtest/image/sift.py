#!/usr/bin/env python
# coding: utf-8
#
# sift match method (most code from opencv official site)
#
# here: sch(sch) img(image)

import numpy as np
import cv2

MIN_MATCH_COUNT = 3

sift = cv2.SIFT()

def _cv2open(filename, arg=1):
    if isinstance(filename, basestring):
        obj = cv2.imread(filename, arg)
    else:
        obj = filename
    if obj == None:
        raise IOError('cv2 read file error:'+filename)
    return obj

def find(search_file, image_file, threshold=None):
    '''
    param threshold are disabled in sift match.
    '''
    sch = _cv2open(search_file, 0)
    img = _cv2open(image_file, 0)

    kp_sch, des_sch = sift.detectAndCompute(sch, None)
    kp_img, des_img = sift.detectAndCompute(img, None)

    if len(kp_sch) < MIN_MATCH_COUNT or len(kp_img) < MIN_MATCH_COUNT:
        return None

    FLANN_INDEX_KDTREE = 0
    index_params = dict(algorithm = FLANN_INDEX_KDTREE, trees = 5)
    search_params = dict(checks = 50)

    flann = cv2.FlannBasedMatcher(index_params, search_params)

    matches = flann.knnMatch(des_sch, des_img, k=2)

    good = []
    for m,n in matches:
        if m.distance < 0.7*n.distance:
            good.append(m)

    if len(good) > MIN_MATCH_COUNT:
        sch_pts = np.float32([kp_sch[m.queryIdx].pt for m in good]).reshape(-1, 1, 2)
        img_pts = np.float32([kp_img[m.trainIdx].pt for m in good]).reshape(-1, 1, 2) 

        M, mask = cv2.findHomography(sch_pts, img_pts, cv2.RANSAC, 5.0)
        # matchesMask = mask.ravel().tolist()

        h, w = sch.shape
        pts = np.float32([ [0, 0], [0, h-1], [w-1, h-1], [w-1, 0] ]).reshape(-1, 1, 2)
        dst = cv2.perspectiveTransform(pts, M)
        lt, br = dst[0][0], dst[2][0]
        return map(int, (lt[0]+w/2, lt[1]+h/2))
    else:
        return None

def findall(search_file, image_file, threshold=None, maxcnt=0):
    sch = _cv2open(search_file, 0)
    img = _cv2open(image_file, 0)

    kp_sch, des_sch = sift.detectAndCompute(sch, None)
    kp_img, des_img = sift.detectAndCompute(img, None)

    if len(kp_sch) < MIN_MATCH_COUNT or len(kp_img) < MIN_MATCH_COUNT:
        return None

    FLANN_INDEX_KDTREE = 0
    index_params = dict(algorithm = FLANN_INDEX_KDTREE, trees = 5)
    search_params = dict(checks = 50)

    flann = cv2.FlannBasedMatcher(index_params, search_params)

    points = []
    while True:
        matches = flann.knnMatch(des_sch, des_img, k=2)
        good = []
        for m,n in matches:
            if m.distance < 0.7*n.distance:
                good.append(m)
        if len(good) < MIN_MATCH_COUNT:
            break

        if maxcnt and len(points) > maxcnt:
            break

        # print good
        sch_pts = np.float32([kp_sch[m.queryIdx].pt for m in good]).reshape(-1, 1, 2)
        img_pts = np.float32([kp_img[m.trainIdx].pt for m in good]).reshape(-1, 1, 2) 

        M, mask = cv2.findHomography(sch_pts, img_pts, cv2.RANSAC, 5.0)

        h, w = sch.shape
        pts = np.float32([ [0, 0], [0, h-1], [w-1, h-1], [w-1, 0] ]).reshape(-1, 1, 2)
        dst = cv2.perspectiveTransform(pts, M)
        lt, br = dst[0][0], dst[2][0]
        pt = map(int, (lt[0]+w/2, lt[1]+h/2))

        qindexes = []
        tindexes = []
        for m in good:
            qindexes.append(m.queryIdx)
            tindexes.append(m.trainIdx)
        def filter_index(indexes, arr):
            r = np.ndarray(0, np.float32)
            for i, item in enumerate(arr):
                if i not in qindexes:
                    # r.append(item)
                    r = np.append(r, item)
            return r
        # print type(des_sch[0][0])
        kp_sch = filter_index(qindexes, kp_sch)
        des_sch =filter_index(qindexes, des_sch)
        kp_img = filter_index(tindexes, kp_img)
        des_img = filter_index(tindexes, des_img)
        points.append(pt)

    return points

if __name__ == '__main__':
    search_file = '../../test/testdata/oneimg-mule1/q1.png'
    image_file = '../../test/testdata/oneimg-mule1/train.png'
    pt = find(search_file, image_file)
    # print pt
    if pt:
        import toolbox
        img = toolbox.markPoint(image_file, pt)
    toolbox.showImage(img)

    pts = findall(search_file, image_file)
    # print pt
    for pt in pts:
        import toolbox
        img = toolbox.markPoint(image_file, pt)
    toolbox.showImage(img)

    
