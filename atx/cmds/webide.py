# coding: utf-8

import os
import sys
import logging
import webbrowser
import socket
import time
import json
import traceback
import shutil
import locale

import cv2
import tornado.ioloop
import tornado.web
import tornado.websocket
from tornado.concurrent import run_on_executor
from concurrent.futures import ThreadPoolExecutor   # `pip install futures` for python2

import atx
from atx import logutils
from atx import imutils
from atx import base


__dir__ = os.path.dirname(os.path.abspath(__file__))
log = logutils.getLogger("webide", level=logging.DEBUG)
log.setLevel(logging.DEBUG)


IMAGE_PATH = ['.', 'imgs', 'images']
device = None
atx_settings = {}
latest_screen = ''


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
        screenshots = []
        for name in imgs:
            realpath = name.replace('\\', '/') # fix for windows
            name = os.path.basename(name).split('@')[0]
            if realpath.startswith('screenshots/'):
                screenshots.append([name, realpath])
            else:
                images.append([name, realpath])
        self.write({
            'images': images,
            'screenshots': screenshots,
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


class DebugWebSocket(tornado.websocket.WebSocketHandler):
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
            images = []
            screenshots = []
            for name in imgs:
                realpath = name.replace('\\', '/') # fix for windows
                name = os.path.basename(name).split('@')[0]
                if realpath.startswith('screenshots/'):
                    screenshots.append({'name':name, 'path':realpath})
                else:
                    images.append({'name':name, 'path':realpath})
            self.write_message({'type': 'image_list', 'images': images, 'screenshots':screenshots, 'latest': latest_screen})
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
        ret['xml_text'] = read_file('blockly.xml', default='<xml xmlns="http://www.w3.org/1999/xhtml"></xml>')
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
        v = self.get_argument('v')
        global latest_screen
        latest_screen = 'screenshots/screen_%s.png' % v
        d.screenshot(latest_screen)

        self.set_header('Content-Type', 'image/png')
        with open(latest_screen, 'rb') as f:
            while 1:
                data = f.read(16000)
                if not data:
                    break
                self.write(data)
        self.finish()

    def post(self):
        screenname = self.get_argument('screenname')
        filename = self.get_argument('filename').encode(locale.getpreferredencoding(), 'ignore')
        bound = self.get_arguments('bound[]')
        l, t, r, b = map(int, bound)
        image = imutils.open(screenname)
        image = imutils.crop(image, l, t, r, b)
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
        (r'/ws', DebugWebSocket), # code debug
        (r"/workspace", WorkspaceHandler), # save and write workspace
        (r"/images/screenshot", ScreenshotHandler),
        (r'/api/images', ImageHandler),
        (r'/static_imgs/(.*)', StaticFileHandler, {'path': static_path}),
    ], **settings)
    return application


def main(web_port=None, host=None, port=None, open_browser=True, workdir='.'):
    os.chdir(workdir)

    global IMAGE_PATH
    if not os.path.exists('screenshots'):
        os.makedirs('screenshots')
    IMAGE_PATH.append('screenshots')

    application = make_app({
        'static_path': os.path.join(__dir__, 'static'),
        'template_path': os.path.join(__dir__, 'static'),
        'debug': True,
    })
    if not web_port:
        web_port = get_valid_port()

    global atx_settings
    atx_settings['host'] = host
    atx_settings['port'] = port

    if open_browser:
        url = 'http://127.0.0.1:{}'.format(web_port)
        webbrowser.open(url, new=2) # 2: open new tab if possible

    application.listen(web_port)
    log.info("Server started.")
    log.info("Listening port on 127.0.0.1:{}".format(web_port))
    tornado.ioloop.IOLoop.instance().start()


if __name__ == "__main__":
    main()
