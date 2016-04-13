#-*- encoding: utf-8 -*-

from .android_hooks import HookManager, HookConstants
from atx.record.base import BaseRecorder

class AndroidRecorder(BaseRecorder):
    def __init__(self, device=None):
        self.hm = HookManager()
        super(AndroidRecorder, self).__init__(device)
        self.hm.register(HookConstants.TOUCH_UP, self._on_click)
        # self.hm.register(HookConstants.GST_DRAG, self._on_drag)
        # self.hm.register(HookConstants.GST_SWIPE, self._on_swipe)
        # self.hm.register(HookConstants.GST_PINCH, self._on_pinch)
        # self.hm.register(HookConstants.ANY_KEY, self._on_key)

    def attach(self, device):
        if self.device is not None:
            self.detach()
        self.device = device
        self.hm.set_serial(self.device._serial)

    def detach(self):
        self.unhook()
        self.device = None
        self.hm.set_serial(None)

    def hook(self):
        self.hm.hook()

    def unhook(self):
        self.hm.unhook()

    def _on_click(self, event):
        pos = (event.x, event.y)
        print 'touch on', pos
        self.on_click(pos)