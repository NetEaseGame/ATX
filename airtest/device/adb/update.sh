#! /bin/sh
#
# update.sh
# Copyright (C) 2015 hzsunshx <hzsunshx@onlinegame-13-180>
#
# Distributed under terms of the MIT license.
#

ADDR="https://raw.githubusercontent.com/dtmilano/AndroidViewClient/master/src/com/dtmilano/android/adb"
for file in androidkeymap.py adbclient.py
do
	wget $ADDR/$file -O $file
done
