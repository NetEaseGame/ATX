# -*- coding: utf-8 -*-
'''An Android-Debug-Bridge wrapper. 
With extra interact functions suported.

Basic Example:
>>> from atx import adb
>>> adb.version
Version(major=1, minor=0, server=32)
>>> adb.devices()
{'8ad789a2': 'device product:cancro model:MI_3W device:cancro'}
>>> adb.shell_getprop()
>>> adb.use(serial='abcdefgh', host='192.168.1.10', port=5039)
>>> adb.install('./test.apk')
>>> adb.uninstall('com.example.test')

Interactions Example
>>> adb.click(100, 100) # nothing happens
UserWarning: Empty function. Please call use_uiautomator or use_openstf first.
>>> adb.use_openstf()
>>> adb.click(100, 100)
>>> print adb.orientation()
0
>>> adb.screenshot('./test.png')
>>> img1 = adb.screenshot(format='pil')
>>> img2 = adb.screenshot(format='cv2')
'''

import os
import re
import sys
import time
import Queue
import socket
import struct
import warnings
import traceback
import threading
import subprocess
import collections
from PIL import Image
from functools import partial

__dir__ = os.path.dirname(os.path.abspath(__file__))

_serial = None
_default_serial = os.environ.get('ANDROID_SERIAL')
_host = DEFAULT_HOST = '127.0.0.1'
_port = DEFAULT_PORT = 5037

def _find_excutable():
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
    return adb_cmd

_adbexe = _find_excutable()

def _adb_server_cmd(*args):
    cmd = [_adbexe]
    if _host != DEFAULT_HOST:
        cmd.extend(['-H', _host])
    if _port != DEFAULT_PORT:
        cmd.extend(['-P', _port])
    cmd.extend(list(args))
    return subprocess.check_output(cmd)

def _version():
    '''local adb excutable version, cannot get remote server version.'''
    pat = re.compile('(?P<major>\d+)\.(?P<minor>\d+)\.(?P<server>\d+)')
    out = _adb_server_cmd('version')
    m = pat.search(out)
    class Version(collections.namedtuple('Version', ['major', 'minor', 'server'])):
        def __str__(self):
            return '%s.%s.%s' % (self.major, self.minor, self.server)
    d = dict([(k, int(v)) for k, v in m.groupdict().iteritems()])
    return Version(**d)

version = _version()

def _get_devices():
    '''use `adb devices` to refresh devices list.'''
    out = _adb_server_cmd('devices', '-l')
    match = "List of devices attached"
    index = out.find(match)
    if index < 0:
        raise EnvironmentError("adb is not working.")
    return dict([s.split(None, 1) for s in out[index + len(match):].strip().splitlines() 
            if s.strip() and not s.strip().startswith('*')])

devices = _get_devices

def use(serial=None, host=None, port=None):
    '''choose device to connect.'''
    global _serial, _host, _port
    if host is not None and host not in (DEFAULT_HOST, 'localhost'):
        _host = host
    if port is not None and port != DEFAULT_PORT:
        _port = port
    _devices = _get_devices()
    if len(_devices) == 0:
        warnings.warn('no devices found.')
        return
    if serial is None:
        if len(_devices) == 1:
            _serial = _devices.keys()[0]
        elif len(_devices) > 1:
            raise EnvironmentError('multiple device found! Please specify a serial.')
        return
    if serial not in _devices:
        raise EnvironmentError('device(%s) not attached!' % serial)
    _serial = serial

def connect(host, port=5555):
    _adb_server_cmd('connect', '%s:%s' % (host, port))

def disconnect(host=None, port=5555):
    if host is None: # disconnect everything
        print _adb_server_cmd('disconnect')
    else:
        print _adb_server_cmd('disconnect', '%s:%s' % (host, port))

def _adb_device_cmd(*args, **kwargs):
    '''run raw adb command, return subprocess.Popen object.'''
    cmd = [_adbexe]
    if _host != DEFAULT_HOST:
        cmd.extend(['-H', _host])
    if _port != DEFAULT_PORT:
        cmd.extend(['-P', _port])
    if _serial is None:
        use(None, _host, _port)
    cmd.extend(['-s', _serial])
    cmd.extend(list(args))

    if kwargs.get('stdin'):
        _stdin = subprocess.PIPE
    else:
        _stdin = None
    if kwargs.get('stdout'):
        _stdout = subprocess.PIPE
        if kwargs.get('err2out'):
            _stderr = subprocess.STDOUT
        else:
            _stderr = subprocess.PIPE
    else:
        _stdout, _stderr = None, None

    p = subprocess.Popen(cmd, stdin=_stdin, stdout=_stdout, stderr=_stderr)
    return p

def _adb_output(*args):
    p = _adb_device_cmd(*args, stdout=True)
    out, err = p.communicate()
    return out.strip()

def _adb_call(*args):
    p = _adb_device_cmd(*args)
    p.wait()

#------------------ adb device commands -------------------#

def push(local, remote, show_progress=False):
    _adb_call('push', local, remote)

def pull(remote, local, copymode=False, show_progress=False):
    cmd = ['pull']
    if copymode: cmd.append('-a')
    cmd += [remote, local]
    _adb_call(*cmd)

def sync(local, sub=''):
    if sub not in ('', 'system', 'vendor', 'oem', 'data'):
        print 'sync device directory should be empty or one of (system, vendor, oem, data)'
        return
    if not os.path.isdir(local):
        print 'cannot open local directory:', local
        return
    cmd = ['-p', local, 'sync']
    if sub: cmd.append(sub)
    _adb_call(*cmd)

def logcat():
    '''may need seperate functions'''
    raise NotImplementedError()

def forward(local, remote, rebind=False):
    cmd = ['forward']
    if not rebind:
        cmd.append('--no-rebind')
    try:
        local = int(local)
        local = 'tcp:%d' % local
    except:
        pass
    try:
        remote = int(remote)
        remote = 'tcp:%d' % remote
    except:
        pass
    cmd.extend([local, remote])
    _adb_call(*cmd)

def forward_list():
    if version.major <=1 and version.server < 31:
        raise EnvironmentError('Low adb version(%s)' % version)
    out = _adb_output('forward', '--list')
    return [line.strip().split() for line in out.splitlines()]

def forward_remove(local=None):
    if local is None: # remove all
        _adb_call('forward', '--remove-all')
        return
    try:
        local = int(local)
        local = 'tcp:%d' % local
    except:
        pass
    _adb_call('forward', '--remove', local)

def reverse(remote, local, rebind=False):
    cmd = ['reverse']
    if not rebind:
        cmd.append('--no-rebind')
    try:
        remote = int(remote)
        remote = 'tcp:%d' % remote
    except:
        pass
    try:
        local = int(local)
        local = 'tcp:%d' % local
    except:
        pass
    cmd.extend([remote, local])
    _adb_call(*cmd)

def reverse_list():
    out = _adb_output('reverse', '--list')
    return [line.strip().split() for line in out.splitlines()]

def reverse_remove(remote=None):
    if remote is None: # remove all
        _adb_call('reverse', '--remove-all')
        return
    try:
        remote = int(remote)
        remote = 'tcp:%d' % remote
    except:
        pass
    _adb_call('reverse', '--remove', remote)

def jdwp():
    '''no use?'''
    raise NotImplementedError()

def install(localfile):
    '''push and install'''
    _adb_call('install', '-rt', localfile)

def install_multiple(*localfiles):
    _adb_call('install-multiple', '-rt', *localfiles)

def uninstall(package_name, keepdata=False):
    if keepdata:
        _adb_call('uninstall', '-k', package_name)
    else:
        _adb_call('uninstall', package_name)

def bugreport():
    '''it took so long time...'''
    raise NotImplementedError()

#------------------ miscellaneous -------------------#
def rmfile(remote):
    _adb_call('shell', 'rm', remote)

def shell_uninstall(package_name):
    _adb_call('shell', 'pm', 'uninstall', package_name)

def shell_install(remote_path, force=False):
    _adb_call('shell', 'pm', 'install', '-rt', remote_path)

def getprops():
    pat = re.compile(r'\[(?P<key>.*?)\]:\s*\[(?P<value>.*)\]')
    out = _adb_output('shell', 'getprop')
    return dict(pat.findall(out))

def getprop(prop):
    return _adb_output('shell', 'getprop', prop)

def getabi():
    return getprop('ro.product.cpu.abi')

def getsdk():
    return int(getprop('ro.build.version.sdk'))

def wlan_ip():
    ip = getprop('dhcp.wlan0.ipaddress').strip()
    if ip:
        return ip
    out = _adb_output('shell', 'ifconfig', 'wlan0')
    m = re.search('inet addr:([\d\.]+) ', out)
    return m.groups()[0]

def start_app(package_name):
    _adb_call('monkey', '-p', package_name, '-c', 'android.intent.category.LAUNCHER', '1')

def stop_app(package_name, clear=False):
    if clear:
        _adb_call('shell', 'pm', 'clear', package_name)
    else:
        _adb_call('shell', 'pm', 'force-stop', package_name)

def get_current_app():
    '''return (package_name, activity)'''
    pat = re.compile('mFocusedApp=.*ActivityRecord{\w+ \w+ (?P<package>.*)/(?P<activity>.*) .*')
    out = _adb_output('shell', 'dumpsys', 'window', 'windows')
    match = pat.findall(out)
    if not match:
        return None
    return match[0]

def get_installed_pacakges():
    out = _adb_output('shell', 'pm', 'list', 'packages')
    packages = set()
    for line in out.splitlines():
        if not line.startswith('package:'): continue
        line = line.strip()
        packages.add(line[8:])
    return packages

def is_file_exists(remote_path):
    out = _adb_output('shell', 'ls', '"%s"' % remote_path)
    if 'No such file or directory' in out:
        return False
    # if 'Permission denied' in out:
    #     warnings.warn('Permission denied')
    #     return False
    return True

def patch_function(mod, fname, new):
    old = getattr(mod, fname, None)
    if not callable(new):
        raise TypeError('module method should be callable!')
    if old is not None and not callable(old):
        raise TypeError('module method "%s" is not callable' % (fname,))
    ## instancemethod not writable!!!
    # if callable(old):
    #     setattr(new, '__doc__', getattr(old, '__doc__'))
    setattr(mod, fname, new)

#------------------ interact functions place holder -------------------#
DISPLAY_PATTERN = re.compile(r'DisplayViewport{valid=true, .*orientation=(?P<orientation>\d+), .*deviceWidth=(?P<width>\d+), deviceHeight=(?P<height>\d+)')

def display():
    '''return device screen size'''
    w, h = 0, 0
    out = _adb_output('shell', 'dumpsys', 'display')
    matches = DISPLAY_PATTERN.findall(out)
    if matches:
        _, w, h = map(int, matches[0])
        w, h = min(w, h), max(w, h)
    return collections.namedtuple('Display', ['width', 'height'])(w, h)

def orientation():
    '''return device orientation.
    0: normal
    1: home key on the right
    2: home key on the top
    3: home key on the left'''
    o = 0
    out = _adb_output('shell', 'dumpsys', 'display')
    matches = DISPLAY_PATTERN.findall(out)
    if matches:
        o = int(matches[0][0])
    return o

def click(x, y):
    '''click on screen point (x, y)'''
    _adb_call('shell', 'input', 'tap', x, y)

def long_click(x, y):
    '''click on screen point (x, y)'''
    _adb_call('shell', 'input', 'tap', x, y)

def swipe(sx, sy, ex, ey, steps=100):
    '''swipe from (sx, sy) to (ex, ey)'''
    _adb_call('shell', 'input', 'swipe', sx, sy, ex, ey, steps*0.5) # duration(ms) 

def keyevent(keycode, longpress=False):
    _adb_call('shell', 'input', 'keyevent', keycode)

def dumpui(filename='window_dump.xml', compressed=None, pretty=True):
    '''dump device window and pull to local file.'''
    _adb_call('shell', 'uiautomator', 'dump', '/data/local/tmp/window_dump.xml')
    pull('/data/local/tmp/window_dump.xml', filename)
    content = open('window_dump.xml').read()
    # if filename:
    #     with open(filename, "wb") as f:
    #         f.write(content.encode("utf-8"))
    # if pretty and "\n " not in content:
    #     xml_text = xml.dom.minidom.parseString(content.encode("utf-8"))
    #     content = U(xml_text.toprettyxml(indent='  '))
    return content

def screenshot(filename=None, format='pil', scale=1.0):
    remote = '/data/local/tmp/screenshot.png'
    _adb_call('shell', 'screencap', '-p', remote)
    pull(remote, filename or 'screenshot.png')
    if format == 'cv2':
        import cv2
        return cv2.imread('screenshot.png')
    return Image('screenshot.png')

def input(text):
    # TODO: handle %s problem
    _adb_call('shell', 'input', 'text', '"%s"' % text)

#------------------ interact functions from uiautomator -------------------#

def use_uiautomator():
    import uiautomator
    _mod = sys.modules[__name__]

    def _uia():
        d = uiautomator.device
        if _serial == d.server.adb.default_serial:
            return d
        d = uiautomator.AutomatorDevice(serial=_serial, adb_server_host=_host, adb_server_port=_port)
        setattr(uiautomator, 'device', d)
        return d

    setattr(_mod, '_uia', _uia)

    def _uia_func(fname, *args, **kwargs): 
        func = getattr(_uia(), fname)
        func(*args, **kwargs)

    def _uia_display():
        d = _uia()
        w, h = d.width, d.height
        w, h = min(w, h), max(w, h)
        return collections.namedtuple('Display', ['width', 'height'])(w, h)
    patch_function(_mod, 'display', _uia_display)

    patch_function(_mod, 'orientation', partial(_uia_func, 'orientation'))
    patch_function(_mod, 'click', partial(_uia_func, 'click'))
    patch_function(_mod, 'long_click', partial(_uia_func, 'long_click'))
    patch_function(_mod, 'swipe', partial(_uia_func, 'swipe'))
    patch_function(_mod, 'dumpui', partial(_uia_func, 'dump'))
    patch_function(_mod, 'screenshot', partial(_uia_func, 'screenshot'))

    def _uia_keyevent(keycode):
        # keys=["home", "back", "left", "right", "up", "down", "center",
        #      "menu", "search", "enter", "delete", "del", "recent",
        #      "volume_up", "volume_down", "volume_mute", "camera", "power"]
        d = _uia()
        d.press(keycode)
    patch_function(_mod, 'keyevent', _uia_keyevent)

#------------------ interact functions from openstf -------------------#
def use_openstf(enabletouch=False, on_rotation=None, on_screenchange=None):
    _mod = sys.modules[__name__]

    def str2img(jpgstr):
        import numpy as np
        import cv2
        arr = np.fromstring(jpgstr, np.uint8)
        img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
        return img

    class MiniSTF(object):
        minicap_port = 1313
        minitouch_port = 1111

        def __init__(self, serial=None, enabletouch=False, on_rotation=None, on_screenchange=None):
            if serial is None:
                serial = _serial
            self.serial = serial
            self.start()

        def start(self):
            # watch screen
            self._screen = None
            self.sub_minicap = None
            def _on_screenchange(img):
                self._screen = img
                if callable(on_screenchange):
                    on_screenchange(self._screen)

            # watch rotation
            self._orientation = 0
            self.sub_rotationwatcher = None
            def _on_rotation(value):
                self._orientation = int(value)/90
                self.start_minicap(_on_screenchange)
                if callable(on_rotation):
                    on_rotation(self._orientation)
            self.watch_rotation(_on_rotation)

            # input touch
            self.sub_minitouch = None
            if enabletouch:
                self.touchqueue = Queue.Queue()
                self.start_minitouch()

        def __del__(self):
            '''stop all subprocesses'''
            self.sub_rotationwatcher.kill()
            self.sub_minicap.kill()
            if self.sub_minitouch is not None:
                self.sub_minitouch.kill()

        def orientation(self):
            return self._orientation

        def watch_rotation(self, listener):
            package_name = 'jp.co.cyberagent.stf.rotationwatcher'
            if package_name not in get_installed_pacakges():
                install(os.path.join(__dir__, 'vendor', 'RotationWatcher.apk'))

            if self.sub_rotationwatcher is not None:
                self.sub_rotationwatcher.kill()

            out = _adb_output('shell', 'pm', 'path', package_name)
            path = out.split(':')[-1]
            p = _adb_device_cmd('shell', 
                'CLASSPATH="%s"' % path, 
                'app_process',
                '/system/bin',
                '"jp.co.cyberagent.stf.rotationwatcher.RotationWatcher"', 
                stdout=True)
            self.sub_rotationwatcher = p

            queue = Queue.Queue()

            def _pull():
                while True:
                    line = p.stdout.readline().strip()
                    if not line:
                        if p.poll() is not None:
                            break
                        continue
                    queue.put(line)

            t = threading.Thread(target=_pull)
            t.setDaemon(True)
            t.start()

            def _listen():
                while True:
                    try:
                        time.sleep(0.005)
                        line = queue.get_nowait()
                        listener(line)
                    except Queue.Empty:
                        if p.poll() is not None:
                            break
                        continue
                    except:
                        pass

            t = threading.Thread(target=_listen)
            t.setDaemon(True)
            t.start()

        def start_minicap(self, listener):
            remote = '/data/local/tmp'
            if not is_file_exists('/'.join([remote, 'minicap'])):
                raise EnvironmentError('minicap not available')

            if self.sub_minicap is not None:
                self.sub_minicap.kill()

            w, h = display()
            params = '{x}x{y}@{x}x{y}/{r}'.format(x=w, y=h, r=self._orientation*90)
            p = _adb_device_cmd('shell', 
                        'LD_LIBRARY_PATH=/data/local/tmp', 
                        '/data/local/tmp/minicap', 
                        '-P %s' % params,
                        '-S',
                        stdout=True)
            self.sub_minicap = p
            time.sleep(1)

            port = self.minicap_port
            forward(port, 'localabstract:minicap')

            queue = Queue.Queue()

            # pull data from socket
            def _pull():
                # print 'start pull', p.pid, p.poll()
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                try:
                    s.connect(('127.0.0.1', port))
                    t = s.recv(24)
                    print 'minicap connected', struct.unpack('<2B5I2B', t)
                    while True:
                        frame_size = struct.unpack("<I", s.recv(4))[0]
                        trunks = []
                        recvd_size = 0
                        while recvd_size < frame_size:
                            trunk_size = min(8192, frame_size-recvd_size)
                            d = s.recv(trunk_size)
                            trunks.append(d)
                            recvd_size += len(d)
                        queue.put(''.join(trunks))
                except Exception as e:
                    if not isinstance(e, struct.error):
                        traceback.print_exc()
                    p.kill()
                finally:
                    forward_remove(port)
                    s.close()

            t = threading.Thread(target=_pull)
            t.setDaemon(True)
            t.start()

            def _listen():
                while True:
                    try:
                        time.sleep(0.005)
                        frame = queue.get_nowait()
                        img = str2img(frame)
                        listener(img)
                    except Queue.Empty:
                        if p.poll() is not None:
                            break
                        continue
                    except:
                        traceback.print_exc()

            t = threading.Thread(target=_listen)
            t.setDaemon(True)
            t.start()

        def start_minitouch(self):
            remote = '/data/local/tmp'
            if not is_file_exists('/'.join([remote, 'minitouch'])):
                raise EnvironmentError('minitouch not available')

            if self.sub_minitouch is not None:
                self.sub_minitouch.kill()

            self.sub_minitouch = p = _adb_device_cmd('shell', '/data/local/tmp/minitouch')
            port = self.minitouch_port
            forward(port, 'localabstract:minitouch')

            def send():
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                try:
                    s.connect(('127.0.0.1', port))
                    while True:
                        cmd = self.touchqueue.get() # wait here
                        if not cmd:
                            continue
                        elif cmd[-1] != '\n':
                            cmd += '\n'
                        try:
                            s.send(cmd)
                        except socket.error:
                            p.kill()
                            break
                except:
                    traceback.print_exc()
                finally:
                    s.close()
                    forward_remove(port)

            t = threading.Thread(target=send)
            t.setDaemon(True)
            t.start()

        def click(self, x, y):
            cmd = 'd 0 %d %d 30\nc\nu 0\nc\n' % (int(x), int(y))
            self.touchqueue.put(cmd)

        def long_click(self, x, y):
            cmd = 'd 0 %d %d 30\nc\n' % (int(x), int(y))
            self.touchqueue.put(cmd)
            time.sleep(0.05)
            cmd = 'u 0\nc\n' % (int(x), int(y))
            self.touchqueue.put(cmd)

        def swipe(self, sx, sy, ex, ey, steps=10):
            sx, sy, ex, ey = map(int, (sx, sy, ex, ey))
            dx = (ex-sx)/steps
            dy = (ey-sy)/steps
            send = self.touchqueue.put
            send('d 0 %d %d 30\nc\n' % (sx, sy))
            for i in range(steps-1):
                x, y = sx+(i+1)*dx, sy+(i+1)*dy
                send('m 0 %d %d 30\nc\n' % (x, y))
            send('u 0 %d %d 30\nc\nu 0\nc\n' % (ex, ey))

        def screenshot(self):
            return self._screen

    # re entrance
    if getattr(_mod, '_mini', None) is not None:
        if _mod._mini.serial == _serial:
            return
        else:
            _mod._mini.__del__()

    _mini = MiniSTF(enabletouch, on_rotation, on_screenchange)
    setattr(_mod, '_mini', _mini)

    patch_function(_mod, 'orientation', _mini.orientation)
    patch_function(_mod, 'screenshot', _mini.screenshot)

    if enabletouch:
        patch_function(_mod, 'click', _mini.click)
        patch_function(_mod, 'long_click', _mini.long_click)
        patch_function(_mod, 'swipe', _mini.swipe)