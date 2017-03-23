#!/bin/bash
#

# Skip all tests in travis
test -n "${TRAVIS}" && exit 0


cd $(dirname $0)

python -mpytest -v \
	test_ext_report.py \
	test_dummy.py \
	test_base.py "$@"
