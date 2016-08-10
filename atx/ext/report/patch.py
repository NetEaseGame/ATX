#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Reference
https://github.com/gevent/gevent/blob/master/src/gevent/monkey.py
"""

from __future__ import absolute_import
import sys

if sys.version_info[0] >= 3:
    string_types = str,
    PY3 = True
else:
    import __builtin__ # pylint:disable=import-error
    string_types = __builtin__.basestring,
    PY3 = False


# maps module name -> {attribute name: original item}
# e.g. "time" -> {"sleep": built-in function sleep}
saved = {}


def is_module_patched(modname):
    """Check if a module has been replaced with a cooperative version."""
    return modname in saved


def is_object_patched(modname, objname):
    """Check if an object in a module has been replaced with a cooperative version."""
    return is_module_patched(modname) and objname in saved[modname]


def _get_original(name, items):
    d = saved.get(name, {})
    values = []
    module = None
    for item in items:
        if item in d:
            values.append(d[item])
        else:
            if module is None:
                module = __import__(name)
            values.append(getattr(module, item))
    return values


def get_original(mod_name, item_name):
    """Retrieve the original object from a module.
    If the object has not been patched, then that object will still be retrieved.
    :param item_name: A string or sequence of strings naming the attribute(s) on the module
        ``mod_name`` to return.
    :return: The original value if a string was given for ``item_name`` or a sequence
        of original values if a sequence was passed.
    """
    if isinstance(item_name, string_types):
        return _get_original(mod_name, [item_name])[0]
    else:
        return _get_original(mod_name, item_name)

_NONE = object()


def patch_item(module, attr, newitem):
    olditem = getattr(module, attr, _NONE)
    if olditem is not _NONE:
        saved.setdefault(module, {}).setdefault(attr, olditem)
    setattr(module, attr, newitem)


def remove_item(module, attr):
    olditem = getattr(module, attr, _NONE)
    if olditem is _NONE:
        return
    saved.setdefault(module, {}).setdefault(attr, olditem)
    delattr(module, attr) 