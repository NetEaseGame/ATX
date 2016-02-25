#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import subprocess
import random
import string
import time
import logging
import threading

random.seed(time.time())
logging.basicConfig(format = '%(asctime)s - %(levelname)s: %(message)s', level = logging.DEBUG) 

def getLogger(name='root'):
    return logging.getLogger(name)

log = getLogger('base')

def makedirs(dirname):
    try:
        os.makedirs(dirname)
    except:
        pass

def dirname(name):
    if os.path.isabs(name):
        return os.path.dirname(name)
    return os.path.dirname(os.path.abspath(name))

def exec_cmd(*cmds, **kwargs):
    '''
    @arguments env=None, timeout=3
    may raise Error
    '''
    env = os.environ.copy()
    env.update(kwargs.get('env', {}))
    envcopy = {}
    for key in env: 
        try:
            envcopy[key] = str(env[key]).encode('utf-8') # fix encoding
        except:
            print 'IGNORE BAD ENV KEY:', repr(key)
    env = envcopy

    timeout = kwargs.get('timeout', 120)
    shell = kwargs.get('shell', False)
    try:
        import sh
        log.debug('RUN(timeout=%ds): %s'%(timeout, ' '.join(cmds)))
        if shell:
            cmds = list(cmds)
            cmds[:0] = ['bash', '-c']
        c = sh.Command(cmds[0])
        try:
            r = c(*cmds[1:], _err_to_out=True, _out=sys.stdout, _env=env, _timeout=timeout)
        except:
            log.error('EXEC_CMD error, cmd: %s'%(' '.join(cmds)))
            raise
    except ImportError:
        log.debug('RUN(timeout=XX): %s'%(' '.join(cmds)))
        if shell:
            cmds = ' '.join(cmds)
        r = subprocess.Popen(cmds, env=env, stdout=sys.stdout, stderr=sys.stderr, shell=shell)
        return r.wait()
    return 0

def check_output(cmd):
    #log.debug('CHECK_OUTPUT, cmd: %s' %(cmd))
    return subprocess.check_output(cmd, shell=True)
    
def random_name(name):
    out = []
    for c in name:
        if c == 'X':
            c = random.choice(string.ascii_lowercase)
        out.append(c)
    return ''.join(out)


def wait_until(fn, interval=0.5, max_retry=10, args=(), kwargs={}):
    '''
    @return True(when found), False(when not found)
    '''
    log.debug('start wait func: %s', fn.__name__)
    retry = 0
    while retry < max_retry:
        retry += 1
        ret = fn(*args, **kwargs)
        if ret:
            return ret
        log.debug('wait until: %s, sleep: %s', fn.__name__, interval)
        time.sleep(interval)
    return None
