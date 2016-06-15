#!/bin/bash -
#

NAME=${NAME:?}
UDID=$(idevice_id -l)
TEST="./instruments-test.js"

TRACETEMPLATE="/Applications/Xcode.app/Contents/Applications/Instruments.app/Contents/PlugIns/AutomationInstrument.xrplugin/Contents/Resources/Automation.tracetemplate"

instruments -w $UDID -t "$TRACETEMPLATE" $NAME -e UIASCRIPT $TEST