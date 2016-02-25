#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''
convert log to html report
'''

import fuckit

import os
import sys
import json
import time
import shutil

import pystache
import markupsafe

from airtest import base

TIME_FORMAT = '%Y/%m/%d %H:%M:%S'

def render(logfile, htmldir):
    '''
    parse logfile and render it to html
    '''
    if not os.path.exists(logfile):
        sys.exit('logfile: %s not exists' %(logfile))
    if not os.path.exists(htmldir):
        os.makedirs(htmldir)
    cpus, items = [], []
    fpss = []
    mems = []
    imgs = []
    # The render data
    data = {
            'info': {
                'generated_time': time.strftime('%Y/%m/%d %H:%M:%S'),
            },
            'items': items, 
            'cpu_data': None,
            'mem_data': None,
            'images': imgs,
        }
    info = data.get('info')

    # Read log line by line
    from . import proto
    records = []
    for line in open(logfile):
        v = json.loads(line)
        r = {'time': time.strftime(TIME_FORMAT, time.localtime(v.get('timestamp')))}
        d = v.get('data', {})
        tag = v.get('tag')

        # Process Function, Snapshot, Memory, CPU ...
        if tag == proto.TAG_FUNCTION:
            tag = markupsafe.Markup('function')    
            args = map(json.dumps, d.get('args'))
            kwargs = [ '%s=%s' %(k, json.dumps(_v)) for k, _v in d.get('kwargs', {}).items() ]
            message = '<code style="color:green">%s(%s)</code>' %(d.get('name'), ', '.join(args+kwargs))
            message = markupsafe.Markup(message)
        elif tag == proto.TAG_SNAPSHOT:
            message = markupsafe.Markup("<img width=100%% src='%s'/>" % d.get('filename'))
        elif tag == proto.TAG_CPU:
            message = '%d%%' %(d)
            cpus.append([r, d])
        elif tag == proto.TAG_MEMORY:
            mems.append([r, d['PSS']])
            message = json.dumps(d)
        else:
            message = None
        
        if message:
            r['tag'] = tag
            r['message'] = message
            records.append(r)

    # Calculate average cpu and mem
    data['records'] = records
    def average(ss):
        if ss:
            return reduce(lambda x,y: x+y, [value for _,value in ss])/float(len(ss))
        return 0.0

    data['cpu_average'] = round(average(cpus), 2)
    data['mem_average'] = round(average(mems), 2)
    data['fps_average'] = round(average(fpss), 2)

    tmpldir = os.path.join(base.dirname(__file__), 'htmltemplate')
    for name in os.listdir(tmpldir):
        fullpath = os.path.join(tmpldir, name)
        outpath = os.path.join(htmldir, name)
        if os.path.isdir(fullpath):
            shutil.rmtree(outpath, ignore_errors=True)
            shutil.copytree(fullpath, outpath)
            continue
        if fullpath.endswith('.swp'):
            continue
        content = open(fullpath).read().decode('utf-8')
        out = pystache.Renderer(escape=markupsafe.escape).render(content, data)
        print fullpath
        with open(outpath, 'w') as file:
            file.write(out.encode('utf-8'))

        # store json data file, for other system
        with open(os.path.join(htmldir, 'data.json'), 'w') as file:
            json.dump(data, file)
    # Copy snapshots
    if htmldir != '.':
        shutil.rmtree(os.path.join(htmldir, 'tmp'), ignore_errors=True)
    shutil.copytree('tmp', os.path.join(htmldir, 'tmp'))

if __name__ == '__main__':
    render('testdata/airtest.log', 'tmp/out.html')
