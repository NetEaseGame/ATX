#-*- encoding: utf-8 -*-

import bisect
import cv2
import os
import threading
import time

from atx.device import Bounds
from atx.device.android import AndroidDevice
from atx.adbkit.mixins import RotationWatcherMixin, MinicapStreamMixin

from atx.record.base import BaseRecorder, ScreenAddon, UixmlAddon
from atx.record.android_hooks import HookManager, HookConstants as HC, set_multitap
from atx.record.android_layout import AndroidLayout

class RecordDevice(RotationWatcherMixin, MinicapStreamMixin, AndroidDevice):

    def __init__(self, *args, **kwargs):
        super(RecordDevice, self).__init__(*args, **kwargs)
        self.open_rotation_watcher(on_rotation_change=lambda v: self.open_minicap_stream())

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
                'pyscript' : 'd.touch_move(%d, %d, %d)' % (e.slotid, e.x, e.y),
            }
        elif e.msg == HC.TOUCH_DOWN:
            d = {
                'action' : 'touch_down',
                'args' : (e.slotid, e.x, e.y),
                'pyscript' : 'd.touch_down(%d, %d, %d)' % (e.slotid, e.x, e.y),
            }
        elif e.msg == HC.TOUCH_UP:
            d = {
                'action' : 'touch_up',
                'args' : (e.slotid, e.x, e.y),
                'pyscript' : 'd.touch_up(%d, %d, %d)' % (e.slotid, e.x, e.y),
            }
        elif e.msg & HC.KEY_ANY:
            if e.msg & 0x01:
                d = {
                    'action' : 'key_down',
                    'args' : (e.key,),
                    'pyscript' : 'd.key_down("%s")' % (e.key,)
                }
            else:
                d = {
                    'action' : 'key_up',
                    'args' : (e.key,),
                    'pyscript' : 'd.key_up("%s")' % (e.key,)
                }
        else:
            return
        self.case_draft.append(d)

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

class AndroidRecorder(BaseRecorder, ScreenAddon, UixmlAddon, AdbStatusAddon):
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
            return {'action':'keyevent', 'args':(e.key,)}
        if e.msg == HC.GST_TAP:
            x, y = e.points[0]
            return {'action':'touch', 'args':(x, y)}
        if e.msg in (HC.GST_SWIPE, HC.GST_DRAG):
            sx, sy = e.points[0]
            ex, ey = e.points[1]
            return {'action':'swipe', 'args':(sx, sy, ex, ey)}

    def analyze_frame(self, idx, event, status, waittime):
        e = event
        if e.msg & HC.KEY_ANY:
            d = {
                'action' : 'keyevent',
                'args' : (e.key,),
                'pyscript' : 'd.keyevent("%s")' % (e.key,)
            }
            self.case_draft.append(d)
            return

        uixml = status['uixml']
        screen = status['screen']
        adbstatus = status['adbstatus']
        activity = adbstatus['activity']

        analyze_ui = False
        if activity is not None and activity not in self.nonui_activities:
            if uixml is not None:
                self.uilayout.parse_xmldata(uixml)
                analyze_ui = True

        d = {}
        if event.msg == HC.GST_TAP:
            x, y = event.points[0]
            if analyze_ui:
                node = self.uilayout.find_clickable_node(x, y)
                if node:
                    selector, order = self.uilayout.find_selector(node)
                    d['action'] = 'click_ui'
                    d['args'] = (selector, order)
                    if order is None:
                        d['pyscript'] = 'd(%s).click(timeout=%d)' %\
                            (', '.join(['%s=u"%s"' % item for item in selector.iteritems()]), 100*(int(waittime*10)))
                    else:
                        d['pyscript'] = 'objs = d(%s)\nif objs.wait.exists(timeout=%d):\n    objs[%d].click()'  %\
                            (', '.join(['%s=u"%s"' % item for item in selector.iteritems()]), 100*(int(waittime*10)), order)
                else:
                    d['action'] = 'click'
                    d['args'] = (x, y)
                    d['pyscript'] = 'd.click(%s, %s)' % (x, y)
            elif screen is not None:
                d['action'] = 'click_image'
                img, bounds = find_clicked_img(screen, x, y)
                imgname = '%d-click.png' % (idx,)
                imgpath = os.path.join(self.draftdir, imgname)
                cv2.imwrite(imgpath, img)
                d['args'] = ((x, y), tuple(bounds))
                d['pyscript'] = 'd.click_image("%s")' % (imgname,)
            else:
                d['action'] = 'click'
                d['args'] = (x, y)
                d['pyscript'] = 'd.click(%s, %s)' % (x, y)

        elif event.msg in (HC.GST_SWIPE, HC.GST_DRAG):
            sx, sy = e.points[0]
            ex, ey = e.points[1]
            d['action'] = 'swipe'
            d['args'] = (sx, sy, ex, ey)
            d['pyscript'] = 'd.swipe(%s, %s, %s, %s, 10)' % (sx, sy, ex, ey)

        elif event.msg == HC.GST_PINCH_IN:
            #TODO
            pass

        else:
            return

        self.case_draft.append(d)

def find_clicked_img(img, x, y):
    bounds = Bounds(0, 0, 100, 100)
    return img, bounds

if __name__ == '__main__':
    # from atx.record.scene_detector import SceneDetector
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

    if os.path.exists(os.path.join('testcase', 'frames', 'frames.json')):
        AndroidRecorder.analyze_frames('testcase')
    else:
        test()
