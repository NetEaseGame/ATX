#-*- encoding: utf-8 -*-

import time
import threading

from atx.device.android import AndroidDevice
from atx.adbkit.mixins import RotationWatcherMixin, MinicapStreamMixin

from atx.record.base import BaseRecorder, ScreenAddon, UixmlAddon
from atx.record.android_hooks import HookManager, HookConstants as HC
from atx.record.android_layout import AndroidLayout
from atx.imutils import from_pillow

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
                    'pyscript' : 'd.key_down("%s")' % (e.key,)
                }
        else:
            return
        self.case_draft.append(d)

class AndroidRecorder(BaseRecorder, ScreenAddon, UixmlAddon):
    def __init__(self, *args, **kwargs):
        self.hm = HookManager()
        super(AndroidRecorder, self).__init__(*args, **kwargs)
        self.hm.register(HC.GST_KEYPRESS, self.input_event)

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


if __name__ == '__main__':
    d = RecordDevice()
    rec = AndroidRecorder(d, 'testcase')
    rec.start()
    while True:
        try:
            time.sleep(1)
        except:
            break
    rec.stop()