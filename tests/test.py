# coding: utf-8

import os
import time
import airtest

print 'Version:', airtest.version

d = airtest.connect(None)

# print d.screenshot('screen.png')

def screenshot():
    height = d.info['displayHeight']
    height = 1920 # this is for my phone
    params = '{x}x{y}@{x}x{y}/{r}'.format(
        x=d.info['displayWidth'], y=height, r=d.info['displayRotation'])
    start = time.time()
    command = 'LD_LIBRARY_PATH=/data/local/tmp /data/local/tmp/minicap -P {} -s > /data/local/tmp/screen2.png'.format(params)
    # print d.touch_image('a.png')
    d.shell(command)
    os.system('adb pull /data/local/tmp/screen2.png')
    print time.time()-start
    # Image now save in screen2.png

def start_app():
    d.start_app('com.netease.my')

def stop_app():
    d.stop_app('com.netease.my')

if __name__ == '__main__':
    # start_app()
    stop_app()