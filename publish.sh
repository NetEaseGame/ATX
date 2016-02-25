#!/bin/bash -
#
# 
set -eu
cd $(dirname $0)
rm -fr dist
python setup.py sdist

# Sync to qiniu
#mv dist/*.tar.gz qiniu/files/airtest.tar.gz
#qiniu/sync.sh

# Sync to pypi
python setup.py upload -r ${1:-pypi}
