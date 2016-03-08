# coding: utf8

import flask
# from flask import request, flash, redirect, url_for, render_template

from . import utils

bp = flask.Blueprint('home', __name__)

@bp.route('/tmp/<path:path>')
def static_proxy(path):
    return flask.send_from_directory(utils.TMPDIR, path)

#@models.db_session
@bp.route('/')
def home():
    return flask.render_template('index.html')
