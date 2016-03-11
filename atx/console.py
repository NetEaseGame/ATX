#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import re
import sys
import subprocess
import time
import urllib
import json
import platform
import csv

import airtest
import click
import humanize
from airtest import log2html as airlog2html
from airtest import androaxml

__debug = False

def _wget(url, filename=None):
    print 'DOWNLOAD:', url, '->', filename
    return urllib.urlretrieve(url, filename)

def _run(*args, **kwargs):
    if __debug:
        click.echo('Exec: %s [%s]' %(args, kwargs))
    kwargs['stdout'] = kwargs.get('stdout') or sys.stdout
    kwargs['stderr'] = kwargs.get('stderr') or sys.stderr
    p = subprocess.Popen(args, **kwargs)
    p.wait()

def _get_apk(config_file, cache=False):
    apk = None
    if os.path.exists(config_file):# compatiable with cli-1
        with open(config_file) as file:
            cfg = json.load(file)
            apk = cfg.get('apk')
            if not apk:
                apk = cfg.get('android', {}).get('apk_url') 
    
    if not apk:
        # sys.exit("Usage: air.test install <APK-PATH | APK-URL")
        apk = raw_input('Enter apk path or url: ')
        assert apk.lower().endswith('.apk')
        # FIXME: save to file
        with open(config_file, 'wb') as file:
            file.write(json.dumps({'apk': apk}))

    if re.match('^\w{1,2}tp://', apk):
        if cache and os.path.exists('tmp.apk'):
            return 'tmp.apk'
        _wget(apk, 'tmp.apk')
        apk = 'tmp.apk'
    return apk

@click.group()
@click.option('-v', '--verbose', is_flag=True, help='Show verbose information')
def cli(verbose=False):
    global __debug
    __debug = verbose

@cli.command(help='Check environment')
def doctor():
    # adb check
    print '>> check if contains multi adb.exe'
    paths = []
    for line in os.getenv('PATH').split(os.pathsep):
        if os.path.exists(os.path.join(line, 'adb' + '.exe' if platform.system() == 'Windows' else '')):
            paths.append(line)
    if len(paths) == 1:
        print 'Good'
    if len(paths) == 0:
        print 'No adb.exe found, download from: http://adbshell.com/download/'
    if len(paths) > 1:
        print 'adb found in %d paths, need to delete and keep one' % len(paths)
        for p in paths:
            print 'PATH:', p

@cli.command(help='Get package and activity name from apk')
@click.argument('apkfile', type=click.Path(exists=True))
def inspect(apkfile):
    pkg, act = androaxml.parse_apk(apkfile)
    click.echo('Package Name: "%s"' % pkg)
    click.echo('Activity: "%s"' % act)

@cli.command(help='Convert airtest.log to html')
@click.option('--logfile', default='log/airtest.log', help='airtest log file path',
        type=click.Path(exists=True, dir_okay=False), show_default=True)
@click.option('--listen', is_flag=True, help='open a web serverf for listen')
@click.option('--port', default=8800, help='listen port', show_default=True)
@click.argument('outdir', type=click.Path(exists=False, file_okay=False))
def log2html(logfile, outdir, listen, port):
    airlog2html.render(logfile, outdir)
    if listen:
        click.echo('Listening on port %d ...' % port)
        _run('python', '-mSimpleHTTPServer', str(port), cwd=outdir)

@cli.command(help='Take a picture of phone')
@click.option('--phoneno', help='If multi android dev connected, should specify serialno')
@click.option('--platform', default='android', type=click.Choice(['android', 'windows', 'ios']), show_default=True)
@click.option('--out', default='snapshot.png', type=click.Path(dir_okay=False),
        help='out filename [default: "snapshot.png"]', show_default=True)
def snapshot(phoneno, platform, out):
    try:
        app = airtest.connect(phoneno, device=platform)
        app.takeSnapshot(out)
    except Exception, e:
        click.echo(e)

@cli.command(help='Install apk to phone')
@click.option('--no-start', is_flag=False, help='Start app after successfully installed')
@click.option('--conf', default='air.json', type=click.Path(dir_okay=False), help='config file', show_default=True)
@click.option('-s', '--serialno', help='Specify which android device to connect')
@click.argument('apk', required=False)
def install(no_start, conf, serialno, apk):
    if not apk:
        apk = _get_apk(conf)
    adbargs = ['adb']
    if serialno:
        adbargs.extend(['-s', serialno])
    args = adbargs + ['install', '-r', apk]
    # install app
    _run(*args)

    if no_start:
        return
    pkg, act = androaxml.parse_apk(apk)
    args = adbargs + ['shell', 'am', 'start', '-n', pkg+'/'+act]
    _run(*args)

@cli.command(help='Uninstall package from device')
@click.option('--conf', default='air.json', type=click.Path(dir_okay=False), help='config file')
@click.option('-s', '--serialno', help='Specify which android device to connect')
@click.argument('apk', required=False)
def uninstall(conf, serialno, apk):
    if not apk:
        apk = _get_apk(conf, cache=True)
    pkg, act = androaxml.parse_apk(apk)
    args = ['adb']
    if serialno:
        args.extend(['-s', serialno])
    args += ['uninstall', pkg]
    _run(*args)


def main():
    cli()
    
if __name__ == '__main__':
    main()