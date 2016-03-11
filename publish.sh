#!/bin/bash -
#
# 
set -eu
cd $(dirname $0)

# Sync to pypi
python setup.py sdist bdist_wheel upload -r ${1:-pypi}
