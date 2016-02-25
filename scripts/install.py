# coding: utf-8
#
'''
To install airtest, download get-airtest.py

    python get-airtest.py

Many requirements will be install automaticly.

    pycrypto-2.6.win32-py2.7
    pyparsing-2.0.2.win32-py2.7
    numpy-MKL-1.8.1.win32-py2.7
    python-dateutil-2.2.win32-py2.7
    matplotlib-1.3.1.win32-py2.7
    Pillow-2.4.0.win32-py2.7
    pip-1.5.6.win32-py2.7
    setuptools-5.4.2.win32-py2.7
    opencv-python-2.4.9.win32-py2.7
'''


import sys
import platform
import subprocess

CDN_PREFIX = 'http://goandroid.qiniudn.com/airtest/'


def log(msg):
    print '>>> LOG:', msg


def err(msg):
    print '>>> ERR:', msg
    raw_input('Press Enter to exit: ')
    sys.exit(1)


# Check
if not platform.system() == 'Windows':
    err('Script only support windows platform')

pyver = platform.python_version()
if not pyver.startswith('2.7'):
    err('Need python version 2.7.*, not %s' % (pyver))

try:
    import pip
except:
    log('Install pip')
    # import urllib
    # code = urllib.urlopen('https://bootstrap.pypa.io/get-pip.py').read()
    # exec code # Will exit, not a ok way.
    # print 'Next'
    code = subprocess.Popen(['easy_install', CDN_PREFIX+'7-pip-1.5.6.win32-py2.7.exe']).wait()
    if code == 0:
        subprocess.Popen(['python', sys.argv[0]]).wait()
        sys.exit(0)

installed = {}
for soft in pip.pip.get_installed_distributions():
    installed[soft.project_name] = soft.version


requirements = [
    ['pyparsing', '2.0.2', '2-pyparsing-2.0.2.win32-py2.7.exe'],
    ['numpy', '1.8.1', '3-numpy-MKL-1.8.1.win32-py2.7.exe'],
    ['python-dateutil', '2.2', '4-python-dateutil-2.2.win32-py2.7.exe'],
    ['matplotlib', '1.3.1', '5-matplotlib-1.3.1.win32-py2.7.exe'],
    ['pillow', '2.4.0', '6-Pillow-2.4.0.win32-py2.7.exe'],
    ['opencv-python', '2.4.9', '9-opencv-python-2.4.9.win32-py2.7.exe'],
    ['pycrypto', '2.6', '10-pycrypto-2.6.win32-py2.7.exe']
]
    #['setuptools', '5.4.2', '8-setuptools-5.4.2.win32-py2.7.exe'],

for name, ver, fname in requirements:
    if installed.get(name) == ver:
        print 'Already installed "%s"' % name
        continue
    #print installed.get(name), ver, name
    print 'Downloading', name, ver
    p = subprocess.Popen(['easy_install', CDN_PREFIX+fname])
    p.wait()

os.system('pip install -i http://pypi.douban.com/simple airtest')
