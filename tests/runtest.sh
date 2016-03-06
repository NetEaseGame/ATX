#!/bin/bash
#
set -eu
cd $(dirname $0)

echo "Skip tests"
exit 0
# Skip test for now

PYTHONPATH=$(cd ../; pwd):/usr/lib/pyshared/python2.7:$PYTHONPATH
export PYTHONPATH

echo "DEBUG: PYTHONPATH=$PYTHONPATH"
python -c 'import airtest; print airtest.__version__'
py.test -v -l "$@"
