# coding: utf-8

import airtest

print 'Version:', airtest.__version__

app = airtest.connect(None)
print app.screenshot('screen.png')
