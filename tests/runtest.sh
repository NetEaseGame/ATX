#!/bin/bash
#

set -eu
cd $(dirname $0)

py.test -v test_dummy.py
