#-*- encoding: utf-8 -*-

from .android_hooks import AndroidInputHookManager
from atx.record.base import BaseRecorder

class AndroidRecorder(BaseRecorder):
    def __init__(self, device=None):
        super(WindowsRecorder, self).__init__(device)
        self.hm = AndroidInputHookManager()

    def attach(self, device):
        pass

    def detach(self):
        pass

    def run(self):
        pass

    def stop(self):
        pass