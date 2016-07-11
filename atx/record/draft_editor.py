#-*- encoding: utf-8 -*-

import os
import os.path
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
    def get(self):
        pass

    def post(self):
        pass

def get_valid_port():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(('', 0))
    port = s.getsockname()[1]
    s.close()
    return port

def load_case(casedir):
    pass

def run(casedir):
    casedir = os.path.abspath(casedir)
    application = tornado.web.Application([
        (r'/', MainHandler),
        (r'/frames/(.*)', tornado.web.StaticFileHandler, {'path':os.path.join(casedir, 'frames')}),
        (r'/(.*)', tornado.web.StaticFileHandler, {'path':'static'}),
    ], autoreload=True, static_hash_cache=False)

    # port = get_valid_port()
    # webbrowser.open('http://127.0.0.1:%s' % port, new=2)
    port = 8000

    application.listen(port)
    print 'Listen on', port
    print 'CaseDir:', casedir
    tornado.ioloop.IOLoop.instance().start()

if __name__ == '__main__':
    run('testcase')
