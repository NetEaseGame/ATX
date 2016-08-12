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

from atx.drivers import Bounds
__UINode = collections.namedtuple('UINode', [
    'xml', 'children', 'depth',
    'index', 'text', 'resourceId',
    'className', 'packageName', 'description',
    'checkable', 'checked', 'clickable', 'enabled', 'focusable', 'focused',
    'scrollable', 'longClickable', 'password', 'selected',
    'bounds'])
# make it hashable & traceble
class UINode(__UINode):
    parent=None
    iterindex = None
    def __hash__(self):
        return id(self)

# ignore text/description contains punctuation
txt_pat = re.compile(ur'^[a-zA-Z0-9 \u4e00-\u9fa5]+$')

def parse_bounds(text):
    m = re.match(r'\[(\d+),(\d+)\]\[(\d+),(\d+)\]', text)
    if m is None:
        return None
    return Bounds(*map(int, m.groups()))

def str2bool(v):
    return v.lower() in ("yes", "true", "t", "1")

def convstr(v):
    return v

class AndroidLayout(object):
    def __init__(self):
        self.tree = None
        self.nodes = []
        self.rotation = 0

    def find_node(self, x, y):
        for n in self.nodes:
            if n.enabled and n.bounds.is_inside(x, y):
                return n

    def find_clickable_node(self, x, y):
        for n in self.nodes:
            if n.enabled and n.clickable and n.bounds.is_inside(x, y):
                return n

    def find_scrollable_node(self, x, y):
        for n in self.nodes:
            if n.enabled and n.scrollable and n.bounds.is_inside(x, y):
                return n

    def display(self, showall=False):
        if not self.tree or not self.nodes:
            return
        b = self.tree.bounds
        l, t = b.left, b.top
        w, h = b.right - b.left, b.bottom - b.top
        img = np.zeros((h, w, 3), np.uint8)

        i = 0
        for n in self.nodes[::-1]:
            if not showall and not n.clickable and not n.scrollable: continue
            b = n.bounds
            cv2.rectangle(img, (b.left-l, b.top-t), (b.right-l, b.bottom-t), (83, min(255, i*5), 18), 2)
            i += 1
        return img

    def _parse_xml_node(self, node, depth=0):
        __alias = {
            'class': 'className',
            'package': 'packageName',
            'resource-id': 'resourceId',
            'content-desc': 'description',
            'long-clickable': 'longClickable',
        }

        parsers = {
            'index': int,
            'text': convstr,
            'resourceId': convstr,
            'className': convstr,
            'packageName': convstr,
            'description': convstr,
            'bounds': parse_bounds,
            'checkable': str2bool,
            'checked': str2bool,
            'clickable': str2bool,
            'enabled': str2bool,
            'focusable': str2bool,
            'focused': str2bool,
            'scrollable': str2bool,
            'longClickable': str2bool,
            'password': str2bool,
            'selected': str2bool,
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

        idx = [0]
        def walk(node, ui_nodes, depth=0):
            while len(node.childNodes) == 1 and node.getAttribute('bounds') == '':
                node = node.childNodes[0]
                depth += 1
            uinode = self._parse_xml_node(node, depth)
            uinode.iterindex = idx[0]
            idx[0] += 1
            for n in node.childNodes:
                sub = walk(n, ui_nodes, depth+1)
                if sub is not None:
                    uinode.children.append(sub)
                    sub.parent = uinode
            ui_nodes.append(uinode)
            return uinode

        self.nodes = []
        self.tree = walk(root, self.nodes)
        self.nodes.sort(key=lambda x: x.bounds.area)
        self.node_index = [n.iterindex for n in self.nodes]

    def find_selector(self, node):
        '''find condition for locate a node, return (postion_node, condition, order)'''
        return self.__find_selector_by_structure(node)
        # return self.__find_selector_by_attrbutes(node)
        # return self.__find_selector_by_score(node)

    def _filter_nodes(self, cond, nodes=None):
        if nodes is None:
            nodes = self.nodes
        res = []
        for n in nodes:
            match = True
            for k, v in cond.iteritems():
                attr = getattr(n, k)
                if isinstance(v, re._pattern_type) and \
                    isinstance(attr, basestring) and v.match(attr) is None:
                    match = False
                    break
                elif attr != v:
                    match = False
                    break
            if match:
                res.append(n)
        return res

    def get_index_node(self, idx):
        '''get node with iterindex `idx`'''
        idx = self.node_index.index(idx)
        return self.nodes[idx]

    def get_node_selector(self, n, sub=False):
        d = {}
        nodes = self.nodes

        # try text, text in subnode cannot be all numbers
        if n.text and txt_pat.match(n.text) and not (sub and n.text.isdigit()):
            d['text'] = n.text
            nodes = self._filter_nodes(d, nodes)
            if len(nodes) == 1:
                return d, None

        # try className, which is never blank
        d['className'] = n.className
        nodes = self._filter_nodes(d, nodes)
        if len(nodes) == 1:
            return d, None

        # try description, like text
        if n.description and txt_pat.match(n.description) and not (sub and n.description.isdigit()):
            d['description'] = n.description
            nodes = self._filter_nodes(d, nodes)
            if len(nodes) == 1:
                return d, None

        ## try resourceId, but on some phone the resourceId may not be available
        if n.resourceId:
            d['resourceId'] = n.resourceId
            nodes = self._filter_nodes(d, nodes)
            if len(nodes) == 1:
                return d, None

        # return order in selected nodes under condition d.
        return d, nodes.index(n)

    def __find_selector_by_structure(self, node):
        # try itself
        d, order = self.get_node_selector(node)
        if order is None:
            return node, d, None

        # try its non-clickable decendants
        decendants = []
        def walk(n):
            for c in n.children:
                if c.clickable: continue
                decendants.append(c)
                walk(c)
        walk(node)

        choices = []
        for n in decendants:
            sd, sorder = self.get_node_selector(n, True)
            choices.append((sorder or 0, -n.bounds.area, sorder, sd, n)) # add area to sort
        choices.sort()

        if choices:
            return choices[0][-1], choices[0][-2], choices[0][-3]

        # TODO
        # # try if its non-clickable parent
        # def is_decendant(n1, n2):
        #     '''check if n1 is decandant of n2'''
        #     for c in n2.children:
        #         if c == n1 or is_decendant(n1, c):
        #             return True
        #     return False
        #
        # p = node.parent
        # while p and not p.clickable:
        #     pd, porder = self.get_node_selector(p)
        #     if porder is None:
        #         print 'parent node', p.className
        #         for i in range(len(p.children)):
        #             c = p.children[i]
        #             if c == node or is_decendant(node, c):
        #                 print 'child', i, c==node, c.className, c.resourceId, c.text
        #         return pd, porder
        #     p = p.parent

        return node, d, order

    def __find_selector_by_attrbutes(self, node):
        # avoid repeat over same attr

        def attrs(n, name):
            '''get node attribute values'''
            res = set()
            v = getattr(n, name)
            if v: res.add(v)
            for subn in n.children:
                if subn.clickable: continue
                res.update(attrs(subn, name))
            return res

        def is_decendant(n1, n2):
            '''check if n1 is decandant of n2'''
            for c in n2.children:
                if c == n1 or is_decendant(n1, c):
                    return True
            return False

        candidates = {}
        def try_attr(top, attr, ignore_filter=None):
            for value in attrs(top, attr):
                if ignore_filter and ignore_filter(value):
                    continue
                tmp = self._filter_nodes({attr:value})
                if len(tmp) == 1:
                    return tmp[0], {attr:value}
                # save candidates
                for n in tmp:
                    if n == top or is_decendant(n, top):
                        candidates.setdefault(n, {})[attr] = len(tmp)
            return None, None

        # try className
        n, cond = try_attr(node, 'className')
        if n:
            return n, cond, None

        # try anything with a resourceId
        n, cond = try_attr(node, 'resourceId')
        if n:
            return n, cond, None

        # try anything with a text
        n, cond = try_attr(node, 'text', lambda s: txt_pat.match(s) is None)
        if n:
            return n, cond, None

        # try anything with a description
        n, cond = try_attr(node, 'description', lambda s: txt_pat.match(s) is None)
        if n:
            return n, cond, None

        print 'candidates:', candidates.values()

        # try combinations

        return node, self.get_node_selector(node)

    def __find_selector_by_score(self, node):
        # TODO
        # find candidate selectors and give a score
        candidates = {}

        def walk(n):
            info = {'depth': n.depth-node.depth}
            d, o = self.get_node_selector(n)
            info['selector'] = d
            info['order'] = o
            info['score'] = 0
            candidates[n] = info
            for c in n.children:
                if c.clickable: continue
                walk(c)
        walk(node)

        # get top score selector

if __name__ == '__main__':
    # import subprocess
    # subprocess.check_call('adb shell uiautomator dump /data/local/tmp/window_dump.xml')
    # subprocess.check_call('adb pull /data/local/tmp/window_dump.xml')
    # xmldata = open('window_dump.xml').read()

    import time
    import traceback
    import locale

    encoding = locale.getpreferredencoding()

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
            node = layout.find_scrollable_node(x*2+l, y*2+t)
            print 'scroll to', x*2, y*2
            if node:
                b = node.bounds
                print 'scrollable node', b, node.index, node.className,
                print 'resource_id:', node.resourceId,
                print 'text:', node.text.encode(encoding, 'ignore'),
                print 'desc:', node.description.encode(encoding, 'ignore')
                cv2.rectangle(highlight, (b.left-l, b.top-t), (b.right-l, b.bottom-t), (0,255,255), 4)
        else:
            node = layout.find_clickable_node(x*2+l, y*2+t)
            if node:
                b = node.bounds
                print 'clickable node', b, node.index, node.className,
                print 'resource_id:', node.resourceId,
                print 'text:', node.text.encode(encoding, 'ignore'),
                print 'desc:', node.description.encode(encoding, 'ignore')
                print device(className=node.className, index=node.index).info
                cv2.rectangle(highlight, (b.left-l, b.top-t), (b.right-l, b.bottom-t), (0,0,255), 4)
                cond, order = layout.find_selector(node)
                if cond:
                    print 'selector', cond, order
                    subnode = layout._filter_nodes(cond)[order or 0]
                    b = subnode.bounds
                    cv2.rectangle(highlight, (b.left-l, b.top-t), (b.right-l, b.bottom-t), (0,180,255), 4)

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
            if layout.tree.packageName != package:
                package = layout.tree.packageName
                print "change to", package

            img = layout.display()
            if img.shape == layout.highlight.shape:
                img += layout.highlight

            h, w = img.shape[:2]
            img = cv2.resize(img, (w/2, h/2))
            cv2.imshow('layout', img)
            # key = cv2.waitKey(10)
            # if key == 115:
            #     with open('%d-%s.xml' % (count, package), 'w') as f:
            #         print 'saved', count, package
            #         f.write(xmldata)
            cv2.waitKey(1)
            count += 1
    except:
        traceback.print_exc()

    toc = time.time()
    t = toc - tic
    if count > 0:
        print 'get %d dumps in %f seconds (%f each)' % (count, t, t/count)
    else:
        print 'get nothing.'
