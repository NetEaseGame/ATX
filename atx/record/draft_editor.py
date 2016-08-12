#-*- encoding: utf-8 -*-

import os
import os.path
import json
import socket
import webbrowser
import tornado.ioloop
import tornado.web
import traceback

from tornado.web import StaticFileHandler

__dir__ = os.path.dirname(os.path.abspath(__file__))

class MainHandler(tornado.web.RequestHandler):
    def get(self):
        self.redirect('/index.html')

class CaseHandler(tornado.web.RequestHandler):
    def initialize(self, basedir):
        self.basedir = basedir
        self.casepath = os.path.join(basedir, 'case', 'case.json')
        self.case = []
        if os.path.exists(self.casepath):
            with open(self.casepath) as f:
                self.case = json.load(f)

    def get(self, *args):
        self.write(json.dumps(self.case))
        self.finish()

    def post(self, *args):
        data = self.request.arguments['data'][0] ## get the string 
        with open(self.casepath, 'w') as f:
            json.dump(json.loads(data), f, indent=2)

        # generate code
        from atx.record.android import AndroidRecorder
        try:
            AndroidRecorder.process_casefile(self.basedir)
            self.write(json.dumps({'success': True}))
        except:
            traceback.print_exc()
            self.write(json.dumps({'success':False}))


class CaseRunnerHandler(tornado.web.RequestHandler):
    def initialize(self, casedir):
        pass

    def get(self, *args):
        pass

def get_valid_port():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(('', 0))
    port = s.getsockname()[1]
    s.close()
    return port

def run(basedir, port=8000):
    basedir = os.path.abspath(basedir)
    application = tornado.web.Application([
        (r'/', MainHandler),
        (r'/frames/(.*)', StaticFileHandler, {'path':os.path.join(basedir, 'frames')}),
        (r'/case(.*)', CaseHandler, {'basedir': basedir}),
        (r'/run(.*)', CaseRunnerHandler, {'casedir': os.path.join(basedir, 'case')}),
        (r'/(.*)', StaticFileHandler, {'path':os.path.join(__dir__, 'site')}),
    ], autoreload=True, static_hash_cache=False)

    if port is None:
        port = get_valid_port()
    webbrowser.open('http://127.0.0.1:%s' % port, new=2)

    application.listen(port)
    print 'Listen on', port
    print 'WorkDir:', basedir
    print 'Press Ctrl+C to stop...'
    try:
        tornado.ioloop.IOLoop.instance().start()
    except:
        print 'Done'

if __name__ == '__main__':
    run('testcase')
