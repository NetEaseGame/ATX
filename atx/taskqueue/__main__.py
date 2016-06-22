#! /usr/bin/env python
# -*- coding: utf-8 -*-

import argparse
import uuid
import json
import inspect
import sys
from contextlib import contextmanager
from collections import defaultdict
from functools import partial

import tornado.web
import tornado.escape
from tornado import gen
from tornado.ioloop import IOLoop
from tornado.queues import Queue

import requests

# @gen.coroutine
# def consumer():
#     while True:
#         item = yield que.get()
#         try:
#             print('Doing work on %s' % item)
#             yield gen.sleep(0.5)
#         finally:
#             que.task_done()

# @gen.coroutine
# def producer():
#     for item in range(5):
#         yield que.put(item)
#         print('Put %s' % item)

# @gen.coroutine
# def main():
#     # Start consumer without waiting (since it never finishes).
#     IOLoop.current().spawn_callback(consumer)
#     yield producer()     # Wait for producer to put all tasks.
#     yield que.join()       # Wait for consumer to finish all tasks.
#     print('Done')


class MainHandler(tornado.web.RequestHandler):
    ques = defaultdict(partial(Queue, maxsize=2))
    results = {}

    @gen.coroutine
    def get(self, udid):
        ''' get new task '''
        que = self.ques[udid]
        item = yield que.get()
        que.task_done()
        self.write(item)
        self.finish()

    @gen.coroutine
    def post(self, udid):
        ''' add new task '''
        que = self.ques[udid]
        data = tornado.escape.json_decode(self.request.body)
        data['id'] = str(uuid.uuid1())
        yield que.put(data)
        print que.qsize()
        self.write({'id': data['id']})
        self.finish()

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
            del(self.results[id])
        self.write('Success')

    @gen.coroutine
    def delete(self, udid):
        # TODO: get and wait loop, until find the result
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
            del(self.results[id])


def make_app(**settings):
    print settings
    return tornado.web.Application([
        (r"/rooms/([^/]*)", MainHandler),
    ], **settings)


def cmd_web():
    app = make_app(debug=True)
    app.listen(10020)
    IOLoop.current().start()

def cmd_put(room, port, task_id, data):
    data = json.loads(data)
    jsondata = {'id': task_id, 'result': data}
    r = requests.put('http://localhost:%d/rooms/%s' % (port, room), data=json.dumps(jsondata))
    print r.text

def cmd_get(room, port):
    r = requests.get('http://localhost:%d/rooms/%s' % (port, room))
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
        p.set_defaults(func=wrap(cmd_web))

    with add_parser('put') as p:
        p.add_argument('task_id')
        p.add_argument('data')
        p.set_defaults(func=wrap(cmd_put))

    with add_parser('get') as p:
        p.set_defaults(func=wrap(cmd_get))

    with add_parser('post') as p:
        p.add_argument('data')
        p.set_defaults(func=wrap(cmd_post))

    with add_parser('delete') as p:
        p.add_argument('task_id')
        p.set_defaults(func=wrap(cmd_delete))

    args = ap.parse_args()
    args.func(args)


if __name__ == '__main__':
    main()
