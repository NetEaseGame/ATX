#-*- encoding: utf-8 -*-

import os
import os.path
import json
import socket
import webbrowser
import tornado.ioloop
import tornado.web
import tornado.websocket
import traceback
import time

from tornado.web import StaticFileHandler

import atx
from atx.record.android import AndroidRecorder

__dir__ = os.path.dirname(os.path.abspath(__file__))

cm = None

class CaseManager(object):
    def __init__(self, basedir):
        self.basedir = basedir

        # record object
        record = AndroidRecorder(None, basedir)
        obj = {}
        with open(os.path.join(basedir, 'frames', 'frames.json')) as f:
            obj = json.load(f)
        record.device_info = obj['device']
        record.frames = obj['frames']
        self.record = record

        # case
        self.casepath = os.path.join(basedir, 'case', 'case.json')
        self.case = []
        with open(self.casepath) as f:
            self.case = json.load(f)

        self._env = None

    def save_case(self, data):
        self.case = json.loads(data)
        with open(self.casepath, 'w') as f:
            json.dump(self.case, f, indent=2)

        # generate code
        try:
            AndroidRecorder.process_casefile(self.basedir)
            return True
        except:
            traceback.print_exc()
            return False

    def build_exec_env(self):
        d = atx.connect()
        d.image_path.append(os.path.join(self.basedir, 'case'))
        self._env = {'time': time, 'd': d}

    def run_step(self, frameidx):
        if self._env is None:
            self.build_exec_env()
        for row in self.case:
            if row['frameidx'] == frameidx:
                code = self.record.process_draft(row)
                print 'running', row, code
                try:
                    cobj = compile(code, '<string>', 'exec')
                    ret = eval(cobj, None, self._env)
                except Exception as e:
                    return str(e)
                else:
                    return 'ok, return value: %s' % str(ret)
        return 'Not Found.'

class MainHandler(tornado.web.RequestHandler):
    def get(self):
        self.redirect('/index.html')

class CaseHandler(tornado.web.RequestHandler):

    def get(self, *args):
        self.write(json.dumps(cm.case))
        self.finish()

    def post(self, *args):
        data = self.request.arguments['data'][0] ## get the string
        ok = cm.save_case(data)
        self.write(json.dumps({'success':ok}))

class CaseRunnerHandler(tornado.websocket.WebSocketHandler):

    def check_origin(self, origin):
        return True

    def open(self, *args, **kwargs):
        print 'Websocket connnected.'

    def on_close(self):
        print 'Websocket closed.'

    def on_message(self, message):
        print 'received:', message
        try:
            data = json.loads(message)
        except Exception as e:
            self.write_message({'err': str(e)})
            return

        action = data['action']
        frame = data.get('frame')
        if action in ('run_all', 'run_step'):
            msg = cm.run_step(frame)
            self.write_message({'action':action, 'frame':frame, 'msg': msg})
        else:
            self.write_message({'err': 'unknown action %s' % action})

def get_valid_port():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(('', 0))
    port = s.getsockname()[1]
    s.close()
    return port

def run(basedir, port=8000):
    global cm
    basedir = os.path.abspath(basedir)
    cm = CaseManager(basedir)
    application = tornado.web.Application([
        (r'/', MainHandler),
        (r'/frames/(.*)', StaticFileHandler, {'path':os.path.join(basedir, 'frames')}),
        (r'/case(.*)', CaseHandler),
        (r'/run', CaseRunnerHandler),
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
