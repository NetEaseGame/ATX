#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import

import os
import re
import socket
try:
    import subprocess32 as subprocess
except:
    import subprocess

from atx.adbkit.device import Device


LOCAL_PORT = 10300
_init_local_port = LOCAL_PORT - 1

def next_local_port(adb_host=None):
    """ find avaliable free port """
    def is_port_listening(port):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        result = s.connect_ex((str(adb_host) if adb_host else '127.0.0.1', port))
        s.close()
        return result == 0
    global _init_local_port
    _init_local_port = _init_local_port + 1 if _init_local_port < 32764 else LOCAL_PORT
    while is_port_listening(_init_local_port):
        _init_local_port += 1
    return _init_local_port


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

    @property
    def server_host(self):
        return self._host
    
    @classmethod
    def adb_path(cls):
        """return adb binary full path"""
        if cls.__adb_cmd is None:
            if "ANDROID_HOME" in os.environ:
                filename = "adb.exe" if os.name == 'nt' else "adb"
                adb_dir = os.path.join(os.environ["ANDROID_HOME"], "platform-tools")
                adb_cmd = os.path.join(adb_dir, filename)
                if not os.path.exists(adb_cmd):
                    raise EnvironmentError(
                        "Adb not found in $ANDROID_HOME/platform-tools path: %s." % adb_dir)
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

    @property    
    def _host_port_args(self):
        args = []
        if self._host and self._host != '127.0.0.1':
            args += ['-H', self._host]
        if self._port:
            args += ['-P', str(self._port)]
        return args

    def raw_cmd(self, *args, **kwargs):
        '''adb command. return the subprocess.Popen object.'''
        cmds = [self.adb_path()] + self._host_port_args + list(args)
        kwargs['stdout'] = kwargs.get('stdout', subprocess.PIPE)
        kwargs['stderr'] = kwargs.get('stderr', subprocess.PIPE)
        # if os.name != "nt":
        #     cmd_line = [" ".join(cmd_line)]
        return subprocess.Popen(cmds, **kwargs)

    def run_cmd(self, *args, **kwargs):
        p = self.raw_cmd(*args, **kwargs)
        return p.communicate()[0].decode('utf-8').replace('\r\n', '\n')

    def devices(self):
        '''get a dict of attached devices. key is the device serial, value is device name.'''
        out = self.run_cmd('devices') #subprocess.check_output([self.adb_path(), 'devices']).decode("utf-8")
        if 'adb server is out of date' in out:
            out = self.run_cmd('devices')
        match = "List of devices attached"
        index = out.find(match)
        if index < 0:
            raise EnvironmentError("adb is not working.")
        return dict([s.split("\t") for s in out[index + len(match):].strip().splitlines() 
                if s.strip() and not s.strip().startswith('*')])

    def version(self):
        '''
        Get version of current adb
        Return example:
            [u'1.0.32', u'1', u'0', u'32']
        '''
        '''adb version'''
        match = re.search(r"(\d+)\.(\d+)\.(\d+)", self.run_cmd("version"))
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
        output = self.run_cmd('connect', addr)
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
        lines = self.run_cmd("forward", "--list").strip().splitlines()
        return [line.strip().split() for line in lines]

    def forward(self, serial, local_port, remote_port=None):
        '''
        adb port forward. return local_port
        TODO: not tested
        '''
        # Shift args, because remote_port is required while local_port is optional
        if remote_port is None:
            remote_port, local_port = local_port, None
        if not local_port:
            for s, lp, rp in self.forward_list():
                if s == serial and rp == 'tcp:%d' % remote_port:
                    return int(lp[4:])
            return self.forward(serial, next_local_port(self.server_host), remote_port)
        else:
            print(serial, remote_port, local_port)
            self.raw_cmd("-s", serial, "forward", "tcp:%d" % local_port, "tcp:%d" % remote_port).wait()
            return local_port


if __name__ == '__main__':
    adb = Client()
    print(adb.devices())
    print(adb.version())
