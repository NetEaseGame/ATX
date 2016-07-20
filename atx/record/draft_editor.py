#-*- encoding: utf-8 -*-

import os
import os.path
import json
import socket
import webbrowser
import tornado.ioloop
import tornado.web
import signal

from tornado.web import StaticFileHandler

__dir__ = os.path.dirname(os.path.abspath(__file__))

class MainHandler(tornado.web.RequestHandler):
    def get(self):
        self.redirect('/index.html')

class CaseHandler(tornado.web.RequestHandler):
    def initialize(self, casedir):
        self.casedir = casedir
        self.case = {}
        casepath = os.path.join(casedir, 'case.json')
        draftpath = os.path.join(casedir, 'draft.json')
        if os.path.exists(casepath):
            with open(casepath) as f:
                self.case = json.load(f)
        elif os.path.exists(draftpath):
            with open(draftpath) as f:
                self.case = json.load(f)

    def get(self):
        self.write(self.case)
        self.finish()

    def post(self):
        pass

def get_valid_port():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(('', 0))
    port = s.getsockname()[1]
    s.close()
    return port

def run(basedir):
    basedir = os.path.abspath(basedir)
    application = tornado.web.Application([
        (r'/', MainHandler),
        (r'/frames/(.*)', tornado.web.StaticFileHandler, {'path':os.path.join(basedir, 'frames')}),
        (r'/case', CaseHandler, {'casedir':os.path.join(basedir, 'case')}),
        (r'/(.*)', tornado.web.StaticFileHandler, {'path':'static'}),
    ], autoreload=True, static_hash_cache=False)

    # port = get_valid_port()
    # webbrowser.open('http://127.0.0.1:%s' % port, new=2)
    port = 8000

    application.listen(port)
    print 'Listen on', port
    print 'CaseDir:', basedir
    tornado.ioloop.IOLoop.instance().start()

if __name__ == '__main__':
    run('testcase')
