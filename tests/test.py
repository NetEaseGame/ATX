# coding: utf-8

import os
import time
import atx
from atx import consts
print 'Version:', atx.version

d = atx.connect(None)

# print d.screenshot('screen.png')

def screenshot():
    # height = d.info['displayHeight']
    # height = 1920 # this is for my phone
    # params = '{x}x{y}@{x}x{y}/{r}'.format(
    #     x=d.info['displayWidth'], y=height, r=d.info['displayRotation'])
    # start = time.time()
    # command = 'LD_LIBRARY_PATH=/data/local/tmp /data/local/tmp/minicap -P {} -s > /data/local/tmp/screen2.png'.format(params)
    # # print d.touch_image('a.png')
    # d.shell(command)
    # os.system('adb pull /data/local/tmp/screen2.png')
    # print time.time()-start
    # Image now save in screen2.png
    # d._minicap()
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

    # # stop_app()
    #print 'inside'
    #screenshot()
    print d.dump_nodes()
    # w.on('setting.png', atx.Watcher.ACTION_TOUCH)
    # w.on('common.png', atx.Watcher.ACTION_TOUCH)

    # wid = d.add_watcher(w)
    # d.del_watcher(wid)
    # while 1:
    #     screenshot()
    # screenshot()
    # touch()
