# -*- coding: utf-8 -*-
"""
    atx.ext
    ~~~~~~~~~
    Redirect imports for extensions.  This module basically makes it possible
    for us to transition from atxext.foo to atx_foo without having to
    force all extensions to upgrade at the same time.
    When a user does ``from atx.ext.foo import bar`` it will attempt to
    import ``from atx_foo import bar`` first and when that fails it will
    try to import ``from atxext.foo import bar``.
    We're switching from namespace packages because it was just too painful for
    everybody involved.
    :license: MIT, see LICENSE for more details.
"""

from __future__ import absolute_import


def setup():
    from atx.ext.exthook import ExtensionImporter
    importer = ExtensionImporter(['atx_%s', 'atxext.%s', 'atx.buildin_ext.%s'], __name__)
    importer.install()


setup()
del setup