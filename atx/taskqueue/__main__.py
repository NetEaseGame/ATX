#! /usr/bin/env python
# -*- coding: utf-8 -*-

import argparse
import uuid
import inspect
from contextlib import contextmanager

import tornado.web
import tornado.escape
from tornado import gen
from tornado.ioloop import IOLoop
from tornado.queues import Queue


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
    que = Queue(maxsize=2)
    results = {}

    @gen.coroutine
    def get(self, udid):
        ''' get new task '''
        item = yield self.que.get()
        print udid, item
        self.que.task_done()
        self.write(item)
        self.finish()

    @gen.coroutine
    def post(self, udid):
        ''' add new task '''
        # print self.request.body
        data = tornado.escape.json_decode(self.request.body)
        data['id'] = str(uuid.uuid1())
        print data
        yield self.que.put(data)
        self.write({'id': data['id']})
        self.finish()

    def put(self, udid):
        ''' finish task '''
        data = tornado.escape.json_decode(self.request.body)
        print data['id']
        print data['result']


def make_app(**settings):
    print settings
    return tornado.web.Application([
        (r"/rooms/([^/]*)", MainHandler),
    ], **settings)


def cmd_web():
    app = make_app(debug=True)
    app.listen(10020)
    IOLoop.current().start() #run_sync(main)

def cmd_put(room, data):
    # FIXME(ssx): maybe need to use requests
    print room, data

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
    subp = ap.add_subparsers()

    @contextmanager
    def add_parser(name):
        yield subp.add_parser(name, formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    with add_parser('web') as p:
        p.set_defaults(func=wrap(cmd_web))

    with add_parser('put') as p:
        p.add_argument('data')
        p.set_defaults(func=wrap(cmd_put))

    # TODO: get, done

    args = ap.parse_args()
    args.func(args)


if __name__ == '__main__':
    main()

    