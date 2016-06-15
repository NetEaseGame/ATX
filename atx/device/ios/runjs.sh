#!/bin/bash -
#

set -eu

sh write_pipe.sh "$@"
head -n1 test.pipe
