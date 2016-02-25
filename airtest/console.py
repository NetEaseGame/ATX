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

@cli.command(help='Watch cpu, mem')
@click.option('--conf', default='air.json', type=click.Path(dir_okay=False), help='config file', show_default=True)
@click.option('-p', '--package', default=None, help='Package name which can get by air.test inspect, this is conflict with --conf')
@click.option('-n', '--interval', type=click.FLOAT, default=3, show_default=True, help='Seconds to wait between updates')
@click.option('-s', '--serialno', default='', help='Specify which android device to connect')
# @click.option('--bytes', '--human-readable', default=True, is_flag=True, help='Print size with human readable format')
# @click.option('--syscpu', is_flag=True, help='Print cpu info seperately')
@click.option('--csv', 'output_file', type=click.Path(dir_okay=False), help='Save output to file as csv format')
def watch(conf, package, interval, serialno, output_file):
    if not package:
        apk = _get_apk(conf, cache=True)
        package, _ = androaxml.parse_apk(apk)

    m = airtest.Monitor('android://'+serialno, package)

    outfd = None
    if output_file:
        outfd = open(output_file, 'wb')
        wr = csv.writer(outfd)
        
    mem_items = ['PSS', 'RSS', 'VSS']
    items = ['TIME', 'CPU'] + mem_items
    format = '%-12s'*len(items)
    # if syscpu:
    #     format += '%-12s'*2
    #     items += ['SYSAVGCPU', 'SYSALLCPU']

    print format % tuple(items)
    if outfd:
        wr.writerow(items)
    while True:
        time_start = time.time()
        values = []
        values.append(time.strftime('%H:%M:%S'))


        #cpu = app.dev.cpuinfo(package)
        values.append(str(m.cpu()))

        mem = m.memory()
        strvals = values[:]
        for item in mem_items:
            v = int(mem.get(item, 0))*1024
            # if human_readable:
            v_str = humanize.naturalsize(int(v))
            # else:
            # v_str = v
            strvals.append(v_str)
            values.append(round(v/1024.0/1024, 2))

        # if syscpu:
        #     syscpus = m.sys_cpu(True)
        #     cpustr = '|'.join([str(round(v, 2)) for v in syscpus])
        #     sysavg = sum(syscpus)/len(syscpus)
        #     values += [(round(sysavg, 2)), cpustr]
        #     strvals += [str(round(sysavg, 2)), cpustr]

        print format % tuple(strvals)
        if outfd:
            wr.writerow(values)
            # outfd.write((format + '\n') % tuple(values))
            # outfd.flush()

        sleep = interval - (time.time() - time_start)
        if sleep > 0:
            time.sleep(sleep)

@cli.command(help='Run GUI in browser')
@click.option('--workdir', default=os.getcwd(), type=click.Path(file_okay=False), help='working directory')
@click.option('-s', '--serialno', help='Specify which android device to connect')
@click.option('--reload', default=False, is_flag=True, help='For developer to auto reload code when code change')
def gui(workdir, serialno, reload):
    from . import webgui
    os.environ['WORKDIR'] = workdir
    import webbrowser
    webbrowser.open('http://localhost:5000')
    webgui.serve(use_reloader=reload)

def main():
	cli()
	
if __name__ == '__main__':
    main()

