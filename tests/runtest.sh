#!/bin/bash
#

# Skip all tests in travis
if test -n "${TRAVIS}"
then
	exit 0
fi


cd $(dirname $0)
python -mpytest -v test_dummy.py test_base.py "$@"
