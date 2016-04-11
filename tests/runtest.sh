#!/bin/bash
#

# Skip all tests in travis
if test -n "${TRAVIS}"
then
	exit 0
fi


cd $(dirname $0)
py.test -v test_dummy.py "$@"
