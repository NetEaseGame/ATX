#! /bin/sh
#
# build.sh
# Copyright (C) 2016 hzsunshx <hzsunshx@onlinegame-14-51>
#
# Distributed under terms of the MIT license.
#


pandoc --from=markdown --to=rst --output=README.rst README.md
