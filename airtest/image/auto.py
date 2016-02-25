#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
2014/09/01 jiaqianghuai: fix the code
"""

__author__ = 'hzjiaqianghuai,hzsunshx'
__version__ = '0.2.09.01'
__description__ ='fix the code'

import os
import time
import math
import numpy as np
import cv2

MIN_MATCH_COUNT = 5
MIN_MATCH = 15
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

#sort the point_list in the ascending order of y coordinate
def _sort_point_list(list, option=1):
    """option=1, ordered by y; option=0, ordered by x"""
    reorder_list = []
    for i in range(len(list)-1):
        min, k = list[0][option], 0
        for j in range(1,len(list)):
            if list[j][option] < min:
                min = list[j][option]
                k = j
        reorder_list.append(list[k])
        del list[k]
    reorder_list.append(list[0])
    return reorder_list

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
                        
#re_cluster center
def _re_cluster_center(image, centers, match_points,
                        hori_distance, veti_distance, threshold):
    """refine center
    
    @param image: np.array(input target image)
    @param match_points: list(contains points that are matched)
    @param hori_distance: int(restrict the horizontal distance between points)
    @param veti_distance: int(restrict the vetical distance between points)
    @param threshold: int(define the least points belonging to one center) 
    @return new_centers: list(they are sorted by the ascending of y coordinate)
    """  
    re_centers = []
    re_match_points = _reremove(match_points)
    for i in range(len(centers)):
        sum_x, sum_y, k = 0, 0, 0
        top_left_x = centers[i][0]-int(hori_distance/2)
        top_left_y = centers[i][1]-int(veti_distance/2)
        bottom_right_x = centers[i][0] + int(hori_distance/2)
        bottom_right_y = centers[i][1] + int(veti_distance/2)
        for j in range(len(re_match_points)):
            '''选择在中心点附近一定区域内的关键点'''
            if (abs(centers[i][0]-re_match_points[j][0])<int(hori_distance/2) and
                abs(centers[i][1]-re_match_points[j][1])<int(veti_distance/2) and
                0 < top_left_x and 0 < top_left_y and
                bottom_right_x<image.shape[1] and bottom_right_y<image.shape[0]):
                    sum_x = sum_x + re_match_points[j][0]
                    sum_y = sum_y + re_match_points[j][1]
                    k = k + 1
        if threshold <= k  and 0 < k:
            [x, y] = [int(float(sum_x)/k), int(float(sum_y)/k)]
            re_centers.append([x, y])
    new_centers = _sort_point_list(re_centers)
    return new_centers

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
   
#write keywords and descriptors into an array
def _pickle_keypoints(keypoints, descriptors):
    i, array = 0, []
    for point in keypoints:
        temp = (point.pt, point.size, point.angle, point.response, point.octave,
                point.class_id, descriptors[i])
        i = i + 1
        array.append(temp)
    return array

#filter keypoints and descriptors in the detected region
def _unpickle_keypoints(array, region_center, region_width,
                        region_height, image_width, image_height):
    keypoints, descriptors = [], []
    [center_x,center_y] = region_center
    top_left_x = int(center_x - region_width)
    top_left_y = int(center_y - region_height)
    bottom_right_x = int(center_x + region_width)
    bottom_right_y = int(center_y + region_height)
    if top_left_x < 0: top_left_x = 0
    if top_left_y < 0: top_left_y = 0
    if image_width < bottom_right_x: bottom_right_x = image_width - 1
    if image_height < bottom_right_y: bottom_right_y = image_height - 1
    for point in array:
        [x, y] = [int(point[0][0]), int(point[0][1])]
        if (x < top_left_x or y < top_left_y or 
            bottom_right_x < x or bottom_right_y < y):
            temp_keypoint = cv2.KeyPoint(x=point[0][0],y=point[0][1],_size=point[1],
                                        _angle=point[2],_response=point[3],
                                        _octave=point[4],_class_id=point[5])
            temp_descriptor = point[6]
            keypoints.append(temp_keypoint)
            descriptors.append(temp_descriptor)
    return keypoints, np.array(descriptors)

#zero the pixel in the image's given region
def _region_pixel_zero(image, region_center, region_width, region_height):
    top_left_x = int(region_center[0]-region_width)
    top_left_y = int(region_center[1]-region_height)
    for i in range(region_height*2):
        y = top_left_y + i
        if image.shape[0] <= y: y = image.shape[0] - 1
        for j in range(region_width*2):
            x = top_left_x + j
            if image.shape[1] <= x: x = image.shape[1] - 1
            if image.ndim == 2: #gray pic
                image[y, x] = 0
            elif image.ndim == 3: #color pic
                image[y, x, 0], image[y, x, 1], image[y, x, 1] = 0, 0, 0
 
#copy region from image
def _region_copy(image, region_center, region_width, region_height, scale=1):
    [center_x,center_y] = region_center
    top_left_x = int(center_x - region_width)
    top_left_y = int(center_y - region_height)
    if top_left_x < 0: top_left_x = 0
    if top_left_y < 0: top_left_y = 0
    if image.ndim == 2: #gray pic
        rect_img = np.zeros((region_height*scale,region_width*scale),image.dtype)
        for i in range(int(region_height * scale)):
            ty = top_left_y + i
            if image.shape[0] <= ty: ty = image.shape[0] - 1
            for j in range(int(region_width * scale)):
                tx = top_left_x + j
                if image.shape[1] <= tx: tx = image.shape[1] - 1
                rect_img[i][j] = image[ty][tx]
    elif image.ndim == 3: #color pic 
        rect_img = np.zeros((region_height*scale,region_width*scale, 3),image.dtype)
        for i in range(int(region_height * scale)):
            ty = top_left_y + i
            if image.shape[0] <= ty: ty = image.shape[0] - 1
            for j in range(int(region_width * scale)):
                tx = top_left_x + j
                if image.shape[1] <= tx: tx = image.shape[1] - 1
                rect_img[i][j][0] = image[ty][tx][0]
                rect_img[i][j][1] = image[ty][tx][1]
                rect_img[i][j][2] = image[ty][tx][2]
    return rect_img

#image process,in order to graying image's maiginal field
def _image_process(image, threshold=0.1):
    [h, w] = [image.shape[0], image.shape[1]]
    [h_top, w_top] = [int(h*threshold), int(w*threshold)]
    [h_bottom, w_bottom] = [h-h_top, w-w_top]
    for i in range(h):
        for j in range(w):
            if (image.ndim == 2 and (i < h_top or j < w_top or h_bottom < i or
                w_bottom < j)):
                if 200 < image[i,j]: image[i,j] = 0
            elif(image.ndim == 2 and (i < h_top or j < w_top or h_bottom < i or
                w_bottom < j)):
                gray_avg = int((image[i,j,0]+image[i,j,1]+image[i,j,2])/3.)
                if 200 < gray_avg:
                    image[i,j,0], image[i,j,1], image[i,j,2] = 0, 0, 0
    
#image rotation    
def _image_rotate(image, angle, scale=1.):
    """ image rotation
    
    @param image: np.array(input image)
    @param angle: degree(from (-180,180),the positive means anticlockwise)
    @param scale: float(rotation scale)
    @return: np.array(rotated image)
    """
    [w, h] = [image.shape[1], image.shape[0]]
    rangle = np.deg2rad(angle)  # angle in radians
    # now calculate new image width and height
    nw = (abs(np.sin(rangle)*h) + abs(np.cos(rangle)*w))*scale
    nh = (abs(np.cos(rangle)*h) + abs(np.sin(rangle)*w))*scale
    # ask OpenCV for the rotation matrix
    rot_mat = cv2.getRotationMatrix2D((nw*0.5, nh*0.5), angle, scale)
    # calculate the move from the old center to the new center combined
    # with the rotation
    rot_move = np.dot(rot_mat, np.array([(nw-w)*0.5, (nh-h)*0.5,0]))
    # the move only affects the translation, so update the translation
    # part of the transform
    rot_mat[0,2] += rot_move[0]
    rot_mat[1,2] += rot_move[1]
    return cv2.warpAffine(image,rot_mat,(int(math.ceil(nw)),int(math.ceil(nh))),
                        flags=cv2.INTER_LANCZOS4)
           
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
    if outfile: cv2.imwrite(outfile,image)

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

#SIFT + Homography
def _homography_match(source_image, template_image, src_points, dst_points,
                     num, match_point=None, option=0):
    """ SIFT+Homography match
    
    @param source_image: np.array(input source image)
    @param template_image: np.array(input template image)
    @param src_points: np.array(template image's match keypoints)
    @param dst_points: np.array(source image's match keypoints)
    @param match_point: list(if not none, save the matched points)
    @param num: int(the number of template_image's keypoints)
    @param option: int(if it is zero, the similarity method will not be not 
                        used to verify the accuracy of the detected center)
    @return [center_x, center_y: list(match center)
    """  
    [height, width] = [template_image.shape[0], template_image.shape[1]]
    dst = _homography(src_points, dst_points, width,height,match_point)
    center, count = [0.0, 0.0], 0
    if dst.any():
        for i in range(dst.shape[0]):
            if (0 <= int(dst[i][0][0]) <= source_image.shape[1] and
                0 <= int(dst[i][0][1]) <= source_image.shape[0]):
                    center = center + dst[i][0]
                    count = count + 1
        if count < 1 or (center[0] == 0.0 and center[1] == 0.0):
            return None
        else:
            center_x = int(center[0] / count)
            center_y = int(center[1] / count)
            if option == 0:
               return [center_x, center_y]
            else:               
                re_center = [center_x,center_y]
                rect_img = _region_copy(source_image,re_center,width,height,1)
                hist_value = hist_similarity(rect_img, template_image)
                if DEBUG: print "342_hist_value: ", hist_value
                rect_img2 = _region_copy(source_image,re_center,width,height, 2)
                value,kp_num = feature_similarity(rect_img2,template_image,0.7)
                if DEBUG: print "345_sift_value and kp_num: ", value, kp_num
                if (hist_value<-0.0006 and 14< kp_num<=45 and 
                    (value < 0.32 or kp_num==45)): # 0.4 >> 0.32 
                    return None
                '''rule has been obtained from the experiments'''    
                if ((value>0.39) or (kp_num<=14 and 0.34<value) or (22<=kp_num) 
                    or ((kp_num <= 9) and num <= (10*kp_num))):
                        return [center_x, center_y]
                else:
                    rect_img3 = _region_copy(source_image,re_center,height,width,2)
                    val2,kp_num2 = feature_similarity(rect_img3,template_image,0.7)
                    if DEBUG: print "356_sift_value and kp_num: ", val2, kp_num2
                    if ((0.28<val2 and value<=val2 and 13<kp_num2) or (35<kp_num2  
                        and kp_num < kp_num2) or (kp_num == 14 and kp_num2==12 
                        and 0.25 <= value)):
                            return [center_x, center_y]
                    else:
                        return None

#image match with little match keypoints
def _re_detectAndmatch(source_image, template_image, origin_image, query_image,
                        source_image_match_keypoints):
    """ image match with little match keypoints
    
    @param source_image: np.array(input source_gray image)
    @param template_image: np.array(input template_gray image)
    @param origin_image: np.array(input source image)
    @param query_image: np.array(input template image)
    @param source_image_match_keypoints: np.array(source image's match keypoints)
    @return [center_x, center_y: list(match center)
    """     
    [h, w] = [template_image.shape[0], template_image.shape[1]]
    kp = source_image_match_keypoints
    dst_pts = np.float32([kp[m] for m in range(len(kp))]).reshape(-1, 1, 2)
    row, col, dim = dst_pts.shape
    if 0 < row < 33:
        _image_process(template_image, 0.1)
        match_value, match_posi, sift_similarity, max, k = [], [], [], 0.0, 0
        for i in range(row): #在匹配特征点附近进行模板搜索
            rect_img = _region_copy(source_image, dst_pts[i][0], w, h, 2.)
            val_1,kp_num = feature_similarity(rect_img,template_image,0.7)
            val_2,disp = template_match(rect_img,template_image,dst_pts[i][0],1)
            sift_similarity.append(val_1)
            match_value.append(val_2)
            match_posi.append(disp)
            if max < val_2:
                max = val_2
                k = i
        if DEBUG: print "393: ", k, max, sift_similarity[k]
        if 0.9 < max and 0.09 < sift_similarity[k] or (0.8 < max and 0.5 < sift_similarity[k]):
                center_x = int(match_posi[k][0] + w/2)
                center_y = int(match_posi[k][1] + h/2)
        elif 0.2 < sift_similarity[k]:
            if 0.5 < sift_similarity[k]:
                val,disp = rotate_template_match(source_image, template_image)
            else:
                val,disp = template_match(source_image, template_image,[],1)
            if DEBUG: print "402_value: ", val
            if val < 0.7: 
                return None
            else:
                [center_x, center_y] = [int(disp[0]+w/2),int(disp[1]+h/2)]
                rect_img = _region_copy(origin_image,[center_x,center_y],w,h,1.5)
                val1 = hist_similarity(rect_img, query_image)
                if DEBUG: print "409_hist_value: ", val1
                if val1 < 0.1 and val < 0.99: 
                    return None
                else:
                    rect = _region_copy(source_image,[center_x,center_y],w,h,2)
                    val_3,kp_num3 = feature_similarity(rect,template_image,0.7)
                    if DEBUG: print "415_sift_value: ", val_3, kp_num3
                    if 0.0 < val_3: num = int(kp_num3/val_3) #计算good_match点数
                    if val_3 < 0.15 or (num <= 5 and val < 0.92): return None
        else:
            value, posi = template_match(source_image, template_image,[],0)
            [center_x,center_y] = [posi[0]+int(w/2), posi[1]+int(h/2)]
            rect2 = _region_copy(source_image,[center_x,center_y],w,h,2.)
            val_4,kp_num4 = feature_similarity(rect2,template_image,0.7)
            if DEBUG: print "423_value: ", value, val_4,kp_num4
            if value < 0.8 or val_4 == 0.0: #可以更高点
                return None
            else:
                rect_img = _region_copy(origin_image,[center_x,center_y],w,h,1.)
                hist_value = hist_similarity(rect_img, query_image)
                if DEBUG: print "429_hist_value: ", hist_value
                if hist_value < 0.35: return None
    else:
        value, posi, scale = multi_scale_match(source_image, template_image)
        [center_x,center_y] = [int(posi[0]+scale*w/2), int(posi[1]+scale*h/2)]
        if DEBUG: print "434_value: ", value
        if 0.9 < value:
            rect_img = _region_copy(origin_image,[center_x,center_y],
                                    int(w*scale), int(h*scale), 1.)
            temp = cv2.resize(query_image, (int(w*scale), int(h*scale)),
                            cv2.cv.CV_INTER_LINEAR)
            hist_value = hist_similarity(rect_img, temp)
            if DEBUG: print "441_hist_value: ", hist_value
            if hist_value < 0.35: return None
        else:
            return None            
    top_x = int(center_x - w / 2)
    top_y = int(center_y - h / 2)
    if (top_x < 0) and (top_y < 0):
        return None
    else:
        return [int(center_x), int(center_y)]

#template match
def template_match(source_image, template_image, region_center, option=0):
    """ template match
    
    @param source_image: np.array(input source image)
    @param template_image: np.array(input template image)
    @param region_center: list(if not None, it means source_image is 
    part of origin target image, otherwise, it is origin target image)
    @param option: int(if it is not zero, source_image and template_image will
    be global thresholding)
    @return max_val: float(the max match value)
    @return [x,y]: list(the best match position)
    """    
    template_width = template_image.shape[1]
    template_height = template_image.shape[0]
    [source_width,source_height] = [source_image.shape[1],source_image.shape[0]]
    width = source_width - template_width + 1
    height = source_height - template_height + 1
    if width < 1 or height < 1: return None
    if option == 0:
        [s_thresh, t_thresh] = [source_image, template_image]
    else:
        s_ret,s_thresh = cv2.threshold(source_image,200,255,cv2.THRESH_TOZERO)
        t_ret,t_thresh = cv2.threshold(template_image,200,255,cv2.THRESH_TOZERO)
    '''template match'''
    result = cv2.matchTemplate(s_thresh, t_thresh, cv2.cv.CV_TM_CCORR_NORMED)
    (min_val, max_val, minloc, maxloc) = cv2.minMaxLoc(result)
    if len(region_center):
        x = int(maxloc[0]+region_center[0]-source_width/2)
        y = int(maxloc[1]+region_center[1]-source_height/2)
    else:
        [x,y] = maxloc
    return max_val, [x,y]

#rotate template match
def rotate_template_match(source_image, template_image):
    left_rotate_img = _image_rotate(template_image,90, 1)
    right_rotate_img = _image_rotate(template_image,-90, 1)
    val_1,disp_1 = template_match(source_image, template_image,[],0)
    val_2,disp_2 = template_match(source_image, left_rotate_img,[],0)
    val_3,disp_3 = template_match(source_image, right_rotate_img,[],0)
    max = val_1
    posi = disp_1
    if val_2 < val_3:
        if max < val_3:
            max = val_3
            posi = disp_3
    else:
        if max < val_2:
            max = val_2
            posi = disp_2
    return max, posi
    
#multi_scale template match,scale is from 0.25,0.5,0.75,1,1.25,1.5,1.75,2
def multi_scale_match(source_image, template_image):
    match_value, match_posi = [], []
    ratio = [1, 0.5, 0.75, 1.25, 1.5, 2] #放缩因子
    value, posi = template_match(source_image, template_image,[],1)
    match_value.append(value)
    match_posi.append(posi)
    max, k = match_value[0], 0
    [height,width] = [template_image.shape[0],template_image.shape[1]]
    for i in range(1,len(ratio)):
        size = (int(ratio[i]*width),int(ratio[i]*height))
        if source_image.shape[1] < size[0] or source_image.shape[0] < size[1]:
            break
        temp = cv2.resize(template_image,size,cv2.cv.CV_INTER_LINEAR)
        value, posi = template_match(source_image, temp,[],1)
        match_value.append(value)
        match_posi.append(posi)
        if max < value:
            max = value
            k = i
    return match_value[k], match_posi[k], ratio[k]

#color_hist based similarity
def hist_similarity(image_1, image_2):
    """color hist based image similarity
    
    @param image_1: np.array(the first input image)
    @param image_2: np.array(the second input image)
    @return similarity: float(range from [0,1], the bigger the more similar)
    """
    if image_1.ndim == 2 and image_2.ndim == 2:
        hist_1 = cv2.calcHist([image_1], [0], None, [256], [0.0, 255.0])
        hist_2 = cv2.calcHist([image_2], [0], None, [256], [0.0, 255.0])
        similarity = cv2.compareHist(hist_1, hist_2, cv2.cv.CV_COMP_CORREL)
    elif image_1.ndim == 3 and image_2.ndim == 3:
        """R,G,B split"""
        b_1, g_1, r_1 = cv2.split(image_1)
        b_2, g_2, r_2 = cv2.split(image_2)
        hist_b_1 = cv2.calcHist([b_1], [0], None, [256], [0.0, 255.0])
        hist_g_1 = cv2.calcHist([g_1], [0], None, [256], [0.0, 255.0])
        hist_r_1 = cv2.calcHist([r_1], [0], None, [256], [0.0, 255.0])
        hist_b_2 = cv2.calcHist([b_2], [0], None, [256], [0.0, 255.0])
        hist_g_2 = cv2.calcHist([g_2], [0], None, [256], [0.0, 255.0])
        hist_r_2 = cv2.calcHist([r_2], [0], None, [256], [0.0, 255.0])
        similarity_b = cv2.compareHist(hist_b_1,hist_b_2,cv2.cv.CV_COMP_CORREL)
        similarity_g = cv2.compareHist(hist_g_1,hist_g_2,cv2.cv.CV_COMP_CORREL)
        similarity_r = cv2.compareHist(hist_r_1,hist_r_2,cv2.cv.CV_COMP_CORREL)
        sum_bgr = similarity_b + similarity_g + similarity_r
        similarity = sum_bgr/3.
    else:
        gray_1 = cv2.cvtColor(image_1,cv2.cv.CV_RGB2GRAY)
        gray_2 = cv2.cvtColor(image_2,cv2.cv.CV_RGB2GRAY)
        hist_1 = cv2.calcHist([gray_1], [0], None, [256], [0.0, 255.0])
        hist_2 = cv2.calcHist([gray_2], [0], None, [256], [0.0, 255.0])
        similarity = cv2.compareHist(hist_1, hist_2, cv2.cv.CV_COMP_CORREL)
    return similarity

#SIFT based similarity
def feature_similarity(image_1,image_2,threshold=0.7):
    """SIFT Feature based image similarity
    
    @param image_1: np.array(the first input image)
    @param image_2: np.array(the second input image)
    @param threshold: float(the lower's threshold)
    @return similarity: float(range from [0,1], the bigger the more similar)
    @return good_match_num； int(the number of good match point pairs)
    """    
    kp1, des1 = _sift_extract(image_1)
    kp2, des2 = _sift_extract(image_2)
    if len(kp1) <= len(kp2):
        num = len(kp1)
    else:
        num = len(kp2)
    if num <= 0:
        similarity, good_match_num = 0.0, 0.0
    else:
        good_match, default = _searchAndmatch(des1, des2, threshold)
        good_match_num = float(len(good_match))
        similarity = good_match_num/num
    return similarity, good_match_num

def locate_image(orig, quer, outfile=None, threshold=0.3):
    pt = locate_one_image(orig, quer, outfile, threshold)
    if pt:
        return [pt]
    else:
        return None

def locate_one_image(origin, query, outfile=None, threshold=0.3):
    '''
    Locate one image position

    @param origin: string (target filename)
    @param query: string (image need to search)
    @param outfile: string (output image filename name)
    @param threshold: float (range [0, 1), the lower the more ease to match)
    @return None if not found, (x,y) point if found
    '''
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
        if DEBUG: print num1, num2
        if num2 < num1: return None
    except:
        return None
    num_single = num1%10
    ratio_num = int(num1 * 0.103)
    '''store all the good matches as per Lowe's ratio test.'''
    good, kp2_xy= _searchAndmatch(des1, des2, threshold,kp2)
    src_pts = np.float32([kp1[m.queryIdx].pt for m in good]).reshape(-1,1,2)
    dst_pts = np.float32([kp2[m.trainIdx].pt for m in good]).reshape(-1,1,2)
    if len(good) > MIN_MATCH_COUNT: #good matches超过给定阈值,则进行Homography
        if DEBUG: print "626_Good"        
        center = _homography_match(img2, img1, src_pts, dst_pts, num1, None,1)
        if center:
            _image_rectangle(target_img, [center], width, height,outfile)
        return center       
    else:
        if DEBUG: print "632_Bad"
        row, col, dim = dst_pts.shape
        '''几乎没有好的匹配点的情况'''
        if DEBUG: print "635 row ratio_num: ", row, ratio_num
        if num1 < 35:
            flag = bool(row < ratio_num and 2 < row)
        else:
            flag = bool(row < ratio_num)
        if (row<1 or flag or (row==1 and ratio_num<1) or (4<row and row==ratio_num )): ####
            center = _re_detectAndmatch(img2, img1, target_img, query_img,kp2_xy)
            if center:
                _image_rectangle(target_img, [center], width, height,outfile)                
            return center
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
                if ((1 <= row <= 2 and 1 <= ratio_num <=2 and num_single != 5) or
                    (row == (ratio_num+1) and row < 4)):
                    rect_img = _region_copy(img2,[center_x,center_y],
                                            width, height, 1)
                    value, posi = template_match(rect_img, img1,[],0)
                    kp_rect, des_rect = _sift_extract(rect_img)
                    if DEBUG: print "663_value: ", value, len(kp_rect)
                    if (value < 0.87 or (len(kp_rect)<=(num1+3) and value<0.9352)
                        or (0.955 < value and len(kp_rect) == 0)): 
                        return None
                center = [center_x,center_y]
                _image_rectangle(target_img, [center], width, height, outfile)
                return center

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
                
def locate_more_image_SIFT(origin, query, outfile=None, threshold=0.3, num=7):
    '''
    Locate multi_object image position with SIFT feature based match method

    @param origin: string (target filename)
    @param query: string (image need to search)
    @param outfile: string (output image filename name)
    @param threshold: float (range [0, 1), the lower the more ease to match)
    @param num: int(defines the number of obejcts to match)
    @return None if not found, (x,y) point list if found
    '''
    _path_check(origin)
    _path_check(query)
    img1 = cv2.imread(query, 0)  # queryImage,gray
    img2 = cv2.imread(origin, 0)  # originImage,gray
    query_img = cv2.imread(query, 1)  # queryImage
    target_img = cv2.imread(origin, 1)  # originImage
    threshold = 1 - threshold
    [h, w] = [img1.shape[0], img1.shape[1]]
    center_list, point_match = [], [[0, 0]]
    try:
        kp1, des1 = _sift_extract(img1)
        kp2, des2 = _sift_extract(img2)
        num1 = len(kp1)
        num2 = len(kp2)
        if num2 < num1:
            return None
    except:
        return None
    ratio_num = int(num1 * 0.1)
    '''store all the good matches as per Lowe's ratio test.'''
    good, default= _searchAndmatch(des1, des2,threshold,None)
    src_pts = np.float32([kp1[m.queryIdx].pt for m in good]).reshape(-1,1,2)
    dst_pts = np.float32([kp2[m.trainIdx].pt for m in good]).reshape(-1,1,2)
    if len(good) > MIN_MATCH_COUNT: #good matches超过给定阈值,则进行Homography        
        center = _homography_match(img2,img1,src_pts,dst_pts,num1,point_match,0)
        if center: center_list.append(center)
    else:
        row,col,dim = dst_pts.shape
        center = [0, 0]
        if (1 <= row and ratio_num <= row):
            for i in range(row):
                [x, y] = [int(dst_pts[i][0][0]), int(dst_pts[i][0][1])]
                point_match.append([x, y])
                center[0] = center[0] + x
                center[1] = center[1] + y
            [center_x, center_y] = [int(center[0]/row), int(center[1]/row)]
            center_list.append([center_x, center_y])
    print "center_list: ", center_list
    if len(center_list) < 1:
        return None
    else:
        center_xy, k = [], 1
        while center_list[-1] and center_list[-1] != center_xy:
            if 0 < num:
                if k == num: break
            center_xy = center_list[-1]
            array = _pickle_keypoints(kp2,des2)
            kp2,des2 = _unpickle_keypoints(array,center_xy,w,h,
                                            img2.shape[1],img2.shape[0])
            good, default= _searchAndmatch(des1, des2,0.9,None)
            src_pts=np.float32([kp1[m.queryIdx].pt for m in good]).reshape(-1,1,2)
            dst_pts=np.float32([kp2[m.trainIdx].pt for m in good]).reshape(-1,1,2) 
            if len(good) > MIN_MATCH_COUNT:       
                center=_homography_match(img2,img1,src_pts,dst_pts,num1,point_match,0)
                if center: 
                    center_list.append(center)
                    k = k + 1
            else:
                if 2 <= len(good):
                    row,col,dim = dst_pts.shape
                    center = [0, 0]
                    if 1 <= row:
                        for i in range(row):
                            [x, y] = [int(dst_pts[i][0][0]),int(dst_pts[i][0][1])]
                            point_match.append([x, y])
                            center[0] = center[0] + x
                            center[1] = center[1] + y
                        [center_x,center_y] = [int(center[0]/row),int(center[1]/row)]
                        center_list.append([center_x, center_y])
                        k = k + 1
        new_centers = _re_cluster_center(img2,center_list,point_match,w,h,ratio_num)
        _image_rectangle(target_img,new_centers,w,h,outfile)
        return new_centers

def locate_more_image_Template(origin, query, outfile=None, num=0):
    '''
    Locate multi_object image position with template match method

    @param origin: string (target filename)
    @param query: string (image need to search)
    @param outfile: string (output image filename name)
    @param threshold: float (range [0, 1), the lower the more ease to match)
    @param num: int(defines the number of obejcts to match)
    @return None if not found, (x,y) point list if found
    '''
    _path_check(origin)
    _path_check(query)
    img1 = cv2.imread(query, 0)  # queryImage,gray
    img2 = cv2.imread(origin, 0)  # originImage,gray
    query_img = cv2.imread(query, 1)  # queryImage
    target_img = cv2.imread(origin, 1)  # originImage
    [h, w] = [img1.shape[0], img1.shape[1]]
    center = []
    if num == 0:
        while (1):                
                maxval, maxloc = template_match(img2, img1, [], 0)
                if maxval < 0.96: break
                center.append([int(maxloc[0]+w/2),int(maxloc[1]+h/2)])
                _region_pixel_zero(img2, center[-1], w, h)
    else:        
        for i in range(num):            
            maxval, maxloc = template_match(img2, img1, [], 0)
            if maxval < 0.96: return None
            center.append([int(maxloc[0]+w/2),int(maxloc[1]+h/2)])
            _region_pixel_zero(img2, center[-1], w, h)
    _image_rectangle(target_img, center, w, h,outfile)
    new_center = _sort_point_list(center)
    return new_center

    
if __name__ == '__main__':
    starttime = time.clock()
    #pts = locate_image('testdata/target.png', 'testdata/query.png',
                        #'testdata/DEBUG.png', 0.3)
    pts = locate_one_image_SIFT('testdata/target.png', 'testdata/query.png',
                        'testdata/DEBUG.png', 0.3)                        
    #pts = locate_more_image_SIFT('testdata/target.jpg', 'testdata/query.png',
                        #'testdata/DEBUG.png', 0.3, 7)
    #pts = locate_more_image_Template('testdata/target.png', 'testdata/query.png',
                        #'testdata/DEBUG.png', 0)
    endtime = time.clock()
    print "time: ", endtime - starttime
    print "center point: ", pts
