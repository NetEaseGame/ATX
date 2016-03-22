# coding: utf-8
#

import atx
from PIL import Image

d = atx.connect('127.0.0.1:26944')
d.resolution = (720, 1280)
d.screenshot('screen.png')
bg = None #Image.open('hm.png')
print d.match('folder.png', bg)
nd = d.region(atx.Bounds(12, 324, 646, 418))
print d._bounds
print nd.match('folder.png', bg)