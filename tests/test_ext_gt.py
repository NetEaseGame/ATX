#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# hzsunshx <2016-06-12>
# make sure only one phone connected to pc/

import time

import atx
from atx.ext.gt import GT


d = atx.connect()

def test_gt():
    gt = GT(d)
    gt.start_test('com.netease.my')
    print 'test started. wait 5s'
    time.sleep(10.0)
    gt.stop_and_save()
    print 'save perf data'
    # time.sleep(3.0)
    # gt.quit()


if __name__ == '__main__':
    test_gt()