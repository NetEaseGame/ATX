#!/bin/bash -
#

CURDIR="$(cd $(dirname $0); pwd)"
echo "$@" > $CURDIR/test.pipe
