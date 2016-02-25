#!/usr/bin/env python
# -*- coding: utf-8 -*-

import time
import threading

from functools import partial

from . import base

log = base.getLogger('patch')

def thread_safe(f):
    '''
    add thread lock for function

    @thread_safe
    def sayhi(name):
        print 'Hi', name
    '''
    lock = threading.Lock()
    def wrapper(*args, **kwargs):
        lock.acquire()
        ret = f(*args, **kwargs)
        lock.release()
        return ret
    return wrapper

def run_once(f):
    ''' 
    Decorator: Make sure function only call once
    not thread safe

    @run_once
    def foo():
        print 'bar'
        return 1+2
    foo()
    foo() # 'bar' only print once
    '''
    def wrapper(*args, **kwargs):
        if not wrapper.has_run:
            wrapper.result = f(*args, **kwargs)
            wrapper.has_run = True
        return wrapper.result
    wrapper.has_run = False
    return wrapper

def attachmethod(target):
    '''
    Reference: https://blog.tonyseek.com/post/open-class-in-python/

    class Spam(object):
        pass

    @attach_method(Spam)
    def egg1(self, name):
        print((self, name))

    spam1 = Spam()
    # OpenClass 加入的方法 egg1 可用
    spam1.egg1("Test1")
    # 输出Test1
    '''
    if isinstance(target, type):
        def decorator(func):
            setattr(target, func.__name__, func)
    else:
        def decorator(func):
            setattr(target, func.__name__, partial(func, target))
    return decorator

def fuckit(fn):
    def decorator(*args, **kwargs):
        try:
            return fn(*args, **kwargs)
        except Exception as e:
            args = list(args).extend([k+'='+v for k, v in kwargs.items()])
            print 'function(%s(%s)) panic(%s). fuckit' %(fn.__name__, ' ,'.join(args), e)
            return None
    return decorator

def go(fn):
    '''
    Decorator
    '''
    def decorator(*args, **kwargs):
        log.info('begin run func(%s) in background', fn.__name__)
        t = threading.Thread(target=fn, args=args, kwargs=kwargs)
        t.setDaemon(True)
        t.start()
        return t
    return decorator

# test code
if __name__ == '__main__':
    @go
    def say_hello(sleep=0.3, message='hello world'):
        time.sleep(sleep)
        print message
        return None
    t1 = say_hello(0.1)
    t2 = say_hello(0.5, 'this message should not showed')
    t1.join()
