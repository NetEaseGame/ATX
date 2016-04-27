#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import cv2
import time
import numpy as np
import matplotlib.pyplot as plt
import scipy.fftpack
from cv2 import cv

def _binary_array_to_hex(arr):
    """
    internal function to make a hex string out of a binary array
    """
    h = 0
    s = []
    for i, v in enumerate(arr.flatten()):
        if v: 
            h += 2**(i % 8)
        if (i % 8) == 7:
            s.append(hex(h)[2:].rjust(2, '0'))
            h = 0
    return "".join(s)

def ahash(img, size=8):
    '''average hash'''
    img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    mat = cv2.resize(img, (size, size))
    avg = mat.mean()
    arr = mat > avg
    return arr
    # return _binary_array_to_hex(arr)


def phash(img, size=8, factor=4):
    '''perceptual Hash'''
    img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    mat = cv2.resize(img, (size*factor, size*factor))/1.0
    dct = scipy.fftpack.dct(scipy.fftpack.dct(mat, axis=0), axis=1)
    dctlowfreq = dct[:size, :size]
    med = np.median(dctlowfreq)
    arr = dctlowfreq > med
    return arr
    # return _binary_array_to_hex(arr)

def dhash(img, size=8):
    '''difference hash'''
    img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    mat = cv2.resize(img, (size+1, size))
    arr = mat[1:, :] > mat[:-1,:]
    return arr
    # return _binary_array_to_hex(arr)


## 尝试判断场景
## 尝试识别UI层(静止不动层) 
# ShiTomasi corner detection & Lucas Kanada optical flow
## 识别2D/3D运动
# Meanshift & Camshift
def test_features():
    from atx.device.android_minicap import AndroidDeviceMinicap
    cv2.namedWindow("preview")
    d = AndroidDeviceMinicap()

    # r, h, c, w = 200, 100, 200, 100
    # track_window = (c, r, w, h)
    # oldimg = cv2.imread('base1.png')
    # roi = oldimg[r:r+h, c:c+w]
    # hsv_roi = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)
    # mask = cv2.inRange(hsv_roi, 0, 255)
    # roi_hist = cv2.calcHist([hsv_roi], [0], mask, [180], [0,180])
    # cv2.normalize(roi_hist, roi_hist, 0, 255, cv2.NORM_MINMAX)
    # term_cirt = (cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT,  10, 1)


    while True:
        try:
            w, h = d._screen.shape[:2]
            img = cv2.resize(d._screen, (h/2, w/2))
            cv2.imshow('preview', img)

            hist = cv2.calcHist([img], [0], None, [256], [0,256])
            plt.plot(plt.hist(hist.ravel(), 256))
            plt.show()
            # if img.shape == oldimg.shape:
            #     # hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
            #     # ret, track_window = cv2.meanShift(hsv, track_window, term_cirt)
            #     # x, y, w, h = track_window
            #     cv2.rectangle(img, (x, y), (x+w, y+h), 255, 2)
            #     cv2.imshow('preview', img)
            # # cv2.imshow('preview', img)
            key = cv2.waitKey(1)
        except KeyboardInterrupt:
            break

    cv2.destroyWindow('preview')

def test_hist():
    files = ('base1.png', 'base2.png')
    for i in range(len(files)):
        img = cv2.imread(files[i])
        # hist = cv2.calcHist([img], [0], None, [256], [0,256])
        for j in range(3):
            plt.subplot(2, 3, 3*i+j+1)
            plt.hist(img[:,:,j].flatten(), 64)
            plt.title('%s-%d' % (files[i], j))
    plt.show()


# def similarize(img, r=5):
#     weights = [60, 40] # first-many, second-many
#     weight_self = 50

#     h, w, _ = img.shape
#     mat = img.copy()

#     for i in range(h):
#         # if i > 10:
#         #     continue
#         mmin, mmax = max(i-r+1, 0), min(i+r, h)
#         for j in range(w):
#             nmin, nmax = max(j-r+1, 0), min(j+r, w)
#             rect = np.zeros((mmax-mmin, nmax-nmin))
#             roi = img[mmin:mmax, nmin:nmax, :]

#             ele = img[i,j,:]
#             for m in range(mmin, mmax):
#                 for n in range(nmin, nmax):
#                     vec = ele - img[m,n,:]
#                     d = (sum(vec**2))**0.5
#                     rect[m-mmin, n-nmin] = d

#             # print 'ijmn', (i, mmin, mmax), (j, nmin, nmax) 
#             # print 'roi', roi
#             # print 'rect', rect
#             m1 = (rect<8)
#             m2 = (rect>8) & (rect<16)
#             # print m1
#             # print m2

#             c1, c2 = m1.sum(), m2.sum()
#             m1 = np.dstack([m1]*3)
#             m2 = np.dstack([m2]*3)

#             if c1 == 0 and c2 == 0:
#                 mat[i, j, :] = ele
#             elif c1 == 0 and c2 != 0:
#                 mat[i, j, :] = (roi*m2).sum(axis=(0,1))/c2
#             elif c1 !=0 and c2 == 0:
#                 mat[i, j, :] = (roi*m1).sum(axis=(0,1))/c1
#             else:
#                 w1, w2 = 0.8, 0.2
#                 mat[i, j, :] = w1*(roi*m1).sum(axis=(0,1))/c1 + w2*(roi*m2).sum(axis=(0,1))/c2
#         #     print mat[i,j,:], ele
#         #     break
#         # if i != h-1:
#         #     break
#     return mat

def test_kmeans(img):
    ## K均值聚类
    z = img.reshape((-1, 3))
    z = np.float32(z)
    criteria = (cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_MAX_ITER, 10, 1.0)
    ret, label, center = cv2.kmeans(z, 20, criteria, 10, cv2.KMEANS_RANDOM_CENTERS)
    center = np.uint8(center)
    res = center[label.flatten()]
    res2 = res.reshape((img.shape))
    cv2.imshow('preview', res2)
    cv2.waitKey()

def test_hsv_gradient(img):
    ## gradient test using hsv
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    s = hsv[:,:,2]
    s = s[:,:,np.newaxis]
    h = np.hstack([np.diff(s, axis=1), (s[:,0,:]-s[:,-1,:])[:,np.newaxis,:]]) 
    v = np.vstack([np.diff(s, axis=0), (s[0,:,:]-s[-1,:,:])[np.newaxis,:,:]])
    edge = (h**2 + v**2)**0.5
    edge[edge<10] = 0
    cv2.imshow('preview', edge)
    cv2.waitKey()
    edge = cv2.GaussianBlur(edge, (3,3), 1)
    cv2.imshow('preview', edge)
    cv2.waitKey()

def test_detect_ui(imgname = 'base1'):
    img = cv2.imread('%s.png' % imgname)

    origin = img
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    hsv_full = cv2.cvtColor(img, cv2.COLOR_BGR2HSV_FULL)
    hls = cv2.cvtColor(img, cv2.COLOR_BGR2HLS)
    hls_full = cv2.cvtColor(img, cv2.COLOR_BGR2HLS_FULL)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    ## this is very slow
    # gray_denoised = cv2.fastNlMeansDenoising(gray, None, 20, 7, 21)
    # img_denoised = cv2.fastNlMeansDenoisingColored(img, None, 10, 10, 7, 21)

    # kernel = np.ones((5,5), np.uint8)
    kernel = cv2.getStructuringElement(cv2.MORPH_CROSS,(5,5))
    print kernel

    nochange = lambda img: img
    erosion = lambda img: cv2.erode(img, kernel, iterations=3)
    dilation = lambda img: cv2.dilate(img, kernel, iterations=3)
    opening = lambda img: cv2.morphologyEx(img, cv2.MORPH_OPEN, kernel, iterations=3)
    closing = lambda img: cv2.morphologyEx(img, cv2.MORPH_CLOSE, kernel, iterations=3)
    gradient = lambda img: cv2.morphologyEx(img, cv2.MORPH_GRADIENT, kernel, iterations=3)
    blackhat = lambda img: cv2.morphologyEx(img, cv2.MORPH_BLACKHAT, kernel, iterations=3)
    tophat = lambda img: cv2.morphologyEx(img, cv2.MORPH_TOPHAT, kernel, iterations=3)
    # laplacian = lambda img: cv2.Laplacian(gray, cv2.CV_8U)
    # sobelx = lambda img: cv2.Sobel(gray,cv2.CV_8U,1,0,ksize=3)
    # sobely = lambda img: cv2.Sobel(gray,cv2.CV_8U,0,1,ksize=3)

    revtrans = {'hsv':cv2.COLOR_HSV2BGR, 'hls':cv2.COLOR_HLS2BGR, 'hsv_full':cv2.COLOR_HSV2BGR, 'hls_full':cv2.COLOR_HLS2BGR}

    for tran in ('origin', 'gray', 'hsv', 'hsv_full', 'hls', 'hls_full', 'gray_denoised', 'img_denoised'):
        sample = locals().get(tran)
        if sample is None: continue
        # sample = cv2.GaussianBlur(sample, (3,3), 1)
        # sample = cv2.bilateralFilter(sample,9,70,70)

        for method in ('nochange', 'erosion', 'dilation', 'opening', 'closing', 'gradient', 'blackhat', 'tophat', 'laplacian', 'sobelx', 'sobely'):
            func = locals().get(method)
            if func is None: continue
            print tran, method
            mat = func(sample.copy())
            edges = cv2.Canny(mat,80,200)
            revtran = revtrans.get(tran)
            if revtran:
                mat = cv2.cvtColor(mat, revtran)
            # edges = cv2.bilateralFilter(edges, 31, 30, 30)
            cv2.imshow('preview', edges)
            cv2.waitKey()
            _, thresh = cv2.threshold(edges, 0, 255, cv2.THRESH_OTSU)
            contours, _ = cv2.findContours(thresh, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_SIMPLE)
            contours.sort(key=lambda cnt: len(cnt), reverse=True)
            for cnt in contours:
                area = cv2.contourArea(cnt)
                length = cv2.arcLength(cnt,True)
                # if len(cnt) < 10:
                #     continue
                # if area < 20:# or area > 300:
                #     continue
                # if length < 100:# or length > 400:
                #     continue
                # print len(cnt), int(area), int(length)
                # epsilon = 0.2*length
                # poly = cv2.approxPolyDP(cnt,epsilon,True)
                hull = cv2.convexHull(cnt)
                hull_area = cv2.contourArea(hull)
                x,y,w,h = cv2.boundingRect(cnt)
                rect_area = float(w*h)
                if w<20 or h<20 or rect_area<100:
                    continue
                if hull_area/rect_area < 0.65:
                    continue

                cv2.drawContours(mat, [hull], 0,255,-1)
                cv2.rectangle(mat,(x,y),(x+w,y+h),(0,255,0),2)
                cnt = hull
                style = -1
                if style == 1:
                    lb,lt,rt,rb = cv.BoxPoints(cv2.minAreaRect(cnt))
                    lt = tuple(map(int, lt))
                    rb = tuple(map(int, rb))
                    cv2.rectangle(mat,lt,rb,(0,255,0),2)
                elif style == 2:
                    (x,y),radius = cv2.minEnclosingCircle(cnt)
                    center = (int(x),int(y))
                    radius = int(radius)
                    cv2.circle(mat,center,radius,(255,255,0),2)
                elif style == 3:
                    ellipse = cv2.fitEllipse(cnt)
                    cv2.ellipse(mat,ellipse,(0,255,0),2)

                # cv2.imshow('preview', mat)
                # cv2.waitKey()
            # break

            cv2.imshow('preview', mat)
            # cv2.imwrite('%s-%s-%s.png' % (imgname, tran, method), mat)
            cv2.waitKey()

if __name__ == '__main__':
    test_detect_ui('base1')