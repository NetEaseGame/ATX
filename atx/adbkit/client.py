#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import

import os
import re
import socket
import subprocess32 as subprocess

from atx.adbkit.device import Device

class Client(object):
    __adb_cmd = None

    def __init__(self, host='127.0.0.1', port=5037):
        """
        Args:
            - host: adb server host, default 127.0.0.1
            - port: adb server port, default 5037
        """
        self._host = host or '127.0.0.1'
        self._port = port or 5037

    @classmethod
    def adb_path(cls):
        """return adb binary full path"""
        if cls.__adb_cmd is None:
            if "ANDROID_HOME" in os.environ:
                filename = "adb.exe" if os.name == 'nt' else "adb"
                adb_cmd = os.path.join(os.environ["ANDROID_HOME"], "platform-tools", filename)
                if not os.path.exists(adb_cmd):
                    raise EnvironmentError(
                        "Adb not found in $ANDROID_HOME path: %s." % os.environ["ANDROID_HOME"])
            else:
                import distutils
                if "spawn" not in dir(distutils):
                    import distutils.spawn
                adb_cmd = distutils.spawn.find_executable("adb")
                if adb_cmd:
                    adb_cmd = os.path.realpath(adb_cmd)
                else:
                    raise EnvironmentError("$ANDROID_HOME environment not set.")
            cls.__adb_cmd = adb_cmd
        return cls.__adb_cmd

    def devices(self):
        '''get a dict of attached devices. key is the device serial, value is device name.'''
        out = subprocess.check_output([self.adb_path(), 'devices']).decode("utf-8")
        match = "List of devices attached"
        index = out.find(match)
        if index < 0:
            raise EnvironmentError("adb is not working.")
        return dict([s.split("\t") for s in out[index + len(match):].strip().splitlines() 
                if s.strip() and not s.strip().startswith('*')])

    @property    
    def _host_port_args(self):
        args = []
        if self._host:
            args += ['-H', self._host]
        if self._port:
            args += ['-P', str(self._port)]
        return args

    def raw_cmd(self, *args, **kwargs):
        '''adb command. return the subprocess.Popen object.'''
        cmds = [self.adb_path()] + self._host_port_args + list(args)
        # if os.name != "nt":
        #     cmd_line = [" ".join(cmd_line)]
        return subprocess.Popen(cmds, stdout=subprocess.PIPE, stderr=kwargs.get('stderr', subprocess.STDOUT))

    def version(self):
        '''
        Get version of current adb
        Return example:
            [u'1.0.32', u'1', u'0', u'32']
        '''
        '''adb version'''
        match = re.search(r"(\d+)\.(\d+)\.(\d+)", self.raw_cmd("version").communicate()[0].decode("utf-8"))
        return [match.group(i) for i in range(4)]

    def device(self, serial=None):
        devices = self.devices()
        if not serial:
            if devices:
                if len(devices) is 1:
                    serial = list(devices.keys())[0]
                else:
                    raise EnvironmentError("Multiple devices attached but default android serial not set.")
            else:
                raise EnvironmentError("Device not attached.")
        else:
            if serial not in devices:
                raise EnvironmentError("Device(%s) not attached." % serial)

        if devices[serial] != 'device':
            raise EnvironmentError("Device(%s) is not ready. status(%s)." % 
                (serial, devices[serial]))
        return Device(self, serial)

    def connect(self, addr):
        '''
        Call adb connect
        Return true when connect success
        '''
        if addr.find(':') == -1:
            addr += ':5555'
        output, _ = self.raw_cmd('connect', addr).communicate()
        return 'unable to connect' not in output

    def disconnect(self, addr):
        ''' disconnect device '''
        return self.raw_cmd('disconnect', addr).wait()

    def forward_list(self):
        '''
        adb forward --list
        TODO: not tested
        '''
        version = self.version()
        if int(version[1]) <= 1 and int(version[2]) <= 0 and int(version[3]) < 31:
            raise EnvironmentError("Low adb version.")
        lines = self.raw_cmd("forward", "--list").communicate()[0].decode("utf-8").strip().splitlines()
        return [line.strip().split() for line in lines]

    def forward(self, device_port, local_port=None):
        '''
        adb port forward. return local_port
        TODO: not tested
        '''
        if local_port is None:
            for s, lp, rp in self.forward_list():
                if s == self.device_serial() and rp == 'tcp:%d' % device_port:
                    return int(lp[4:])
            return self.forward(device_port, next_local_port(self.server_host))
        else:
            self.raw_cmd("forward", "tcp:%d" % local_port, "tcp:%d" % device_port).wait()
            return local_port


if __name__ == '__main__':
    adb = Client()
    print adb.devices()
    print adb.version()
