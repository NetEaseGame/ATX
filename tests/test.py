# coding: utf-8

import airtest

print 'Version:', airtest.__version__

d = airtest.connect(None)
print d.screenshot('screen.png')
print d.touch_image('a.png')
