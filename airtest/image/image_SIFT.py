#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
2014/08/05 jiaqianghuai: create this code
"""

__author__ = 'hzjiaqianghuai,hzsunshx'
__version__ = '0.2.08.05'
__description__ ='create this code'

import os
import time
import math
import numpy as np
import cv2

MIN_MATCH_COUNT = 5
DEBUG = os.getenv('DEBUG') == 'true'

#path check
def _path_check(image_path):
    if not os.path.exists(image_path):
        raise IOError(image_path + 'not exists')

#Euclidean distance
def _distance(point_1,point_2):
    norm2 = ((point_1[0]-point_2[0])*(point_1[0]-point_2[0]) + 
            (point_1[1]-point_2[1])*(point_1[1]-point_2[1]))
    return math.sqrt(norm2)     

#remove the duplicate element in the list
def _reremove(list):
    checked = []
    for e in list:
        if e not in checked: checked.append(e)
    return checked            
        
#SIFT extraction
def _sift_extract(image):
    sift = cv2.SIFT()
    keypoints, descriptors = sift.detectAndCompute(image, None)
    return keypoints, descriptors

#search and match keypoint_pair
def _searchAndmatch(image_1_descriptors, image_2_descriptors, threshold=0.7
                    ,image_2_keypoint=None):
    """KNN Match"""
    Good_match_keypoints, kp2_xy = [], []
    FLANN_INDEX_KDTREE = 0
    index_params = dict(algorithm=FLANN_INDEX_KDTREE, trees=5)
    search_params = dict(checks=50)
    flann = cv2.FlannBasedMatcher(index_params, search_params)
    matches = flann.knnMatch(image_1_descriptors, image_2_descriptors, k=2)
    """Lower's threshold"""
    for m,n in matches:
        if image_2_keypoint: kp2_xy.append(image_2_keypoint[m.trainIdx].pt)
        if m.distance < threshold*n.distance: Good_match_keypoints.append(m)
    return Good_match_keypoints, kp2_xy

#refine center
def _refine_center(point_list, hori_distance, veti_distance):
    """refine center
    
    @param point_list: list(contains points that is near to the latent center)
    @param hori_distance: int(restrict the horizontal distance between points)
    @param veti_distance: int(restrict the vetical distance between points)
    @return new_center: list(new center)
    """
    point_sum,re_point_sum, max, dist, index, count= [0, 0],[0, 0], 0, [], [], 0
    re_list = _reremove(point_list)
    if len(re_list) < 1 or len(re_list) < int(len(point_list)*0.5): return None
    for i in range(len(re_list)):
        point_sum[0] = point_sum[0] + re_list[i][0]
        point_sum[1] = point_sum[1] + re_list[i][1]
    center = [float(point_sum[0])/len(re_list),float(point_sum[1])/len(re_list)]
    if len(re_list) == 1:
        return center        
    else:
        for i in range(len(re_list)):
            dis = _distance(center, re_list[i])
            if max < dis:
                max = dis
                k = i
        if len(re_list) == 2:
            [re_center_x,re_center_y] = center
        else:
            re_point_sum[0] = point_sum[0] - re_list[k][0]
            re_point_sum[1] = point_sum[1] - re_list[k][1]
            del re_list[k]
            re_center_x = float(re_point_sum[0])/len(re_list)
            re_center_y = float(re_point_sum[1])/len(re_list)
        for i in range(len(re_list)):
                if (int(1.5*hori_distance) < (abs(re_center_x-re_list[i][0])) or 
                    int(1.5*veti_distance) < (abs(re_center_y-re_list[i][1]))):
                        count = count + 1
        if count == len(re_list):
            return None
        else:
            return [re_center_x, re_center_y]

#rectangle object in an image
def _image_rectangle(image, centers, width, height,outfile='match.png'):
    for i in range(len(centers)):
        center = centers[i]
        '''判断中心点是否在图像中'''
        if 0 < center[0] < image.shape[1] and 0 < center[1] < image.shape[0]:
            topleft_x = int(center[0]-width*0.5)
            topleft_y = int(center[1]-height*0.5)
            bottomright_x = int(center[0]+width*0.5)
            bottomright_y = int(center[1]+height*0.5)
            if topleft_x < 0: topleft_x = 0
            if topleft_y < 0: topleft_y = 0
            if image.shape[1] <= bottomright_x: bottomright_x = image.shape[1]-1
            if image.shape[0] <= bottomright_y: bottomright_y = image.shape[0]-1
            if DEBUG:
                cv2.rectangle(image,(topleft_x,topleft_y),
                                    (bottomright_x,bottomright_y),(0,0,255),1,0)
                cv2.circle(image,(int(center[0]),int(center[1])),2,(0,255,0),-1)
    if outfile:
        cv2.imwrite(outfile,image)    
    
#homography
def _homography(src_pts,dst_pts,template_width,template_height,match_point=None):
    row,col,dim = dst_pts.shape
    if match_point:
        for i in range(row):
            match_point.append([int(dst_pts[i][0][0]),int(dst_pts[i][0][1])])
    M, mask = cv2.findHomography(src_pts, dst_pts, cv2.RANSAC, 5.0)
    pts = np.float32([[0, 0], [0, template_height - 1], 
                    [template_width - 1, template_height - 1], 
                    [template_width - 1, 0]]).reshape(-1, 1, 2)
    #找到一个变换矩阵，从查询图映射到检测图片
    dst = cv2.perspectiveTransform(pts, M) 
    return dst
        
def locate_one_image_SIFT(origin, query, outfile=None, threshold=0.3):
    """Locate one image position with SIFT based match method

    @param origin: string (target filename)
    @param query: string (image need to search)
    @param outfile: string (output image filename name)
    @param threshold: float (range [0, 1), the lower the more ease to match)
    @return None if not found, (x,y) point if found
    """
    _path_check(origin)
    _path_check(query)
    img1 = cv2.imread(query, 0)  # queryImage,gray
    img2 = cv2.imread(origin, 0)  # originImage,gray
    query_img = cv2.imread(query, 1)  # queryImage
    target_img = cv2.imread(origin, 1)  # originImage
    threshold = 1 - threshold
    [height, width] = [img1.shape[0], img1.shape[1]]
    try:
        kp1, des1 = _sift_extract(img1)
        kp2, des2 = _sift_extract(img2)
        [num1, num2] = [len(kp1), len(kp2)]
        if num2 < num1: return None
    except:
        return None
    ratio_num = int(num1 * 0.1)
    '''store all the good matches as per Lowe's ratio test.'''
    good, kp2_xy= _searchAndmatch(des1, des2, threshold,kp2)
    src_pts = np.float32([kp1[m.queryIdx].pt for m in good]).reshape(-1,1,2)
    dst_pts = np.float32([kp2[m.trainIdx].pt for m in good]).reshape(-1,1,2)
    if len(good) > MIN_MATCH_COUNT: #good matches超过给定阈值,则进行Homography       
        dst = _homography(src_pts, dst_pts, width,height,None)
        center, count = [0.0, 0.0], 0
        for i in range(dst.shape[0]):
            if (0 <= int(dst[i][0][0]) <= img2.shape[1] and
                0 <= int(dst[i][0][1]) <= img2.shape[0]):
                    center = center + dst[i][0]
                    count = count + 1
        if count < 1 or (center[0] == 0.0 and center[1] == 0.0):
            return None
        else:
            new_center = [int(center[0]/count), int(center[1]/count)]
            if new_center:
                _image_rectangle(target_img,[new_center], width, height, outfile)
            return new_center
    else:
        row,col,dim = dst_pts.shape
        '''几乎没有好的匹配点的情况'''
        if row < 1 or (row+1) < ratio_num:
            return None
        else:
            list = []
            for i in range(row):
                [x, y] = [dst_pts[i][0][0], dst_pts[i][0][1]]
                list.append([int(x),int(y)])
                if DEBUG:
                    cv2.circle(target_img, (int(x), int(y)), 2, (255, 0, 0), -1)
            newcenter = _refine_center(list,width,height)
            if newcenter:
                [center_x, center_y] = [int(newcenter[0]),int(newcenter[1])]
                [top_x, top_y] = [int(center_x-width/2), int(center_y-height/2)]
                if (top_x < 0) and (top_y < 0): return None
                center = [center_x,center_y]
                _image_rectangle(target_img, [center], width, height, outfile)
                return center
                
if __name__ == '__main__':
    starttime = time.clock()
    pts = locate_one_image_SIFT('testdata/target.png', 'testdata/query.png',
                        'testdata/DEBUG.png', 0.3)                        
    endtime = time.clock()
    print "time: ", endtime - starttime
    print "center point: ", pts
