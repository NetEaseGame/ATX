#! /usr/bin/env python
# -*- coding: utf-8 -*-

import argparse
import uuid
import json
import inspect
import sys
import os
import time
from contextlib import contextmanager
from collections import defaultdict
from functools import partial

import tornado.web
import tornado.escape
from tornado import gen
from tornado.ioloop import IOLoop
from tornado.queues import Queue, QueueEmpty

import requests


class IndexHandler(tornado.web.RequestHandler):
    def get(self):
        self.write('Homepage')

    def delete(self):
        self.write('Quit')
        IOLoop.instance().stop()


class TaskQueueHandler(tornado.web.RequestHandler):
    ques = defaultdict(partial(Queue, maxsize=2))
    results = {}

    @gen.coroutine
    def get(self, udid):
        ''' get new task '''
        timeout = self.get_argument('timeout', 10.0)
        if timeout is not None:
            timeout = float(timeout)
        print timeout
        que = self.ques[udid]
        try:
            item = yield que.get(timeout=time.time()+timeout) # timeout is a timestamp, strange
            print 'get from queue:', item
            self.write(item)
            que.task_done()
        except gen.TimeoutError:
            print 'timeout'
            self.write('')
        finally:
            self.finish()

    @gen.coroutine
    def post(self, udid):
        ''' add new task '''
        que = self.ques[udid]
        data = tornado.escape.json_decode(self.request.body)
        data = {'id': str(uuid.uuid1()), 'data': data}
        yield que.put(data)
        print 'post, queue size:', que.qsize()
        self.write({'id': data['id']})
        self.finish()

    @gen.coroutine
    def put(self, udid):
        ''' finish task '''
        data = tornado.escape.json_decode(self.request.body)
        id = data['id']
        result = data['result']
        if self.results.get(id) is None:
            self.results[id] = result
        else:
            that = self.results[id]
            that.write(json.dumps(result))
            that.finish()
            self.results.pop(id, None)
        self.write('Success')
        self.finish()

    @gen.coroutine
    def delete(self, udid):
        data = tornado.escape.json_decode(self.request.body)
        id = data['id']
        timeout = float(data.get('timeout', 10.0))
        print 'Timeout:', timeout
        result = self.results.get(id)
        if result is None:
            self.results[id] = self
            yield gen.sleep(timeout)
            if self.results.get(id) == self:
                del(self.results[id])
                self.write('null')
                self.finish()
        else:
            self.write(json.dumps(result))
            self.results.pop(id, None)


def make_app(**settings):
    print settings
    return tornado.web.Application([
        (r"/", IndexHandler),
        (r"/rooms/([^/]*)", TaskQueueHandler),
    ], **settings)


def cmd_web(port, debug):
    app = make_app(debug=debug)
    app.listen(port)
    IOLoop.current().start()
    

def cmd_put(room, port, task_id, data):
    data = json.loads(data)
    jsondata = {'id': task_id, 'result': data}
    r = requests.put('http://localhost:%d/rooms/%s' % (port, room), data=json.dumps(jsondata))
    print r.text

def cmd_get(room, port, timeout):
    r = requests.get('http://localhost:%d/rooms/%s' % (port, room), params={'timeout': timeout})
    print r.text

def cmd_post(room, port, data):
    jsondata = json.loads(data)
    if not isinstance(jsondata, dict):
        sys.exit('data must be dict, for example: {"name": "kitty"}')
    r = requests.post('http://localhost:%d/rooms/%s' % (port, room), data=json.dumps(jsondata))
    print r.json()['id']

def cmd_delete(room, port, task_id):
    jsondata = {'id': task_id}
    r = requests.delete('http://localhost:%d/rooms/%s' % (port, room), data=json.dumps(jsondata))
    print r.text

def cmd_quit(room, port):
    r = requests.delete('http://localhost:%d/' % (port))
    print r.text

def _inject(func, kwargs):
    args = []
    for name in inspect.getargspec(func).args:
        args.append(kwargs.get(name))
    return func(*args)

def wrap(fn):
    def inner(parser_args):
        return _inject(fn, vars(parser_args))
    return inner


def main():
    ap = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    ap.add_argument("--room", required=False, help="udid or something")
    ap.add_argument("--port", required=False, default=10020, type=int, help="sever listen port")
    subp = ap.add_subparsers()

    @contextmanager
    def add_parser(name):
        yield subp.add_parser(name, formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    with add_parser('web') as p:
        # p.add_argument('--daemon', action='store_true', dest='is_daemon', help='Run is background')
        p.add_argument('--debug', action='store_true', help='Run in debug mode')
        p.set_defaults(func=wrap(cmd_web))

    with add_parser('put') as p:
        p.add_argument('task_id')
        p.add_argument('data')
        p.set_defaults(func=wrap(cmd_put))

    with add_parser('get') as p:
        p.add_argument('--timeout', type=float, default=10.0)
        p.set_defaults(func=wrap(cmd_get))

    with add_parser('post') as p:
        p.add_argument('data')
        p.set_defaults(func=wrap(cmd_post))

    with add_parser('delete') as p:
        p.add_argument('task_id')
        p.set_defaults(func=wrap(cmd_delete))

    with add_parser('quit') as p:
        p.set_defaults(func=wrap(cmd_quit))

    args = ap.parse_args()
    args.func(args)


if __name__ == '__main__':
    main()
