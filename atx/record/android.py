#-*- encoding: utf-8 -*-

from .android_hooks import HookManager, HookConstants
from atx.record.base import BaseRecorder

class AndroidRecorder(BaseRecorder):
    def __init__(self, device=None):
        self.hm = HookManager()
        super(AndroidRecorder, self).__init__(device)
        self.hm.register(HookConstants.GST_TAP, self.on_click)
        self.hm.register(HookConstants.GST_DRAG, self.on_drag)
        self.hm.register(HookConstants.GST_SWIPE, self.on_swipe)
        self.hm.register(HookConstants.GST_PINCH, self.on_pinch)
        self.hm.register(HookConstants.ANY_KEY, self.on_key)

    def attach(self, device):
        if self.device is not None:
            self.detach()
        self.device = device
        self.hm.set_serial(self.device._serial)

    def detach(self):
        self.unhook()
        self.device = None

    def hook(self):
        self.hm.hook()

    def unhook(self):
        self.hm.unhook()