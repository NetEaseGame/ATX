#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
2014/08/05 jiaqianghuai: create this code
"""

import os
import time
import cv2

DEBUG = os.getenv('DEBUG') == 'true'

#path check
def _path_check(image_path):
    if not os.path.exists(image_path):
        raise IOError(image_path + 'not exists')

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

def _cv2open(filename, arg=0):
    obj = cv2.imread(filename, arg)
    if not obj:
        raise IOError('cv2 read file error:'+filename)
    return obj

def find(search_file, image_file, threshold=0.7):
    '''
    Locate image position with cv2.templateFind

    Use pixel match to find pictures.

    Args:
        search_file(string): filename of search object
        image_file(string): filename of image to search on
        threshold: optional variable, to ensure the match rate should >= threshold

    Returns:
        A tuple like (x, y) or None if nothing found

    Raises:
        IOError: when file read error
    '''
    search = _cv2open(search_file)
    image  = _cv2open(image_file)

    w, h = search.shape[::-1]

    method = cv2.CV_TM_CCORR_NORMED
    res = cv2.matchTemplate(image, search, method)
    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)
    if method in [cv2.TM_SQDIFF, cv2.TM_SQDIFF_NORMED]:
        top_left = min_loc
    else:
        top_left = max_loc
    bottom_right = (top_left[0] + w, top_left[1] + h)
    middle_point = (top_left[0]+w/2, top_left[1]+h/2)
    print top_left, bottom_right
    return middle_point

    # if len(region_center):
    #     x = int(maxloc[0]+region_center[0]-source_width/2)
    #     y = int(maxloc[1]+region_center[1]-source_height/2)
    # else:
    #     [x,y] = maxloc
    # return max_val, [x,y]

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
    # query_img = cv2.imread(query, 1)  # queryImage
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
    pts = locate_more_image_Template('testdata/target.png', 'testdata/query.png',
                        'testdata/DEBUG.png', 1)
    endtime = time.clock()
    print "time: ", endtime - starttime
    print "center point: ", pts