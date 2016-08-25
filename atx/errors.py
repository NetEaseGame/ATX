#!/usr/bin/env python
# -*- coding: utf-8 -*-


class BaseError(Exception):
    def __init__(self, message, data=None):
        self.message = message
        self.data = data

    def __str__(self):
        if self.data:
            return '{}, data: {}'.format(self.message, self.data)
        return self.message

    def __repr__(self):
        return repr(self.message)


class WindowsAppNotFoundError(BaseError):
    pass


class ImageNotFoundError(BaseError):
    pass

class WatchTimeoutError(BaseError):
    pass

class AssertError(BaseError):
    pass

class AssertExistsError(AssertError):
    pass