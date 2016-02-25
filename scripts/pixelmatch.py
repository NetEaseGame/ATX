# coding: utf-8
import cv2

method = cv2.TM_CCORR_NORMED
method = cv2.TM_SQDIFF_NORMED

def locate_img(image, template):
    img = image.copy()
    res = cv2.matchTemplate(img, template, method)
    print res
    print res.shape
    cv2.imwrite('image/shape.png', res)
    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)
    print cv2.minMaxLoc(res)
    if method in [cv2.TM_SQDIFF, cv2.TM_SQDIFF_NORMED]:
        top_left = min_loc
    else:
        top_left = max_loc
    h, w = template.shape
    bottom_right = (top_left[0] + w, top_left[1]+h)
    cv2.rectangle(img, top_left, bottom_right, 255, 2)
    cv2.imwrite('image/tt.jpg', img)

image = cv2.imread('image/mule_mobile.png', 0)
#image = cv2.imread('image/mule.png', 0)
template = cv2.imread('image/template.png', 0)
locate_img(image, template)
