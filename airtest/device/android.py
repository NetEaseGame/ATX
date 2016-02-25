#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''
basic operation for a game(like a user does)
'''

import json
import os
import re
import subprocess
import string
import StringIO
from functools import partial
from .adb.adbclient import AdbClient

from .. import patch, base
from .. import proto

DEBUG = os.getenv("AIRDEBUG")=="true"
log = base.getLogger('android')

__dir__ = os.path.dirname(os.path.abspath(__file__))

def str2any(s):
    if s.isdigit():
        return int(s)
    if s.lower() == 'true' or s.lower() == 'false':
        return s.lower() == 'true'
    return s

class Monitor(object):
    def __init__(self, serialno, pkgname):
        self._sno = serialno 
        self._pkg = pkgname
        def _adb(*args):
            return subprocess.check_output(['adb', '-s', self._sno] + list(args))
        self.adb = _adb
        self.adbshell = partial(_adb, 'shell')

    @patch.run_once
    def ncpu(self):
        ''' number of cpu '''
        output = self.adbshell('cat', '/proc/cpuinfo')
        matches = re.compile('processor').findall(output)
        return len(matches)

    def cpu(self, percpu=False):
        ''' cpu usage, range must be in [0, 100] '''      
        for line in StringIO.StringIO(self.adbshell('dumpsys', 'cpuinfo')):
            line = line.strip()
            # 0% 11655/im.yixin: 0% user + 0% kernel / faults: 10 minor
            if '/'+self._pkg+':' in line:
                return float(line.split()[0][:-1])/self.ncpu()
        return None

    def sys_cpu(self, percpu=False):
        ''' use air-native '''
        if percpu:
            output = self.adbshell(proto.AIRNATIVE, '-q', '-runjs', 
                'console.log(JSON.stringify(cpuPercent(300, true)))')
            return json.loads(output)
        else:
            output = self.adbshell(proto.AIRNATIVE, '-q', '-runjs', 
                'console.log(JSON.stringify(cpuPercent(300, false)))')
            return json.loads(output)[0]

    def battery(self):
        ''' use: adb shell dumpsys battery '''
        output = self.adbshell('dumpsys', 'battery')
        output = output[output.find('\n'):] # ignore the first line
        patten = re.compile('(\w[\w ]+):\s*([-\w\d]+)')
        ret = {}
        for key, val in patten.findall(output):
            ret[key] = str2any(val)
        return ret

    def memory(self):
        '''
        @description details view: http://my.oschina.net/goskyblue/blog/296798

        @param package(string): android package name
        @return dict: {'VSS', 'RSS', 'PSS'} (unit KB)
        '''
        ret = {}
        # VSS, RSS
        for line in StringIO.StringIO(self.adbshell('ps')):
            if line and line.split()[-1] == self._pkg:
                # USER PID PPID VSIZE RSS WCHAN PC NAME
                values = line.split()
                if values[3].isdigit() and values[4].isdigit():
                    ret.update(dict(VSS=int(values[3]), RSS=int(values[4])))
                else:
                    ret.update(dict(VSS=-1, RSS=-1))
                break
        else:
            log.error("mem get: adb shell ps error")
            return {}

        # PSS
        memout = self.adbshell('dumpsys', 'meminfo', self._pkg)
        pss = 0
        result = re.search(r'\(Pss\):(\s+\d+)+', memout, re.M)
        if result:
            pss = result.group(1)
        else:
            result = re.search(r'TOTAL\s+(\d+)', memout, re.M)
            if result:
                pss = result.group(1)
        ret.update(dict(PSS=int(pss)))
        return ret

    def sys_memory(self):
        '''
        unit KB
        '''
        output = self.adbshell('cat', '/proc/meminfo')
        match = re.compile('MemTotal:\s*(\d+)\s*kB\s*MemFree:\s*(\d+)', re.IGNORECASE).match(output)
        if match:
            total = int(match.group(1), 10)
            free = int(match.group(2), 10)
        else:
            total, free = 0, 0
        return dict(TOTAL=total, FREE=free)

class Device(object):
    def __init__(self, serialno, addr=''):
        self._snapshot_method = 'adb'
        self._serialno = serialno
        print 'SerialNo:', serialno

        if addr:
            host, port = addr.split(':')
            self.adbclient = AdbClient(serialno, hostname=host, port=int(port))
        else:
            self.adbclient = AdbClient(serialno)

        # self.adbclient, self._serialno = ViewClient.connectToDeviceOrExit(verbose=False, serialno=serialno, ignoreversioncheck=True)
        self.adbclient.setReconnect(True) # this way is more stable

        # self.vc = ViewClient(self.adbclient, serialno, autodump=False)

        def _adb(*args):
            if addr:
                return subprocess.check_output(['adb', '-H', host, '-P', port, '-s', self._serialno] + list(map(str, args)))
            return subprocess.check_output(['adb', '-s', self._serialno] + list(map(str, args)))
        self.adb = _adb
        self.adbshell = partial(_adb, 'shell')
      
        # try:
        #     if not self.adbclient.isScreenOn():
        #         self.adb.wake()
        # except:
        #     pass

        # install air-native
        airnative = os.path.join(__dir__, '../binfiles/air-native')
        md5sum = open(airnative+'.md5').read().strip()
        try:
            output = self.adbshell('md5', proto.AIRNATIVE)
            arr = string.split(output, maxsplit=1)
        except:
            arr = [None]
        if arr and md5sum != arr[0]:
            self.adb('push', airnative, proto.AIRNATIVE)
            self.adbshell('chmod', '755', proto.AIRNATIVE)

        self._init_adbinput()

    def _init_adbinput(self):
        apkfile = os.path.join(__dir__, '../binfiles/adb-keyboard.apk')
        pkgname = 'com.android.adbkeyboard'
        if not self.adbshell('pm', 'path', pkgname).strip():
            print 'Install adbkeyboard.apk input method'
            self.adb('install', '-r', apkfile)

    def snapshot(self, filename):
        ''' save screen snapshot '''
        if self._snapshot_method == 'adb':
            log.debug('start take snapshot(%s)'%(filename))
            self.adbclient.display['orientation'] = self.rotation()
            pil = self.adbclient.takeSnapshot(reconnect=True)
            pil.save(filename)
        elif self._snapshot_method == 'screencap':
            # FIXME(ssx): image not rotate
            tmpname = '/data/local/tmp/airtest-tmp-snapshot.png'
            self.adbshell('screencap', '-p', tmpname)
            self.adb('pull', tmpname, filename)
            self.adbshell('rm', tmpname)
        else:
            raise RuntimeError("No such snapshot method: [%s]" % self._snapshot_method)


    def touch(self, x, y, duration=None):
        '''
        same as adb -s ${SERIALNO} shell input tap x y
        '''
        if not duration:
            self.adbshell('input', 'tap', x, y)
        else:
            self.adbshell(proto.AIRNATIVE, '-runjs', 'tap({x}, {y}, {dur})'.format(
                x=x, y=y, dur=int(duration*1000)))

    def drag(self, (x0, y0), (x1, y1), duration=0.5):
        '''
        Drap screen
        '''
        self.adbshell(proto.AIRNATIVE, '-runjs', 'drag({x0}, {y0}, {x1}, {y1}, {steps}, {dur})'.format(
            x0=x0, y0=y0, x1=x1, y1=y1, steps=10, dur=int(duration*1000)))
        # self.adb.drag((x0, y0), (x1, y1), duration)

    def rotation(self):
        '''
        dumpsys ref: http://imsardine.simplbug.com/note/android/adb/commands/dumpsys.html
        '''
        patten = re.compile('SurfaceOrientation:\s+(\d+)')
        output = self.adbshell('dumpsys', 'input')
        match = patten.search(output)
        if match:
            return int(match.group(1))
        return proto.ROTATION_0

    def shape(self):
        ''' 
        Get screen width and height, when landscape width > height
        '''
        width = self.adbclient.getProperty("display.width")
        height = self.adbclient.getProperty("display.height")
        return (width, height)

    def type(self, text):
        '''
        Input some text

        @param text: string (text want to type)
        '''
        log.debug('type text: %s', repr(text))
        adbime = 'com.android.adbkeyboard/.AdbIME'
        self.adbshell('ime', 'enable', adbime)
        self.adbshell('ime', 'set', adbime)
        first = True
        for s in text.split('\n'):
            if first:
                first=False
            else:
                KEYCODE_ENTER = '66'
                self.adbshell('am', 'broadcast', '-a', 'ADB_INPUT_CODE', '--ei', 'code', KEYCODE_ENTER)
            if not s:
                continue
            self.adbshell('am', 'broadcast', '-a', 'ADB_INPUT_TEXT', '--es', 'msg', s)
        self.adbshell('ime', 'disable', adbime)

    def keyevent(self, event):
        '''
        Send keyevent by adb

        @param event: string (one of MENU, HOME, BACK)
        '''
        self.adbshell('input', 'keyevent', str(event))

    def start_app(self, appname, activity):
        '''
        Start a program

        @param extra: dict (defined in air.json)
        '''
        self.adbshell('am', 'start', '-n', appname+'/'+activity)

    def stop_app(self, appname):
        '''
        Stop app
        '''
        self.adbshell('am', 'force-stop', appname)
    #
    # ------------ useless below -------------------
    #
    # def meminfo(self, appname):
    #     '''
    #     Retrive memory info for app
    #     @param package(string): android package name
    #     @return dict: {'VSS', 'RSS', 'PSS'} (unit KB)
    #     '''
    #     return _get_meminfo(self._serialno, appname)

    # def cpuinfo(self, appname):
    #     '''
    #     @param package(string): android package name
    #     @return dict: {'total': float, 'average': float}
    #     '''
    #     total = _get_cpuinfo(self._serialno, appname)
    #     ncpu=self._devinfo['cpu_count']
    #     return total/ncpu #dict(total=total, )


    # def clear(self, appname):
    #     '''
    #     Stop app and clear data
    #     '''
    #     self.adbshell('pm', 'clear', appname)

    # def getdevinfo(self):
    #     # cpu
    #     output = self.adbshell('cat', '/proc/cpuinfo')
    #     matches = re.compile('processor').findall(output)
    #     cpu_count = len(matches)
    #     # mem
    #     output = self.adbshell('cat', '/proc/meminfo')
    #     match = re.compile('MemTotal:\s*(\d+)\s*kB\s*MemFree:\s*(\d+)', re.IGNORECASE).match(output)
    #     if match:
    #         mem_total = int(match.group(1), 10)>>10 # MB
    #         mem_free = int(match.group(2), 10)>>10
    #     else:
    #         mem_total = -1
    #         mem_free = -1

    #     # brand = self.adb.getProperty('ro.product.brand')
    #     return {
    #         'cpu_count': cpu_count,
    #         'mem_total': mem_total,
    #         'mem_free': mem_free,
    #         'product_brand': self.adbclient.getProperty('ro.product.brand'),
    #         'product_model': self.adbclient.getProperty('ro.product.model')
    #         }
