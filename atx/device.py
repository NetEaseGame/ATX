#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# License under MIT

import subprocess
import collections
import os
import platform
import re
import sys
import time
import threading
import json
import warnings

from uiautomator import device as d
from uiautomator import Device as UiaDevice
import cv2
import aircv as ac

from . import base
from . import proto
from . import patch

from atx import consts
from atx import errors


FindPoint = collections.namedtuple('FindPoint', ['pos', 'confidence', 'method'])
log = base.getLogger('devsuit')

__dir__ = os.path.dirname(os.path.abspath(__file__))
__tmp__ = os.path.join(__dir__, '__cache__')

DISPLAY_RE = re.compile(
    '.*DisplayViewport{valid=true, .*orientation=(?P<orientation>\d+), .*deviceWidth=(?P<width>\d+), deviceHeight=(?P<height>\d+).*')

class Watcher(object):
    ACTION_TOUCH = 1 <<0
    ACTION_QUIT = 1 <<1

    def __init__(self):
        self._events = {}
        self.name = None

    def on(self, image, flags):
        self._events[image] = flags

    def hook(self, screen, d):
        for (img, flags) in self._events.items():
            ret = d.exists(img, screen=screen)
            if ret is None:
                continue

            # FIXME(ssx): Image match confidence should can set
            if ret.method == consts.IMAGE_MATCH_METHOD_TMPL:
                if ret.confidence < 0.9:
                    print("Skip confidence:", ret.confidence)
                    continue
            elif ret.method == consts.IMAGE_MATCH_METHOD_SIFT:
                matches, total = ret.confidence
                if 1.0*matches/total < 0.5:
                    continue
            if flags & Watcher.ACTION_TOUCH:
                print('trigger watch click', ret.pos)
                d.click(*ret.pos)
            if flags & Watcher.ACTION_QUIT:
                d.stop_watcher()


class CommonWrap(object):
    def __init__(self):
        self.image_match_method = consts.IMAGE_MATCH_METHOD_TMPL

    def _read_img(self, img):
        if isinstance(img, basestring):
            return ac.imread(img)
        # FIXME(ssx): need support other types
        return img

    def sleep(self, secs):
        secs = int(secs)
        for i in reversed(range(secs)):
            sys.stdout.write('\r')
            sys.stdout.write("sleep %ds, left %2ds" % (secs, i+1))
            sys.stdout.flush()
            time.sleep(1)
        sys.stdout.write("\n")

    def exists(self, img, screen=None):
        """Change if image exists

        Args:
            img: string or opencv image
            screen: opencv image, optional, if not None, screenshot will be called

        Returns:
            None or FindPoint

        Raises:
            TypeError: when image_match_method is invalid
        """
        search_img = self._read_img(img)
        if screen is None:
            screen = self.screenshot()
        
        # image match
        if self.image_match_method == consts.IMAGE_MATCH_METHOD_TMPL:
            ret = ac.find_template(screen, search_img)
        elif self.image_match_method == consts.IMAGE_MATCH_METHOD_SIFT:
            ret = ac.find_sift(screen, search_img, min_match_count=10)
        else:
            raise TypeError("Invalid image match method: %s" %(self.image_match_method,))

        if ret is None:
            return None
        position = ret['result']
        confidence = ret['confidence']
        log.info('match confidence: %s', confidence)
        return FindPoint(position, confidence, self.image_match_method)

    def touch_image(self, img, timeout=20.0, wait_change=False):
        """Simulate touch according image position

        Args:
            img: filename or an opencv image object
            timeout: float, if image not found during this time, ImageNotFoundError will raise.
            wait_change: wait until background image changed.
        Returns:
            None

        Raises:
            ImageNotFoundError: An error occured when img not found in current screen.
        """
        search_img = self._read_img(img)
        log.info('touch image: %s', img)
        start_time = time.time()
        found = False
        while time.time() - start_time < timeout:
            point = self.exists(search_img)
            if point is None:
                continue
            self._uiauto.click(*point.pos)
            found = True
            break

        # wait until click area not same
        if found and wait_change:
            start_time = time.time()
            while time.time()-start_time < timeout:
                screen_img = self.screenshot()
                ret = ac.find_template(screen_img, search_img)
                if ret is None:
                    break

        if not found:
            raise errors.ImageNotFoundError('Not found image %s' %(img,))

    def add_watcher(self, w, name=None):
        if name is None:
            name = time.time()
        self._watchers[name] = w
        w.name = name
        return name

    def remove_watcher(self, name):
        """Remove watcher from event loop
        Args:
            name: string watcher name

        Returns:
            None
        """
        self._watchers.pop(name, None)

    def remove_all_watcher(self):
        self._watchers = {}

    def watch_all(self, timeout=None):
        """Start watch and wait until timeout

        Args:
            timeout: float, optional

        Returns:
            None
        """
        self._run_watch = True
        start_time = time.time()
        while self._run_watch:
            if timeout is not None:
                if time.time() - start_time > timeout:
                    raise errors.WatchTimeoutError("Watch timeout %s" % (timeout,))
                log.debug("Watch time left: %.1fs", timeout-time.time()+start_time)
            self.screenshot()

    def stop_watcher(self):
        self._run_watch = False

class AndroidDevice(CommonWrap, UiaDevice):
    def __init__(self, serialno=None, **kwargs):
        self._host = kwargs.get('host', '127.0.0.1')
        self._port = kwargs.get('port', 5037)

        UiaDevice.__init__(self, serialno, **kwargs)
        # super(AndroidDevice, self).__init__(serialno, **kwargs)

        self._serial = serialno

        self._uiauto = super(AndroidDevice, self)
        self._minicap_params = None
        self._watchers = {}

        self.screenshot_method = consts.SCREENSHOT_METHOD_UIAUTOMATOR
        # self.dev = dev
        # self.appname = appname
        # self._devtype = devtype
        # self._inside_depth = 0

        # # default image search extentension and 
        # self._image_exts = ['.jpg', '.png']
        # self._image_dirs = ['.', 'image']

        # self._rotation = None # 0,1,2,3
        # self._tmpdir = 'tmp'
        # self._click_timeout = 20.0 # if icon not found in this time, then panic
        # self._delay_after_click = 0.5 # when finished click, wait time
        # self._screen_resolution = None

        # self._snapshot_file = None
        # self._keep_capture = False # for func:keepScreen,releaseScreen
        # # self._logfile = logfile
        # self._loglock = threading.Lock()
        # self._operation_mark = False

        # self._image_match_method = 'auto'
        # self._threshold = 0.3 # for findImage

        # # if self._logfile:
        # #     logdir = os.path.dirname(logfile) or '.'
        # #     if not os.path.exists(logdir):
        # #         os.makedirs(logdir)
        # #     if os.path.exists(logfile):
        # #         backfile = logfile+'.'+time.strftime('%Y%m%d%H%M%S')
        # #         os.rename(logfile, backfile)

        # # Only for android phone method=<adb|screencap>
        # def _snapshot_method(method):
        #     if method and self._devtype == 'android':
        #         self.dev._snapshot_method = method

        # self._snapshot_method = _snapshot_method
        #-- end of func setting

    def _tmp_filename(self, prefix='tmp-', ext='.png'):
        return '%s%s%s' %(prefix, time.time(), ext)

    def _get_minicap_params(self):
        """
        Used about 0.1s
        uiautomator d.info is now well working with device which has virtual menu.
        """
        w, h = (0, 0)
        for line in self.adb_shell('dumpsys display').splitlines():
            m = DISPLAY_RE.search(line, 0)
            if not m:
                continue
            w = int(m.group('width'))
            h = int(m.group('height'))
            # o = int(m.group('orientation'))
            w, h = min(w, h), max(w, h)
            self._minicap_params = '{x}x{y}@{x}x{y}/{r}'.format(
                x=w, y=h, r=d.info['displayRotation']*90)
            break
        else:
            raise errors.BaseError('Fail to get display width and height')
        return self._minicap_params
        
    def _minicap(self):
        phone_tmp_file = '/data/local/tmp/'+self._tmp_filename(ext='.jpg')
        local_tmp_file = os.path.join(__tmp__, self._tmp_filename(ext='.jpg'))
        command = 'LD_LIBRARY_PATH=/data/local/tmp /data/local/tmp/minicap -P {} -s > {}'.format(
            self._get_minicap_params(), phone_tmp_file)
        self.adb_shell(command)
        self.adbrun(['pull', phone_tmp_file, local_tmp_file])
        self.adb_shell(['rm', phone_tmp_file])
        img = cv2.imread(local_tmp_file)
        os.remove(local_tmp_file)
        return img

    def screenshot(self, filename=None):
        """
        Take screen snapshot

        Args:
            filename: filename where save to, optional

        Returns:
            cv2 Image object

        Raises:
            TypeError
        """
        screen = None
        if self.screenshot_method == consts.SCREENSHOT_METHOD_UIAUTOMATOR:
            tmp_file = os.path.join(__tmp__, self._tmp_filename())
            self._uiauto.screenshot(tmp_file)
            screen = cv2.imread(tmp_file)
            os.remove(tmp_file)
        elif self.screenshot_method == consts.SCREENSHOT_METHOD_MINICAP:
            screen = self._minicap()
        else:
            raise TypeError('Invalid screenshot_method')

        if filename:
            save_dir = os.path.dirname(filename) or '.'
            if not os.path.exists(save_dir):
                os.makedirs(save_dir)
            cv2.imwrite(filename, screen)

        # handle watchers
        for w in self._watchers.values():
            w.hook(screen, self)

        return screen

    def adbrun(self, command):
        '''
        Run adb command, for example: adbrun(['pull', '/data/local/tmp/a.png'])

        Args:
            command: string or list of string

        Returns:
            command output
        '''
        cmds = ['adb']
        if self._serial:
            cmds.extend(['-s', self._serial])
        cmds.extend(['-H', self._host, '-P', str(self._port)])

        if isinstance(command, list) or isinstance(command, tuple):
            cmds.extend(list(command))
        else:
            cmds.append(command)
        output = subprocess.check_output(cmds, stderr=subprocess.STDOUT)
        return output.replace('\r\n', '\n')
        # os.system(subprocess.list2cmdline(cmds))

    def adb_shell(self, command):
        '''
        Run adb shell command

        Args:
            command: string or list of string

        Returns:
            command output
        '''
        if isinstance(command, list) or isinstance(command, tuple):
            return self.adbrun(['shell'] + list(command))
        else:
            return self.adbrun(['shell'] + [command])

    def start_app(self, package_name):
        '''
        Start application

        Args:
            package_name: string like com.example.app1

        Returns:
            None
        '''
        self.adb_shell(['monkey', '-p', package_name, '-c', 'android.intent.category.LAUNCHER', '1'])
        return self

    def stop_app(self, package_name, clear=False):
        '''
        Stop application

        Args:
            package_name: string like com.example.app1
            clear: bool, remove user data

        Returns:
            None
        '''
        if clear:
            self.adb_shell(['pm', 'clear', package_name])
        else:
            self.adb_shell(['am', 'force-stop', package_name])
        return self

    def takeSnapshot(self, filename):
        '''
        Deprecated, use screenshot instead.
        '''
        warnings.warn("deprecated, use snapshot instead", DeprecationWarning)
        return self.screenshot(filename)

    # def __getattribute__(self, name):
    #     # print name
    #     v = object.__getattribute__(self, name)
    #     if isinstance(v, collections.Callable):
    #         objdict = object.__getattribute__(self, '__dict__')
    #         # print objdict

    #         def _wrapper(*args, **kwargs):
    #             objdict['_inside_depth'] += 1
    #             # log function call
    #             ret = v(*args, **kwargs)
    #             if objdict['_inside_depth'] == 1 and \
    #                 not v.__name__.startswith('_') and \
    #                     not v.__name__ == 'log':
    #                 self.log(proto.TAG_FUNCTION, dict(name=v.__name__, args=args, kwargs=kwargs))
    #             objdict['_inside_depth'] -= 1
    #             return ret
    #         return _wrapper
    #     return v

    # def _imfind(self, bgimg, search):
    #     method = self._image_match_method
    #     print 'match-method:', method
    #     imsrc, imsch = ac.imread(bgimg), ac.imread(search)
    #     if method == 'auto':
    #         point = ac.find(imsrc, imsch)
    #     elif method == 'template':
    #         res = ac.find_template(imsrc, imsch, self._threshold)
    #         if res:
    #             point, score = res
    #             print 'match result:', point, score
    #             return point
    #         return None

    #     elif method == 'sift':
    #         point = imtsift.find(search, bgimg)
    #     else:
    #         raise RuntimeError("Unknown image match method: %s" %(method))
    #     return point

    # def _imfindall(self, bgimg, search, maxcnt, sort):
    #     if not maxcnt:
    #         maxcnt = 0
    #     method = self._image_match_method
    #     imsrc, imsch = ac.imread(bgimg), ac.imread(search)
    #     if method == 'auto':
    #         points = ac.find_all(imsrc, imsch, maxcnt=5)
    #         # points = imtauto.locate_more_image_Template(search, bgimg, num=maxcnt)
    #     elif method == 'template':
    #         points = imttemplate.findall(search, bgimg, self._threshold, maxcnt=maxcnt)
    #     elif method == 'sift':
    #         points = imtsift.findall(search, bgimg, maxcnt=maxcnt)
    #     else:
    #         raise RuntimeError("Unknown image match method: %s" %(method))
    #     if sort:
    #         def cmpy((x0, y0), (x1, y1)):
    #             return y1<y0

    #         def cmpx((x0, y0), (x1, y1)):
    #             return x1<x1
    #         m = {'x': cmpx, 'y': cmpy}
    #         points.sort(cmp=m[sort])
    #     return points

    # def rotation(self):
    #     '''
    #     device orientation
    #     @return int
    #     '''
    #     # 通过globalSet设置的rotation
    #     if self._rotation:
    #         return self._rotation
    #     # 看dev是否有rotation方法
    #     if hasattr(self.dev, 'rotation'):
    #         return self.dev.rotation()
    #     # windows上的特殊处理
    #     if self._devtype == 'windows':
    #         return proto.ROTATION_0
    #     return proto.ROTATION_0

    # def _fix_point(self, (x, y)):
    #     w, h = self.shape() # in shape() the width always < height
    #     if self.rotation() % 2 == 1:
    #         w, h = h, w

    #     if isinstance(x, float) and x <= 1.0:
    #         x = int(w*x)
    #     if isinstance(y, float) and y <= 1.0:
    #         y = int(h*y)
    #     return (x, y)

    def _search_image(self, filename):
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

    def _save_screen(self, filename, random_name=True, tempdir=True):
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

    # def log(self, tag, message):
    #     if not self._logfile:
    #         return

    #     self._loglock.acquire()
    #     timestamp = time.time()
    #     try:
    #         dirname = os.path.dirname(self._logfile) or '.'
    #         if not os.path.exists(dirname):
    #             os.path.makedirs(dirname)
    #     except:
    #         pass
    #     with open(self._logfile, 'a') as file:
    #         data = dict(timestamp=int(timestamp), tag=tag, data=message)
    #         file.write(json.dumps(data) + '\n')
    #     self._loglock.release()

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
        for k, v in m.items():
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
        filepath = self._search_image(imgfile)
        
        log.debug('Locate image path: %s', filepath)
        
        screen = self._save_screen('screen-{t}-XXXX.png'.format(t=time.strftime("%y%m%d%H%M%S")))
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
        filepath = self._search_image(imgfile)
        screen = self._save_screen('find-XXXXXXXX.png')
        pts = self._imfindall(screen, filepath, maxcnt, sort)
        return pts

    def safeWait(self, imgfile, seconds=20.0):
        '''
        Like wait, but don't raise RuntimeError

        return None when timeout
        return point if found
        '''
        warnings.warn("deprecated, use safe_wait instead", DeprecationWarning)
        self.safe_wait(imgfile, seconds)

    def safe_wait(self, img, seconds=20.0):
        '''
        Like wait, but don't raise RuntimeError

        return None when timeout
        return point if found
        '''
        warnings.warn("deprecated, use safe_wait instead", DeprecationWarning)
        try:
            return self.wait(img, seconds)
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

    # def exists(self, imgfile):
        # return True if self.find(imgfile) else False

    # def click(self, img_or_point, timeout=None, duration=None):
    #     '''
    #     Click function
    #     @param seconds: float (if time not exceed, it will retry and retry)
    #     '''
    #     if timeout is None:
    #         timeout = self._click_timeout
    #     log.info('CLICK %s, timeout=%.2fs, duration=%s', img_or_point, timeout, str(duration))
    #     point = self._val_to_point(img_or_point)
    #     if point:
    #         (x, y) = point
    #     else:
    #         (x, y) = self.wait(img_or_point, timeout=timeout)
    #     log.info('Click %s point: (%d, %d)', img_or_point, x, y)
    #     self.dev.touch(x, y, duration)
    #     log.debug('delay after click: %.2fs', self._delay_after_click)

    #     # FIXME(ssx): not tested
    #     if self._operation_mark:
    #         if self._snapshot_file and os.path.exists(self._snapshot_file):
    #             img = ac.imread(self._snapshot_file)
    #             ac.mark_point(img, (x, y))
    #             cv2.imwrite(self._snapshot_file, img)
    #         if self._devtype == 'android':
    #             self.dev.adbshell('am', 'broadcast', '-a', 'MP_POSITION', '--es', 'msg', '%d,%d' %(x, y))

    #     time.sleep(self._delay_after_click)

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
        fpt = self._val_to_point(fpt)
        tpt = self._val_to_point(tpt)
        return self.dev.drag(fpt, tpt, duration)

    # def sleep(self, secs=1.0):
    #     '''
    #     Sleeps for the specified number of seconds

    #     @param secs: float (number of seconds)
    #     @return None
    #     '''
    #     log.debug('SLEEP %.2fs', secs)
    #     time.sleep(secs)

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
