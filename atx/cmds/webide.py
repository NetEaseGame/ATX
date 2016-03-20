# coding: utf-8

import os
import logging
import webbrowser
import socket

import tornado.ioloop
import tornado.web
from atx import logutils

__dir__ = os.path.dirname(os.path.abspath(__file__))

log = logutils.getLogger("webide")
log.setLevel(logging.DEBUG)


def get_valid_port():
    for port in range(10010, 10100):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        result = sock.connect_ex(('127.0.0.1', port))
        if result != 0:
            return port

    raise SystemError("Can not find a unused port, amazing!")

class MainHandler(tornado.web.RequestHandler):
    def get(self):
        self.render('index.html')


def make_app(settings={}):
    application = tornado.web.Application([
        (r"/", MainHandler),
    ], **settings)
    return application


def main(**kws):
    application = make_app({
        'static_path': os.path.join(__dir__, 'static'),
        'template_path': os.path.join(__dir__, 'static'),
    })
    port = kws.get('port', None)
    if not port:
        port = get_valid_port()

    open_browser = kws.get('open_browser', True)
    if open_browser:
        url = 'http://127.0.0.1:{}'.format(port)
        webbrowser.open(url, new=2) # 2: open new tab if possible

    application.listen(port)
    log.info("Listening port on 127.0.0.1:{}".format(port))
    tornado.ioloop.IOLoop.instance().start()

if __name__ == "__main__":
    main()
