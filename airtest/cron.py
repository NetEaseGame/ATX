# coding: utf-8

import uuid
import threading
import time
from . import patch

class Crontab(object):
    def __init__(self):
        self._tasks = {}
        self._running = False
        self._cycle = 3.0
        self._drain()

    def start(self):
        self._running = True

    def stop(self):
        self._running = False

    def running(self):
        return self._running

    def addfunc(self, func, *args, **kwargs):
        key = str(uuid.uuid4())
        self._tasks[key] = [func, args, kwargs]
        return key

    def delfunc(self, key):
        del(self._tasks[key])

    @patch.go
    def _drain(self):
        while True:
            if not self._running:
                time.sleep(1.5)
                continue
            for task in self._tasks.values():
                func, args, kwargs = task
                t = threading.Thread(target=func, args=args, kwargs=kwargs)
                t.daemon=True
                t.start()
            time.sleep(max(0.5, self._cycle))

if __name__ == '__main__':
    m = Crontab()
    def say(msg = 'hello'):
        print 'say:', msg
    m.addfunc(say, 'hi')
    key = m.addfunc(say, 'hey')
    m.start()
    time.sleep(2)
    m.delfunc(key)
    time.sleep(2)
    print 'stop', m.running()
    m.stop()
    time.sleep(2)

