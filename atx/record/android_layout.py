# -*- coding: utf-8 -*-
# hook only ui related events via uiautomator.
# the basic idea is find gesture target via postion.
# so we should simulate the layout via dumped ui tree.
# The ui hierarchy needs to be dumped repeatedly 
# and the process costs a rather long time.
# after each gesture we need to refresh the tree.


import re
import cv2
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

class AndroidLayout(object):
    def __init__(self):
        self.tree = None
        self.nodes = []
        self.rotation = 0
        self.focused_node = None

    def find_clickable_rect(self, x, y):
        def _find(node, x, y):
            if node.enabled and node.bounds.is_inside(x, y):
                for n in node.children[::-1]:
                    subnode = _find(n, x, y)
                    if subnode and subnode.clickable:
                        return subnode
                return node
        return _find(self.tree, x, y)

    def find_minimal_clickable_rect(self, x, y):
        for n in self.nodes:
            if n.enabled and n.clickable and n.bounds.is_inside(x, y):
                return n

    def find_scrollable_rect(self, x, y):
        for n in self.nodes:
            if n.enabled and n.scrollable and n.bounds.is_inside(x, y):
                return n

    def display(self):
        if not self.tree or not self.nodes:
            return
        b = self.tree.bounds
        l, t = b.left, b.top
        w, h = b.right - b.left, b.bottom - b.top
        img = np.zeros((h, w, 3), np.uint8)
        # highlight = np.zeros((h, w, 3), np.uint8)
        
        i = 0
        for n in self.nodes:
            if not n.clickable and not n.scrollable: continue
            b = n.bounds
            cv2.rectangle(img, (b.left-l, b.top-t), (b.right-l, b.bottom-t), (83, min(255, i*5), 18), 2)
            i += 1
        return img

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

    def parse_xmldata(self, xmldata):
        dom = xml.dom.minidom.parseString(xmldata)
        root = dom.documentElement
        self.rotation = int(root.getAttribute('rotation'))
        self.focused_node = None

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
            if uinode.focused:
                if self.focused_node is not None:
                    print 'Errorrrrrrr, more than one focused node.'
                self.focused_node = uinode
            return uinode

        self.nodes = []
        self.tree = walk(root, self.nodes)
        # self.nodes.sort(key=lambda x: x.depth, reverse=True)
        self.nodes.sort(key=lambda x: x.bounds.area)

if __name__ == '__main__':
    # import subprocess
    # subprocess.check_call('adb shell uiautomator dump /data/local/tmp/window_dump.xml')
    # subprocess.check_call('adb pull /data/local/tmp/window_dump.xml')
    # xmldata = open('window_dump.xml').read()

    import time
    import traceback

    from uiautomator import device
    device.dump()

    layout = AndroidLayout()
    layout.highlight = np.zeros((1, 1, 3), np.uint8)

    cv2.namedWindow("layout")

    def on_mouse(event, x, y, flags, param):
        layout, downpos, ismove = param

        # record downpos
        if event == cv2.EVENT_LBUTTONDOWN:
            print 'click at', x*2, y*2 # picture is half-sized.
            param[1] = (x, y)
            param[2] = False
            return
        # check if is moving
        if event == cv2.EVENT_MOUSEMOVE:
            if ismove: return
            if downpos is None:
                param[2] = False
                return
            _x, _y = downpos
            if (_x-x)**2 + (_y-y)**2 > 64:
                param[2] = True
            return
        if event != cv2.EVENT_LBUTTONUP: 
            return

        # update layout.highlight
        b = layout.tree.bounds
        l, t = b.left, b.top
        w, h = b.right - b.left, b.bottom - b.top
        highlight = np.zeros((h, w, 3), np.uint8)

        if downpos and ismove: # drag
            node = layout.find_scrollable_rect(x*2+l, y*2+t)
            print 'scroll to', x*2, y*2
            if node:
                b = node.bounds
                print 'scrolled node', b, node.index, node.class_name, 
                print 'resource_id:', node.resource_id, 
                print 'text:', node.text, 
                print 'desc:', node.content_desc
                cv2.rectangle(highlight, (b.left-l, b.top-t), (b.right-l, b.bottom-t), (0,255,255), 4)
        else:
            # node = layout.find_clickable_rect(x*2, y*2)
            node = layout.find_minimal_clickable_rect(x*2+l, y*2+t)
            if node:
                b = node.bounds
                print 'clicked node', b, node.index, node.class_name, 
                print 'resource_id:', node.resource_id, 
                print 'text:', node.text, 
                print 'desc:', node.content_desc
                print device(className=node.class_name, index=node.index).info
                cv2.rectangle(highlight, (b.left-l, b.top-t), (b.right-l, b.bottom-t), (0,0,255), 4)

        param[0].highlight = highlight
        param[1], param[2] = None, False

    cv2.setMouseCallback('layout', on_mouse, [layout, None, False])

    tic = time.time()
    count = 0
    package = None
    try:
        while True:
            xmldata = device.dump(pretty=False).encode('utf-8')
            layout.parse_xmldata(xmldata)
            if layout.tree.package != package:
                package = layout.tree.package
                print "change to", package

            img = layout.display()
            if img.shape == layout.highlight.shape:
                img += layout.highlight

            h, w = img.shape[:2]
            img = cv2.resize(img, (w/2, h/2))
            cv2.imshow('layout', img)
            cv2.waitKey(1)
            count += 1
    except:
        traceback.print_exc()

    toc = time.time()
    t = toc - tic
    print 'get %d dumps in %f seconds (%f each)' % (count, t, t/count)


