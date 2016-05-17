# coding: utf-8

import subprocess32 as subprocess
import tornado
import tornado.web
import tornado.ioloop
import tornado.websocket

from tornado.concurrent import run_on_executor
from concurrent.futures import ThreadPoolExecutor   # `pip install futures` for python2


class MainHandler(tornado.web.RequestHandler):
    def get(self):
        self.render('index.html')


class TestHandler(tornado.web.RequestHandler):
    executor = ThreadPoolExecutor(max_workers=1)
    output = ''
    running = False

    @run_on_executor
    def background_test(self):
        self.running = True
        proc = subprocess.Popen('echo hello', shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        while True:
            line = proc.stdout.readline()
            if line == '':
                break
            print line
            for client in ProgressHandler.clients:
                client.write_message(line)
            self.output = self.output + line
        self.running = False

    def get(self):
        self.render('runtest.html')

    def post(self):
        if not self.running:
            self.background_test()
        self.render('runtest.html', running=self.running)


class ProgressHandler(tornado.websocket.WebSocketHandler):
    clients = set()

    def open(self):
        print 'websocket connected'
        self.write_message(TestHandler.output)
        self.clients.add(self)

    def on_close(self):
        self.clients.remove(self)
        print "WebSocket closed"
    
    def check_origin(self, origin):
        return True


def make_app(**settings):
    settings['template_path'] = 'templates'
    settings['static_path'] = 'static'
    return tornado.web.Application([
        (r"/", MainHandler),
        (r"/runtest", TestHandler),
        (r"/ws/progress", ProgressHandler),
    ], **settings)


def main():
    app = make_app(debug=True)
    app.listen(4000)
    print 'listening on port 4000'
    tornado.ioloop.IOLoop.current().start()


if __name__ == '__main__':
    main()