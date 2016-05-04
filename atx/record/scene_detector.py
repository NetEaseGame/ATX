#-*- encoding: utf-8 -*-

import os
import cv2
import yaml
import numpy as np
from collections import defaultdict

def find_match(img, tmpl, rect=None, mask=None):
    if rect is not None:
        h, w = img.shape[:2]
        x, y, x1, y1 = rect
        if x1 > w or y1 > h:
            return 0, None
        img = img[y:y1, x:x1, :]

        if mask is not None:
            img = img.copy()
            img[mask!=0] = 0
            tmpl = tmpl.copy()
            tmpl[mask!=0] = 0

    s_bgr = cv2.split(tmpl) # Blue Green Red
    i_bgr = cv2.split(img)

    weight = (0.3, 0.3, 0.4)
    resbgr = [0, 0, 0]
    for i in range(3): # bgr
        resbgr[i] = cv2.matchTemplate(i_bgr[i], s_bgr[i], cv2.TM_CCOEFF_NORMED)
    match = resbgr[0]*weight[0] + resbgr[1]*weight[1] + resbgr[2]*weight[2]
    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(match)
    confidence = max_val
    x, y = max_loc
    h, w = tmpl.shape[:2]
    if rect is None:
        rect = (x, y, x+w, y+h)
    # cv2.rectangle(img, (x,y), (x+w,y+h), (0,255,0) ,2)
    # cv2.imshow('test', img)
    # cv2.waitKey(20)
    return confidence, rect

def get_mask(img1, img2, thresh=20):
    if img1.shape != img2.shape:
        return
    diff = cv2.absdiff(img1, img2)
    diff = np.mean(diff, axis=2)
    diff[diff<=thresh] = 0
    diff[diff>thresh] = 255
    mask = np.dstack([diff]*3)
    return mask

def get_match_confidence(img1, img2, mask=None):
    if img1.shape != img2.shape:
        return False
    ## first try, using absdiff
    # diff = cv2.absdiff(img1, img2)
    # h, w, d = diff.shape
    # total = h*w*d
    # num = (diff<20).sum()
    # print 'is_match', total, num
    # return num > total*0.90
    if mask is not None:
        img1 = img1.copy()
        img1[mask!=0] = 0
        img2 = img2.copy()
        img2[mask!=0] = 0
    ## using match
    match = cv2.matchTemplate(img1, img2, cv2.TM_CCOEFF_NORMED)
    _, confidence, _, _ = cv2.minMaxLoc(match)
    # print confidence
    return confidence

class SceneDetector(object):
    '''detect game scene from screen image'''

    def __init__(self, scene_directory):
        self.scene_touches = {}
        self.scene_directory = scene_directory
        self.build_tree(scene_directory)

    def build_tree(self, directory):
        '''build scene tree from images'''
        confile = os.path.join(directory, 'config.yml')
        conf = {}
        if os.path.exists(confile):
            conf = yaml.load(open(confile).read())

        class node(defaultdict):
            name = ''
            parent = None
            tmpl = None
            rect = None
            mask = None

            def __str__(self):
                obj = self
                names = []
                while obj.parent is not None:
                    names.append(obj.name)
                    obj = obj.parent
                return '-'.join(names[::-1])

        def tree():
            return node(tree)

        root = tree()
        for s in os.listdir(directory):
            if not s.endswith('.png') or s.endswith('_mask.png'): 
                continue
            obj = root
            for i in s[:-4].split('-'):
                obj[i].name = i
                obj[i].parent = obj
                obj = obj[i]
            obj.tmpl = cv2.imread(os.path.join(directory, s))
            obj.rect = conf.get(s[:-4], {}).get('rect')
            maskimg = conf.get(s[:-4], {}).get('mask')
            if maskimg is not None:
                maskimg = os.path.join(directory, maskimg)
                if os.path.exists(maskimg):
                    obj.mask = cv2.imread(maskimg)

        self.tree = root
        self.current_scene = []
        self.confile = confile
        self.conf = conf

    def match_child(self, img, node):
        c, s, r = (0, None, None)
        for scene in node.itervalues():
            if scene.tmpl is None:
                continue
            print str(scene), scene.rect, img.shape
            confidence, rect = find_match(img, scene.tmpl, scene.rect, scene.mask)
            # print scene.name, confidence, rect
            if confidence > c:
                c, s, r = (confidence, scene, rect)

        if c > 0.95:
            key = str(s)
            if key not in self.conf:
                self.conf[key] = {}

            changed = False
            if c > self.conf[key].get('confidence', 0):
                s.rect = r
                self.conf[key]['confidence'] = c
                self.conf[key]['rect'] = list(r)
                changed = True

            if changed or s.mask is None:
                x, y, x1, y1 = r
                s.mask = get_mask(img[y:y1, x:x1, :], s.tmpl, 20)
                maskimg = os.path.join(self.scene_directory, '%s_mask.png' % key)
                cv2.imwrite(maskimg, s.mask)
                self.conf[key]['mask'] = maskimg
                changed = True

            if changed:
                self.save_config()

        return c, s, r

    def save_config(self):
        print 'save config', self.conf
        with open(self.confile, 'w') as f:
            yaml.dump(self.conf, f)

    def detect(self, img):
        # check current scene path        
        # print 'checking current scene'
        if self.current_scene:
            for i in range(len(self.current_scene)):
                s, r = self.current_scene[i]
                x, y, x1, y1 = r
                c = get_match_confidence(img[y:y1, x:x1, :], s.tmpl, s.mask)
                if c < 0.75:
                    break
            else:
                # print 'current scene ok'
                s = self.current_scene[-1][0]
                if len(s.values()) == 0:
                    return s
            self.current_scene = self.current_scene[:i]

        # top scene has changed
        if not self.current_scene:
            c, s, r = self.match_child(img, self.tree)
            if c < 0.75:
                return
            self.current_scene = [(s, r)]
        
        s = self.current_scene[-1][0]
        while True:
            c, s, r = self.match_child(img, s)
            if c < 0.75:
                break
            self.current_scene.append((s, r))

        return s