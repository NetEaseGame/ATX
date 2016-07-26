#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# hzsunshx <2016-06-12>
# make sure only one phone connected to pc/

import unittest
import shutil
from collections import namedtuple
from mock import MagicMock, patch

import atx
from atx.ext.report import Report
from PIL import Image


class TestExtReport(unittest.TestCase):
    def setUp(self):
        self.d = atx.connect(platform='dummy')
        self.rp = Report(self.d, save_dir='tmp_report')

    def tearDown(self):
        self.rp.close()
        shutil.rmtree('tmp_report')

    def test_screenshot(self):
        assert self.rp.last_screenshot is None
        self.d.screenshot()
        assert isinstance(self.rp.last_screenshot, Image.Image)
