#-*- encoding: utf-8 -*-

import os
import cv2
import time
import yaml
import numpy as np
from collections import defaultdict

def find_match(img, tmpl, rect=None, mask=None):
    if rect is not None:
        x, y, x1, y1 = rect
        img = img[y:y1, x:x1, :]

        if mask is not None:
            img = img.copy()
            img[mask] = 0
            tmpl = tmpl.copy()
            tmpl[mask] = 0

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
    diff[diff<=thresh] = 1
    diff[diff>thresh] = 0
    mask = np.dstack([diff]*3)
    return mask

def is_match(img1, img2):
    if img1.shape != img2.shape:
        return False
    ## first try, using absdiff
    # diff = cv2.absdiff(img1, img2)
    # h, w, d = diff.shape
    # total = h*w*d
    # num = (diff<20).sum()
    # print 'is_match', total, num
    # return num > total*0.65

    ## using match
    match = cv2.matchTemplate(img1, img2, cv2.TM_CCOEFF_NORMED)
    _, confidence, _, _ = cv2.minMaxLoc(match)
    # print confidence
    return confidence > 0.65

class SceneDetector(object):
    def __init__(self, scene_directory, device=None):
        self.scene_touches = {}
        self.build_tree(scene_directory)
        self.device = device

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
            if not s.endswith('.png'): continue
            obj = root
            for i in s[:-4].split('-'):
                obj[i].name = i
                obj[i].parent = obj
                obj = obj[i]
            obj.tmpl = cv2.imread(os.path.join(directory, s))
            obj.rect = conf.get(s[:-4], {}).get('rect')
            obj.mask = conf.get(s[:-4], {}).get('mask')

        self.tree = root
        self.cur_scene = None
        self.cur_rect = None
        self.confile = confile
        self.conf = conf

    def save_config(self):
        print 'save config', self.conf
        with open(self.confile, 'w') as f:
            yaml.dump(self.conf, f)

    def dectect(self):
        screen = self.device.screenshot_cv2()
        h, w = screen.shape[:2]
        img = cv2.resize(screen, (w/2, h/2))

        if self.cur_scene is not None:
            # print 'checking current scene'
            x, y, x1, y1 = self.cur_rect
            if is_match(img[y:y1, x:x1, :], self.cur_scene.tmpl):
                # print 'current scene ok'
                return self.cur_scene

        # print 'check all top level'
        s, c, r = None, 0, None
        for scene in self.tree.itervalues():
            if scene.tmpl is None:
                continue
            confidence, rect = find_match(img, scene.tmpl, scene.rect, scene.mask)
            # print scene.name, confidence, rect
            if confidence > c:
                c = confidence
                s = scene
                r = rect

        if c < 0.5:
            return
        if c > 0.95:
            s.rect = r
            if s.mask is None:
                x, y, x1, y1 = r
                s.mask = get_mask(img[y:y1, x:x1, :], s.tmpl, 25)

            key = str(s)
            if key not in self.conf:
                self.conf[key] = {}
            self.conf[key]['rect'] = list(r)
            self.conf[key]['confidence'] = c
            self.save_config()
        self.cur_scene = s
        self.cur_rect = r
        return s


if __name__ == '__main__':
    from atx.device.android_minicap import AndroidDeviceMinicap
    dev = AndroidDeviceMinicap()
    dev._adb.start_minitouch()
    time.sleep(3)
    m = SceneDetector('../../tests/txxscene', dev)
    old, new = None, None
    while True:
        # time.sleep(0.3)
        screen = m.device.screenshot_cv2()
        h, w = screen.shape[:2]
        img = cv2.resize(screen, (w/2, h/2))

        tic = time.clock()
        new = str(m.dectect_scene())
        t = time.clock() - tic
        if new != old:
            print 'change to', new
            print 'cost time', t
        old = new

        if m.cur_rect is not None:
            x, y, x1, y1 = m.cur_rect
            cv2.rectangle(img, (x,y), (x1,y1), (0,255,0) ,2)
        cv2.imshow('test', img)
        cv2.waitKey(1)