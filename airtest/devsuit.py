#!/usr/bin/env python
# -*- coding: utf-8 -*-

import collections
import os
import platform
import time
import threading
import json

import cv2
import aircv as ac

from . import base
from . import proto
from . import patch
from .image import sift as imtsift
from .image import template as imttemplate

log = base.getLogger('devsuit')

class DeviceSuit(object):
    def __init__(self, devtype, dev, logfile='log/airtest.log'):
        # print 'DEVSUIT_SERIALNO:', phoneno
        self.dev = dev
        # self.appname = appname
        self._devtype = devtype
        self._inside_depth = 0

        # default image search extentension and 
        self._image_exts = ['.jpg', '.png']
        self._image_dirs = ['.', 'image']

        self._rotation = None # 0,1,2,3
        self._tmpdir = 'tmp'
        self._click_timeout = 20.0 # if icon not found in this time, then panic
        self._delay_after_click = 0.5 # when finished click, wait time
        self._screen_resolution = None

        self._snapshot_file = None
        self._keep_capture = False # for func:keepScreen,releaseScreen
        self._logfile = logfile
        self._loglock = threading.Lock()
        self._operation_mark = False

        self._image_match_method = 'auto'
        self._threshold = 0.3 # for findImage


        if self._logfile:
            logdir = os.path.dirname(logfile) or '.'
            if not os.path.exists(logdir):
                os.makedirs(logdir)
            if os.path.exists(logfile):
                backfile = logfile+'.'+time.strftime('%Y%m%d%H%M%S')
                os.rename(logfile, backfile)

        # Only for android phone method=<adb|screencap>
        def _snapshot_method(method):
            if method and self._devtype == 'android':
                self.dev._snapshot_method = method

        self._snapshot_method = _snapshot_method
        #-- end of func setting

    def __getattribute__(self, name):
        # print name
        v = object.__getattribute__(self, name)
        if isinstance(v, collections.Callable):
            objdict = object.__getattribute__(self, '__dict__')
            # print objdict
            def _wrapper(*args, **kwargs):
                objdict['_inside_depth'] += 1
                # log function call
                ret = v(*args, **kwargs)
                if objdict['_inside_depth'] == 1 and \
                    not v.__name__.startswith('_') and \
                    not v.__name__ == 'log':
                    self.log(proto.TAG_FUNCTION, dict(name=v.__name__, args=args, kwargs=kwargs))
                objdict['_inside_depth'] -= 1
                return ret
            return _wrapper
        return v

    def _imfind(self, bgimg, search):
        method = self._image_match_method
        print 'match-method:', method
        imsrc, imsch = ac.imread(bgimg), ac.imread(search)
        if method == 'auto':
            point = ac.find(imsrc, imsch)
        elif method == 'template':
            res = ac.find_template(imsrc, imsch, self._threshold)
            if res:
                point, score = res
                print 'match result:', point, score
                return point
            return None

        elif method == 'sift':
            point = imtsift.find(search, bgimg)
        else:
            raise RuntimeError("Unknown image match method: %s" %(method))
        return point

    def _imfindall(self, bgimg, search, maxcnt, sort):
        if not maxcnt:
            maxcnt = 0
        method = self._image_match_method
        imsrc, imsch = ac.imread(bgimg), ac.imread(search)
        if method == 'auto':
            points = ac.find_all(imsrc, imsch, maxcnt=5)
            # points = imtauto.locate_more_image_Template(search, bgimg, num=maxcnt)
        elif method == 'template':
            points = imttemplate.findall(search, bgimg, self._threshold, maxcnt=maxcnt)
        elif method == 'sift':
            points = imtsift.findall(search, bgimg, maxcnt=maxcnt)
        else:
            raise RuntimeError("Unknown image match method: %s" %(method))
        if sort:
            def cmpy((x0, y0), (x1, y1)):
                return y1<y0
            def cmpx((x0, y0), (x1, y1)):
                return x1<x1
            m = {'x': cmpx, 'y': cmpy}
            points.sort(cmp=m[sort])
        return points

    def rotation(self):
        '''
        device orientation
        @return int
        '''
        # 通过globalSet设置的rotation
        if self._rotation:
            return self._rotation
        # 看dev是否有rotation方法
        if hasattr(self.dev, 'rotation'):
            return self.dev.rotation()
        # windows上的特殊处理
        if self._devtype == 'windows':
            return proto.ROTATION_0
        return proto.ROTATION_0

    def _fixPoint(self, (x, y)):
        w, h = self.shape() # in shape() the width always < height
        if self.rotation() % 2 == 1:
            w, h = h, w

        if isinstance(x, float) and x <= 1.0:
            x = int(w*x)
        if isinstance(y, float) and y <= 1.0:
            y = int(h*y)
        return (x, y)

    def _searchImage(self, filename):
        ''' Search image in default path '''
        if isinstance(filename, unicode) and platform.system() == 'Windows':
            filename = filename.encode('gbk')
            #filename = filename.encode('utf-8')
        basename, ext = os.path.splitext(filename)
        exts = [ext] if ext else self._image_exts
        for folder in self._image_dirs:
            for ext in exts:
                fullpath = os.path.join(folder, basename+ext)
                if os.path.exists(fullpath):
                    return fullpath
        raise RuntimeError('Image file(%s) not found in %s' %(filename, self._image_dirs))

    def _PS2Point(self, PS):
        '''
        Convert PS to point
        @return (x, y) or None if not found
        '''
        if isinstance(PS, basestring):
            PS = self.find(PS)
            if not PS:
                return None
        (x, y) = self._fixPoint(PS)#(PS[0], PS[1]))#(1L, 2L))
        return (x, y)

    def _saveScreen(self, filename, random_name=True, tempdir=True):
        # use last snapshot file
        if self._snapshot_file and self._keep_capture:
            return self._snapshot_file

        if random_name:
            filename = base.random_name(filename)
        if tempdir:
            filename = os.path.join(self._tmpdir, filename)

        parent_dir = os.path.dirname(filename) or '.'
        if not os.path.exists(parent_dir):
            base.makedirs(parent_dir)

        # FIXME(ssx): don't save as file, better store in memory
        self.dev.snapshot(filename)

        if tempdir:
            self.log(proto.TAG_SNAPSHOT, dict(filename=filename))
        self._snapshot_file = filename
        return filename

    def log(self, tag, message):
        if not self._logfile:
            return

        self._loglock.acquire()
        timestamp = time.time()
        try:
            dirname = os.path.dirname(self._logfile) or '.'
            if not os.path.exists(dirname):
                os.path.makedirs(dirname)
        except:
            pass
        with open(self._logfile, 'a') as file:
            data = dict(timestamp=int(timestamp), tag=tag, data=message)
            file.write(json.dumps(data) + '\n')
        self._loglock.release()

    def keepCapture(self):
        '''
        Use screen in memory
        '''
        self._keep_capture = True

    def releaseCapture(self):
        '''
        Donot use screen in memory (this is default behavior)
        '''
        self._keep_capture = False

    def takeSnapshot(self, filename):
        '''
        Take screen snapshot

        @param filename: string (base filename want to save as basename)
        @return string: (filename that really save to)
        '''
        savefile = self._saveScreen(filename, random_name=False, tempdir=False)
        return savefile

    def globalSet(self, *args, **kwargs):
        '''
        app setting, be careful you should known what you are doing.
        @parma m(dict): eg:{"threshold": 0.3}
        '''
        if len(args) > 0:
            m = args[0]
            assert isinstance(m, dict)
        else:
            m = kwargs
        for k,v in m.items():
            key = '_'+k
            if hasattr(self, key):
                item = getattr(self, key)
                if callable(item):
                    item(v)
                else:
                    setattr(self, key, v)
            else:
                print 'not have such setting: %s' %(k)

    def globalGet(self, key):
        '''
        get app setting
        '''
        if hasattr(self, '_'+key):
            return getattr(self, '_'+key)
        return None

    def startApp(self, appname, activity):
        '''
        Start app
        '''
        self.dev.start_app(appname, activity)

    def stopApp(self, appname):
        '''
        Stop app
        '''
        self.dev.stop_app(appname)

    def find(self, imgfile):
        '''
        Find image position on screen

        @return (point founded or None if not found)
        '''
        filepath = self._searchImage(imgfile)
        
        log.debug('Locate image path: %s', filepath)
        
        screen = self._saveScreen('screen-{t}-XXXX.png'.format(t=time.strftime("%y%m%d%H%M%S")))
        if self._screen_resolution:
            # resize image
            ow, oh = self._screen_resolution # original
            cw, ch = self.shape() # current
            (ratew, rateh) = cw/float(ow), ch/float(oh)

            im = cv2.imread(filepath, cv2.IMREAD_UNCHANGED)

            nim = cv2.resize(im, (0, 0), fx=ratew, fy=rateh)
            new_name = base.random_name('resize-{t}-XXXX.png'.format(t=time.strftime("%y%m%d%H%M%S")))
            filepath = new_name = os.path.join(self._tmpdir, new_name)
            cv2.imwrite(new_name, nim)
            # im.resize((int(ratew*rw), int(rateh*rh))).save(new_name)
            # filepath = new_name
        pt = self._imfind(screen, filepath)
        return pt

    def mustFind(self, imgfile):
        ''' 
        Raise Error if image not found
        '''
        pt = self.find(imgfile)
        if not pt:
            raise RuntimeError("Image[%s] not found" %(imgfile))
        return pt

    def findall(self, imgfile, maxcnt=None, sort=None):
        '''
        Find multi positions that imgfile on screen

        @maxcnt (int): max number of object restricted.
        @sort (string): (None|x|y) x to sort with x, small in front, None to be origin order
        @return list point that found
        @warn not finished yet.
        '''
        filepath = self._searchImage(imgfile)
        screen = self._saveScreen('find-XXXXXXXX.png')
        pts = self._imfindall(screen, filepath, maxcnt, sort)
        return pts

    def safeWait(self, imgfile, seconds=20.0):
        '''
        Like wait, but don't raise RuntimeError

        return None when timeout
        return point if found
        '''
        try:
            return self.wait(imgfile, seconds)
        except:
            return None

    def wait(self, imgfile, timeout=20):
        '''
        Wait until some picture exists
        @return position when imgfile shows
        @raise RuntimeError if not found
        '''
        log.info('WAIT: %s', imgfile)
        start = time.time()
        while True:
            pt = self.find(imgfile)
            if pt:
                return pt
            if time.time()-start > timeout: 
                break
            time.sleep(1)
        raise RuntimeError('Wait timeout(%.2f)', float(timeout))

    def exists(self, imgfile):
        return True if self.find(imgfile) else False

    def click(self, SF, timeout=None, duration=None):
        '''
        Click function
        @param seconds: float (if time not exceed, it will retry and retry)
        '''
        if timeout == None:
            timeout = self._click_timeout
        log.info('CLICK %s, timeout=%.2fs, duration=%s', SF, timeout, str(duration))
        point = self._PS2Point(SF)
        if point:
            (x, y) = point
        else:
            (x, y) = self.wait(SF, timeout=timeout)
        log.info('Click %s point: (%d, %d)', SF, x, y)
        self.dev.touch(x, y, duration)
        log.debug('delay after click: %.2fs' ,self._delay_after_click)

        # FIXME(ssx): not tested
        if self._operation_mark:
            if self._snapshot_file and os.path.exists(self._snapshot_file):
                img = ac.imread(self._snapshot_file)
                ac.mark_point(img, (x, y))
                cv2.imwrite(self._snapshot_file, img)
            if self._devtype == 'android':
                self.dev.adbshell('am', 'broadcast', '-a', 'MP_POSITION', '--es', 'msg', '%d,%d'%(x, y))

        time.sleep(self._delay_after_click)

    def center(self):
        '''
        Center position
        '''
        w, h = self.shape()
        return w/2, h/2
    
    def clickIfExists(self, imgfile):
        '''
        Click when image file exists

        @return (True|False) if clicked
        '''
        log.info('CLICK IF EXISTS: %s' %(imgfile))
        pt = self.find(imgfile)
        if pt:
            log.debug('click for exists %s', imgfile)
            self.click(pt)
            return True
        else:
            log.debug('ignore for no exists %s', imgfile)
            return False

    def drag(self, fpt, tpt, duration=0.5):
        ''' 
        Drag from one place to another place

        @param fpt,tpt: filename or position
        @param duration: float (duration of the event in seconds)
        '''
        fpt = self._PS2Point(fpt)
        tpt = self._PS2Point(tpt)
        return self.dev.drag(fpt, tpt, duration)

    def sleep(self, secs=1.0):
        '''
        Sleeps for the specified number of seconds

        @param secs: float (number of seconds)
        @return None
        '''
        log.debug('SLEEP %.2fs', secs)
        time.sleep(secs)

    def type(self, text):
        '''
        Input some text

        @param text: string (text want to type)
        '''
        self.dev.type(text)

    @patch.run_once
    def shape(self):
        '''
        Get device shape

        @return (width, height), width < height
        '''
        return sorted(self.dev.shape())

    def keyevent(self, event):
        '''
        Send keyevent (only support android and ios)

        @param event: string (one of MENU,BACK,HOME)
        @return nothing
        '''
        if hasattr(self.dev, 'keyevent'):
            return self.dev.keyevent(event)
        raise RuntimeError('keyevent not support')


