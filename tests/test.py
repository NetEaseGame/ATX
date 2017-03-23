# coding: utf-8

import os
import time
import atx
import logging
from atx import consts
print 'Version:', atx.version

d = atx.connect(None)

# 你好

def screenshot():
    start = time.time()
    #d.screenshot_method = consts.SCREENSHOT_METHOD_MINICAP
    d.screenshot('ttt.png')
    print time.time() - start

def start_app():
    d.start_app('com.netease.txx')

def stop_app():
    d.stop_app('com.netease.txx', clear=True)

def touch():
    d.screenshot_method = consts.SCREENSHOT_METHOD_MINICAP
    d.touch_image('button.png')

if __name__ == '__main__':
    log = logging.getLogger('atx')
    log.setLevel(logging.DEBUG)

    # d.screen.off()

    #def foo(evt):
        #print 'good', evt
        #d.click(*evt.pos)

    #with d.watch('simulator', 10) as w:
        #w.on(atx.Pattern("mmm.png", offset=(-79, -13))).do(foo).quit()
    # # stop_app()
    #print 'inside'
    #screenshot()
    # print d.dump_nodes()
    # w.on('setting.png', atx.Watcher.ACTION_TOUCH)
    # w.on('common.png', atx.Watcher.ACTION_TOUCH)

    # wid = d.add_watcher(w)
    # d.del_watcher(wid)
    # while 1:
    #     screenshot()
    # screenshot()
    # touch()
