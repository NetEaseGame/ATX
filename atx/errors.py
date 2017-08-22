#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import absolute_import
from __future__ import print_function


class Error(Exception):
    def __init__(self, message, data=None):
        self.message = message
        self.data = data

    def __str__(self):
        if self.data:
            return '{}, data: {}'.format(self.message, self.data)
        return self.message

    def __repr__(self):
        return repr(self.message)


class WindowsAppNotFoundError(Error):
    pass


class ImageNotFoundError(Error):
    pass

class WatchTimeoutError(Error):
    pass

class AssertError(Error):
    pass

class AssertExistsError(AssertError):
    pass
