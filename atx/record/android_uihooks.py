# -*- coding: utf-8 -*-
# hook only ui related events via uiautomator.
# the basic idea is find gesture target via postion.
# so we should simulate the layout via dumped ui tree.
# The ui hierarchy needs to be dumped repeatedly 
# and the process costs a rather long time.
# after each gesture we need to refresh the tree.


import re
import cv2
import tempfile
import subprocess
import collections
import xml.dom.minidom
import numpy as np

from atx.device import Bounds
UINode = collections.namedtuple('UINode', [
    'xml', 'children', 'depth',
    'bounds', 
    'selected', 'checkable', 'clickable', 'scrollable', 'focusable', 'enabled', 'focused', 'long_clickable',
    'password',
    'class_name',
    'index', 'resource_id',
    'text', 'content_desc',
    'package'])

def parse_bounds(text):
    m = re.match(r'\[(\d+),(\d+)\]\[(\d+),(\d+)\]', text)
    if m is None:
        return None
    return Bounds(*map(int, m.groups()))

def str2bool(v):
    return v.lower() in ("yes", "true", "t", "1")

def convstr(v):
    return v.encode('utf-8')

def in_bounds(x, y, b):
    return b.left<x<b.right and b.top<y<b.bottom

class AndroidLayout(object):
    def __init__(self):
        self.tree = None
        self.nodes = []
        self.rotation = 0

    def find_clickable_rect(self, x, y):
        def _find(node, x, y):
            if node.enabled and in_bounds(x, y, node.bounds):
                for n in node.children[::-1]:
                    subnode = _find(n, x, y)
                    if subnode and subnode.clickable:
                        return subnode
                return node
        return _find(self.tree, x, y)


    def find_scrollable_rect(self, x, y):
        for n in self.nodes:
            if n.enabled and n.scrollable and in_bounds(x, y, n.bounds):
                return n

    def display(self):
        self.dump_nodes()
        if not self.tree or not self.nodes:
            return
        b = self.tree.bounds
        w, h = b.right - b.left, b.bottom - b.top
        img = np.zeros((h, w, 3), np.uint8)
        highlight = np.zeros((h, w, 3), np.uint8)
        
        i = 0
        for n in self.nodes:
            if not n.clickable and not n.scrollable: continue
            b = n.bounds
            cv2.rectangle(img, (b.left, b.top), (b.right, b.bottom), (83, min(255, i*5), 18), 2)
            i += 1

        global down, move
        down = None
        move = False
        def on_mouse(event, x, y, flags, param):
            global down, move
            if event == cv2.EVENT_LBUTTONDOWN:
                down, move = (x, y), False
                return
            if event == cv2.EVENT_MOUSEMOVE:
                if move: return
                if down is None:
                    move = False
                    return
                _x, _y = down
                if (_x-x)**2 + (_y-y)**2 > 64:
                    move = True
                return
            if event != cv2.EVENT_LBUTTONUP: return
            if down and move: # drag
                node = self.find_scrollable_rect(x*2, y*2)
                if node:
                    b = node.bounds
                    print 'scroll to', x*2, y*2, b, node.depth
                    cv2.rectangle(highlight, (b.left, b.top), (b.right, b.bottom), (0,255,255), 4)
            else:
                node = self.find_clickable_rect(x*2, y*2)
                if node:
                    b = node.bounds
                    print 'click at', x*2, y*2, b, node.depth
                    cv2.rectangle(highlight, (b.left, b.top), (b.right, b.bottom), (0,0,255), 4)
            down, move = None, False

        cv2.namedWindow("layout")
        cv2.setMouseCallback('layout', on_mouse)

        while True:
            try:
                disp = img + highlight
                disp = cv2.resize(disp, (w/2, h/2))
                cv2.imshow('layout', disp)
                cv2.waitKey(1)
            except KeyboardInterrupt:
                break

    def _parse_xml_node(self, node, depth=0):
        # ['bounds', 'checkable', 'class', 'text', 'resource_id', 'package']
        __alias = {
            'class': 'class_name',
            'resource-id': 'resource_id',
            'content-desc': 'content_desc',
            'long-clickable': 'long_clickable',
        }

        parsers = {
            'bounds': parse_bounds,
            'text': convstr,
            'class_name': convstr,
            'resource_id': convstr,
            'package': convstr,
            'checkable': str2bool,
            'scrollable': str2bool,
            'focused': str2bool,
            'clickable': str2bool,
            'enabled': str2bool,
            'selected': str2bool,
            'long_clickable': str2bool,
            'focusable': str2bool,
            'password': str2bool,
            'index': int,
            'content_desc': convstr,
        }
        ks = {}
        for key, value in node.attributes.items():
            key = __alias.get(key, key)
            f = parsers.get(key)
            if value is None:
                ks[key] = None
            elif f:
                ks[key] = f(value)
        for key in parsers.keys():
            ks[key] = ks.get(key)
        ks['children'] = []
        ks['depth'] = depth
        ks['xml'] = node

        return UINode(**ks)

    def dump_nodes(self):
        subprocess.check_call('adb shell uiautomator dump /data/local/tmp/window_dump.xml')
        subprocess.check_call('adb pull /data/local/tmp/window_dump.xml')
        xmldata = open('window_dump.xml').read()
        dom = xml.dom.minidom.parseString(xmldata)
        root = dom.documentElement
        self.rotation = int(root.getAttribute('rotation'))

        def walk(node, ui_nodes, depth=0):
            while len(node.childNodes) == 1 and node.getAttribute('bounds') == '':
                node = node.childNodes[0]
                depth += 1
            uinode = self._parse_xml_node(node, depth)
            for n in node.childNodes:
                sub = walk(n, ui_nodes, depth+1)
                if sub is not None:
                    uinode.children.append(sub)
            ui_nodes.append(uinode)
            return uinode

        self.nodes = []
        self.tree = walk(root, self.nodes)
        self.nodes.sort(key=lambda x: x.depth, reverse=True)

if __name__ == '__main__':
    layout = AndroidLayout()
    nodes = layout.dump_nodes()
    layout.display()  
