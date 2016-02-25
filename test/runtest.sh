#!/bin/bash
#
set -eu
cd $(dirname $0)

PYTHONPATH=$(cd ../; pwd):/usr/lib/pyshared/python2.7:$PYTHONPATH
export PYTHONPATH

echo "DEBUG: PYTHONPATH=$PYTHONPATH"
python -c 'import airtest; print airtest.__version__'
py.test -v -l "$@"
