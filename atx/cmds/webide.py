# coding: utf-8

import os
import sys
import logging
import webbrowser
import socket
import time
import json
import traceback

import cv2
import tornado.ioloop
import tornado.web
import tornado.websocket
from tornado.concurrent import run_on_executor
from concurrent.futures import ThreadPoolExecutor   # `pip install futures` for python2

import atx
from atx import logutils
from atx import base
from atx import imutils


__dir__ = os.path.dirname(os.path.abspath(__file__))
log = logutils.getLogger("webide", level=logging.DEBUG)
log.setLevel(logging.DEBUG)


IMAGE_PATH = ['.', 'imgs', 'images']
workdir = '.'
device = None
atx_settings = {}


def read_file(filename, default=''):
    if not os.path.isfile(filename):
        return default
    with open(filename, 'rb') as f:
        return f.read()

def write_file(filename, content):
    with open(filename, 'w') as f:
        f.write(content.encode('utf-8'))

def get_valid_port():
    for port in range(10010, 10100):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        result = sock.connect_ex(('127.0.0.1', port))
        sock.close()
        if result != 0:
            return port

    raise SystemError("Can not find a unused port, amazing!")


class FakeStdout(object):
    def __init__(self, fn=sys.stdout.write):
        self._fn = fn

    def write(self, s):
        self._fn(s)

    def flush(self):
        pass


class ImageHandler(tornado.web.RequestHandler):
    def get(self):
        imgs = base.list_images(path=IMAGE_PATH)
        images = []
        for name in imgs:
            realpath = name.replace('\\', '/') # fix for windows
            name = os.path.basename(name).split('@')[0]
            images.append([name, realpath])
        self.write({
            'images': images, 
            'baseURL': self.request.protocol + '://' + self.request.host+'/static_imgs/'
        })


class MainHandler(tornado.web.RequestHandler):
    def get(self):
        imgs = base.list_images(path=IMAGE_PATH)
        imgs = [(os.path.basename(name), name) for name in imgs]
        self.render('index.html', images=imgs)

    def post(self):
        print self.get_argument('xml_text')
        self.write("Good")


class EchoWebSocket(tornado.websocket.WebSocketHandler):
    executor = ThreadPoolExecutor(max_workers=1)

    def open(self):
        log.info("WebSocket connected")
        self._run = False

    def _highlight_block(self, id):
        self.write_message({'type': 'highlight', 'id': id})
        if not self._run:
            raise RuntimeError("stopped")
        else:
            time.sleep(.1)

    def write_console(self, s):
        self.write_message({'type': 'console', 'output': s})

    def run_blockly(self, code):
        filename = '__tmp.py'
        fake_sysout = FakeStdout(self.write_console)

        __sysout = sys.stdout
        sys.stdout = fake_sysout # TODOs
        self.write_message({'type': 'console', 'output': '# '+time.strftime('%H:%M:%S') + ' start running\n'})
        try:
            # python code always UTF-8
            code = code.encode('utf-8')
            # hot patch
            code = code.replace('atx.click_image', 'd.click_image')

            exec code in {
                'highlight_block': self._highlight_block,
                '__name__': '__main__',
                '__file__': filename}
        except RuntimeError as e:
            if str(e) != 'stopped':
                raise
            print 'Program stopped'
        except Exception as e:
            self.write_message({'type': 'traceback', 'output': traceback.format_exc()})
        finally:
            self._run = False
            self.write_message({'type': 'run', 'status': 'ready'})
            sys.stdout = __sysout
        
    @run_on_executor
    def background_task(self, code):
        self.write_message({'type': 'run', 'status': 'running'})
        self.run_blockly(code)
        return True

    @tornado.gen.coroutine
    def on_message(self, message_text):
        message = None
        try:
            message = json.loads(message_text)
        except:
            print 'Invalid message from browser:', message_text
            return
        command = message.get('command')

        if command == 'refresh':
            imgs = base.list_images(path=IMAGE_PATH)
            imgs = [dict(
                path=name.replace('\\', '/'), name=os.path.basename(name)) for name in imgs]
            self.write_message({'type': 'image_list', 'data': list(imgs)})
        elif command == 'stop':
            self._run = False
            self.write_message({'type': 'run', 'notify': '停止中'})
        elif command == 'run':
            if self._run:
                self.write_message({'type': 'run', 'notify': '运行中'})
                return
            self._run = True
            res = yield self.background_task(message.get('code'))
            self.write_message({'type': 'run', 'status': 'ready', 'notify': '运行结束', 'result': res})
        else:
            self.write_message(u"You said: " + message)

    def on_close(self):
        log.info("WebSocket closed")
    
    def check_origin(self, origin):
        return True


class WorkspaceHandler(tornado.web.RequestHandler):
    def get(self):
        ret = {}
        ret['xml_text'] = read_file('blockly.xml', '<xml xmlns="http://www.w3.org/1999/xhtml"></xml>')
        ret['python_text'] = read_file('blockly.py')
        self.write(ret)

    def post(self):
        log.info("Save workspace")
        xml_text = self.get_argument('xml_text')
        python_text = self.get_argument('python_text')
        write_file('blockly.xml', xml_text)
        write_file('blockly.py', python_text)


class ScreenshotHandler(tornado.web.RequestHandler):
    def get(self):
        d = atx.connect(**atx_settings)
        d.screenshot('_screen.png')

        self.set_header('Content-Type', 'image/png')
        with open('_screen.png', 'rb') as f:
            while 1:
                data = f.read(16000)
                if not data:
                    break
                self.write(data)
        self.finish()

    def post(self):
        raw_image = self.get_argument('raw_image')
        filename = self.get_argument('filename')
        image = imutils.open(raw_image)
        cv2.imwrite(filename, image)
        self.write({'status': 'ok'})


class StaticFileHandler(tornado.web.StaticFileHandler):
    def get(self, path=None, include_body=True):
        path = path.encode(base.SYSTEM_ENCODING) # fix for windows
        return super(StaticFileHandler, self).get(path, include_body)


def make_app(settings={}):
    static_path = os.getcwd()
    application = tornado.web.Application([
        (r"/", MainHandler),
        (r"/workspace", WorkspaceHandler),
        (r"/images/screenshot", ScreenshotHandler),
        (r'/static_imgs/(.*)', StaticFileHandler, {'path': static_path}),
        (r'/api/images', ImageHandler),
        (r'/ws', EchoWebSocket),
    ], **settings)
    return application


def main(**kws):
    application = make_app({
        'static_path': os.path.join(__dir__, 'static'),
        'template_path': os.path.join(__dir__, 'static'),
        'debug': True,
    })
    port = kws.get('port', None)
    if not port:
        port = get_valid_port()

    global device
    global workdir
    workdir = kws.get('workdir', '.')
    atx_settings['host'] = kws.get('adb_host')
    atx_settings['port'] = kws.get('adb_port')
    # device = atx.connect(host=kws.get('host'), port=kws.get('port'))
    # TODO
    # filename = 'blockly.py'
    IMAGE_PATH.append('images/blockly')

    open_browser = kws.get('open_browser', True)
    if open_browser:
        url = 'http://127.0.0.1:{}'.format(port)
        webbrowser.open(url, new=2) # 2: open new tab if possible

    application.listen(port)
    log.info("Server started.")
    log.info("Listening port on 127.0.0.1:{}".format(port))
    tornado.ioloop.IOLoop.instance().start()


if __name__ == "__main__":
    main()
