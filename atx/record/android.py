#-*- encoding: utf-8 -*-

import bisect
import cv2
import os
import threading
import time

from atx.drivers import Bounds
from atx.drivers.android import AndroidDevice
from atx.adbkit.mixins import RotationWatcherMixin, MinicapStreamMixin

from atx.record.base import BaseRecorder, ScreenAddon, UixmlAddon
from atx.record.android_hooks import HookManager, HookConstants as HC, set_multitap
from atx.record.android_layout import AndroidLayout

class RotationAddon(object):
    __addon_name = 'rotation'

    def get_rotation(self, t):
        if self.device is None:
            return
        idx = bisect.bisect(self.device._rotation_cache, (t, 0, 0))
        if idx != 0:
            return self.device._rotation_cache[idx-1][-1]

    def save_rotation(self, data, dirpath, idx):
        return data

    def load_rotation(self, dirpath, data):
        return data

class RecordDevice(RotationWatcherMixin, MinicapStreamMixin, AndroidDevice):

    def __init__(self, *args, **kwargs):
        super(RecordDevice, self).__init__(*args, **kwargs)

        self._rotation_cache = []
        def on_rotation_change(v):
            self.open_minicap_stream()
            # add idx for sort
            if self._rotation_cache:
                idx = self._rotation_cache[-1][1] + 1
            else:
                idx = 0
            self._rotation_cache.append((time.time(), idx, v))

        self.open_rotation_watcher(on_rotation_change=on_rotation_change)

    def dumpui(self):
        xmldata = self._uiauto.dump(pretty=False)
        return xmldata

class AndroidAtomRecorder(BaseRecorder):
    '''record detailed events: TOUCH_UP, TOUCH_DOWN, TOUCH_MOVE, KEY_UP, KEY_DOWN'''

    def __init__(self, *args, **kwargs):
        self.hm = HookManager()
        super(AndroidAtomRecorder, self).__init__(*args, **kwargs)
        self.hm.register(HC.KEY_ANY, self.input_event)
        self.hm.register(HC.TOUCH_ANY, self.input_event)

    def attach(self, device):
        if self.device is not None:
            self.detach()
        self.device = device
        self.hm.set_serial(self.device.serial)

    def detach(self):
        self.unhook()
        self.device = None
        self.hm.set_serial(None)

    def hook(self):
        self.hm.hook()

    def unhook(self):
        self.hm.unhook()

    def analyze_frame(self, idx, event, status):
        e = event
        if e.msg == HC.TOUCH_MOVE:
            d = {
                'action' : 'touch_move',
                'args' : (e.slotid, e.x, e.y),
            }
        elif e.msg == HC.TOUCH_DOWN:
            d = {
                'action' : 'touch_down',
                'args' : (e.slotid, e.x, e.y),
            }
        elif e.msg == HC.TOUCH_UP:
            d = {
                'action' : 'touch_up',
                'args' : (e.slotid, e.x, e.y),
            }
        elif e.msg & HC.KEY_ANY:
            if e.msg & 0x01:
                d = {
                    'action' : 'key_down',
                    'args' : (e.key,),
                }
            else:
                d = {
                    'action' : 'key_up',
                    'args' : (e.key,),
                }
        else:
            return
        self.case_draft.append(d)

    def process_draft(self, d):
        tmpl = {
            'touch_move' : 'd.touch_move({:d}, {:d}, {:d})',
            'touch_down' : 'd.touch_down({:d}, {:d}, {:d})',
            'touch_up' : 'd.touch_up({:d}, {:d}, {:d})',
            'key_down' : 'd.key_down("{}")',
            'key_up' : 'd.key_up("{}")',
        }
        return tmpl[d['action']].format(*d['args'])

class AdbStatusAddon(object):
    __addon_name = 'adbstatus'
    __cmd_interval = 0.1
    __cmd_lock = None
    __cmd_thread = None

    __adbstatus_cache = []

    def get_adbstatus(self, t):
        if self.__cmd_thread is None:
            self.__start()
        with self.__cmd_lock:
            idx = bisect.bisect(self.__adbstatus_cache, (t, None))
            if idx != 0:
                return self.__adbstatus_cache[idx-1][1]

    def save_adbstatus(self, data, dirpath, idx):
        return data

    def load_adbstatus(self, dirpath, data):
        return data

    def __start(self):
        print 'start', self.__addon_name
        if self.__cmd_lock is None:
            self.__cmd_lock = threading.Lock()
        if self.__cmd_thread is not None:
            self.__cmd_thread._Thread_stop() # using __stop private method, not good
        self.__cmd_thread = t = threading.Thread(target=self.__cmd)
        t.setDaemon(True)
        t.start()

    def __cmd(self):
        cmd_maxnum = int(self.monitor_period/self.__cmd_interval)
        while True:
            self.__cmd_lock.acquire()
            try:
                time.sleep(self.__cmd_interval)
                if not self.running or self.device is None:
                    continue
                # tic = time.time()
                status = {
                    'activity' : self.__get_activity(),
                }
                self.__adbstatus_cache.append((time.time(), status))
                self.__adbstatus_cache = self.__adbstatus_cache[-cmd_maxnum:]
            finally:
                self.__cmd_lock.release()

    def __get_activity(self): # cost around 75ms
        try:
            package, activity = self.device.adb_device.current_app()
            return package + '/' + activity
        except:
            # traceback.print_exc()
            return

class AndroidRecorder(BaseRecorder, ScreenAddon, UixmlAddon, AdbStatusAddon, RotationAddon):
    def __init__(self, *args, **kwargs):
        self.hm = HookManager()
        self.uilayout = AndroidLayout()
        self.nonui_activities = set()
        self.scene_detector = kwargs.pop('scene_detector', None)

        super(AndroidRecorder, self).__init__(*args, **kwargs)
        self.hm.register(HC.KEY_ANY, self.on_key)
        self.hm.register(HC.GST_TAP, self.input_event)
        self.hm.register(HC.GST_SWIPE, self.input_event)
        self.hm.register(HC.GST_DRAG, self.input_event)

    def attach(self, device):
        if self.device is not None:
            self.detach()
        self.device = device
        self.hm.set_serial(self.device.serial)

    def detach(self):
        self.unhook()
        self.device = None
        self.hm.set_serial(None)

    def hook(self):
        self.hm.hook()

    def unhook(self):
        self.hm.unhook()

    def add_nonui_activity(self, activity):
        self.nonui_activities.add(activity)

    def remove_nonui_activity(self, activity):
        self.nonui_activities.discard(activity)

    def on_key(self, event):
        if not event.msg & 0x01: # key_up
            print 'KeyEvent', event.key
            self.input_event(event)

    def serialize_event(self, event):
        e = event
        if e.msg & HC.KEY_ANY:
            return {'action':'key_event', 'args':(e.key,)}
        if e.msg == HC.GST_TAP:
            x, y = e.points[0]
            return {'action':'click', 'args':(x, y)}
        if e.msg in (HC.GST_SWIPE, HC.GST_DRAG):
            sx, sy = e.points[0]
            ex, ey = e.points[1]
            return {'action':'swipe', 'args':(sx, sy, ex, ey)}

    def analyze_frame(self, idx, event, status):
        e = event
        d = {'frameidx': idx}
        if e.msg & HC.KEY_ANY:
            d['action'] = 'key_event'
            d['args'] = (e.key,)
            self.case_draft.append(d)
            return

        uixml = status['uixml']
        screen = status['screen']
        adbstatus = status['adbstatus']
        activity = adbstatus and adbstatus['activity'] or None
        rotation = status['rotation']

        analyze_ui = False
        if activity is not None and activity not in self.nonui_activities:
            if uixml is not None:
                self.uilayout.parse_xmldata(uixml)
                rotation = self.uilayout.rotation
                analyze_ui = True

        # default rotation
        if rotation is None:
            rotation = 0

        w, h = self.device_info['width'], self.device_info['height']

        if e.msg == HC.GST_TAP:
            x, y = touch2screen(w, h, rotation, e.points[0][0], e.points[0][1])

            found_ui = False
            if analyze_ui:
                node = self.uilayout.find_clickable_node(x, y)
                if node:
                    found_ui = True
                    pnode, selector, order = self.uilayout.find_selector(node)
                    d['action'] = 'click_ui'
                    d['args'] = (pnode.iterindex, )
                    d['extra'] = (selector, order)

            # try image first when uinode not found.
            if not found_ui:
                if screen is not None:
                    bounds = find_clicked_bound(screen, x, y)
                    d['action'] = 'click_image'
                    d['args'] = (x, y, tuple(bounds))
                else:
                    d['action'] = 'click'
                    d['args'] = (x, y)

        elif e.msg in (HC.GST_SWIPE, HC.GST_DRAG):
            sx, sy = touch2screen(w, h, rotation, e.points[0][0], e.points[0][1])
            ex, ey = touch2screen(w, h, rotation, e.points[1][0], e.points[1][1])
            d['action'] = 'swipe'
            d['args'] = (sx, sy, ex, ey)

        elif e.msg == HC.GST_PINCH_IN:
            #TODO
            pass

        else:
            return

        self.case_draft.append(d)

    def process_draft(self, d):
        if not d:
            return ''
        idx = int(d['frameidx'])
        frame = self.frames[idx]
        waittime = frame['waittime']
        if d['action'] == 'key_event':
            return 'd.keyevent("{}")'.format(*d['args'])
        elif d['action'] == 'click':
            return 'd.click({}, {})'.format(*d['args'])
        elif d['action'] == 'click_ui':
            if 'extra' in d:
                selector, order = d['extra']
            else:
                uixml = open(os.path.join(self.framedir, frame['status']['uixml'])).read()
                self.uilayout.parse_xmldata(uixml)
                pnode = self.uilayout.get_index_node(int(d['args'][0]))
                selector, order = self.uilayout.get_node_selector(pnode)
            if order is None:
                return 'd(%s).click(timeout=%d)' %\
                    (', '.join(['%s=u"%s"' % item for item in selector.iteritems()]), 100*(int(waittime*10)))
            else:
                return 'objs = d(%s)\nif objs.wait.exists(timeout=%d):\n    objs[%d].click()'  %\
                    (', '.join(['%s=u"%s"' % item for item in selector.iteritems()]), 100*(int(waittime*10)), order)
        elif d['action'] == 'click_image':
            x, y, bounds = d['args']
            x, y, bounds = int(x), int(y), map(int, bounds)
            desc = get_point_desc(x, y, bounds)
            screen = cv2.imread(os.path.join(self.framedir, frame['status']['screen']))
            l, t, w, h = bounds
            img = screen[t:t+h, l:l+w]
            imgname = '%d-click.%dx%d.%s.png' % (idx, self.device_info['width'], self.device_info['height'], desc)
            imgpath = os.path.join(self.casedir, imgname)
            cv2.imwrite(imgpath, img)
            return 'd.click_image("%s")' % (imgname,)
        elif d['action'] == 'swipe':
            sx, sy, ex, ey = d['args']
            if waittime == 0:
                return 'd.swipe(%s, %s, %s, %s, 10)' % (sx, sy, ex, ey)
            return 'time.sleep(%.2f)\nd.swipe(%s, %s, %s, %s, 10)' % (waittime, sx, sy, ex, ey)
        else:
            print 'unsupported action', d['action']
            return ''

def touch2screen(w, h, o, x, y):
    '''convert touch position'''
    if o == 0:
        return x, y
    elif o == 1: # landscape-right
        return y, w-x
    elif o == 2: # upsidedown
        return w-x, h-y
    elif o == 3: # landscape-left
        return h-y, x
    return x, y

def find_clicked_bound(img, x, y, size=200):
    maxy, maxx = img.shape[:2]
    size = min(size, maxx, maxy)
    l, r, t, b = x-size/2, x+size/2, y-size/2, y+size/2
    if l < 0:
        l = 0
    elif r > maxx:
        l = maxx-size
    if t < 0:
        t = 0
    elif b > maxy:
        t = maxy-size
    return Bounds(l, t, size, size)

def get_point_desc(x, y, bounds):
    l, t, w, h = bounds
    cx, cy = l+w/2, t+h/2
    desc = ''
    if x < cx:
        desc += 'L%d' % int((cx-x+0.0)*100/w)
    else:
        desc += 'R%d' % int((x-cx+0.0)*100/w)
    if y < cy:
        desc += 'T%d' % int((cy-y+0.0)*100/h)
    else:
        desc += 'B%d' % int((y-cy+0.0)*100/h)
    return desc

if __name__ == '__main__':
    # from atx.record.scene_detector import SceneDetector

    # disable multitap
    set_multitap(1)

    def test():
        d = RecordDevice()
        # detector = SceneDetector('txxscene')
        rec = AndroidRecorder(d, 'testcase', realtime_analyze=True)
        rec.add_nonui_activity('com.netease.txx.mi/com.netease.txx.Client')
        rec.start()
        while True:
            try:
                time.sleep(1)
            except:
                break
        rec.stop()

    if os.path.exists(os.path.join('testcase', 'case', 'case.json')):
        AndroidRecorder.process_casefile('testcase')
    elif os.path.exists(os.path.join('testcase', 'frames', 'frames.json')):
        AndroidRecorder.analyze_frames('testcase')
    else:
        test()
