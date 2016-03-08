#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import flask

import airtest
import airtest.image as aim
import cv2
import time

from . import utils

app = None #airtest.connect(monitor=False)

bp = flask.Blueprint('api', __name__)

@bp.route('/')
def home():
    return 'API documentation'

@bp.route('/snapshot')
def snapshot():
    filename = '%d-screen.png' % int(time.time())
    if os.path.exists(filename):
        os.unlink(filename)
    app.takeSnapshot(os.path.join(utils.TMPDIR, filename))
    return flask.jsonify(dict(filename=filename))

@bp.route('/crop')
def crop():
    rget = flask.request.args.get

    filename = rget('filename')
    screen = rget('screen')
    x, y = int(rget('x')), int(rget('y'))
    width, height = int(rget('width')), int(rget('height'))

    screen_file = screen.lstrip('/').replace('/', os.sep)
    screen_path = os.path.join(utils.selfdir(), screen_file)
    output_path = os.path.join(utils.workdir(), filename)
    assert os.path.exists(screen_path)

    im = cv2.imread(screen_path)
    cv2.imwrite(output_path, im[y:y+height, x:x+width])
    return flask.jsonify(dict(success=True, 
        message="文件已保存: "+output_path.encode('utf-8')))

@bp.route('/cropcheck')
def crop_check():
    rget = flask.request.args.get
    
    screen = rget('screen')
    x, y = int(rget('x')), int(rget('y'))
    width, height = int(rget('width')), int(rget('height'))

    screen_file = screen.lstrip('/').replace('/', os.sep)
    screen_path = os.path.join(utils.selfdir(), screen_file)

    im = cv2.imread(screen_path)
    im = im[y:y+height, x:x+width]  # crop image
    siftcnt = aim.sift_point_count(im)
    return flask.jsonify(dict(siftcnt=siftcnt))

@bp.route('/run')
def run_code():
    global app
    code = flask.request.args.get('code')
    try:
        exec code        
    except Exception, e:
        return flask.jsonify(dict(success=False, message=str(e)))
    return flask.jsonify(dict(success=True, message=""))

@bp.route('/connect')
def connect():
    global app
    device = flask.request.args.get('device')
    devno = flask.request.args.get('devno')
    try:
        app = airtest.connect(devno, device=device, monitor=False)
    except Exception, e:
        return flask.jsonify(dict(success=False, message=str(e)))
        
    return flask.jsonify(dict(success=True, message="连接成功"))