#!/bin/bash -
#
set -e
cd $(dirname $0)

BUNDLE_ID=${BUNDLE_ID:?}
UDID=${UDID:-$(idevice_id -l)}
TEST="./instruments-test.js"
PIPE=${PIPE:-"/tmp/atx.instruments.$UDID.pipe"}

TRACETEMPLATE="/Applications/Xcode.app/Contents/Applications/Instruments.app/Contents/PlugIns/AutomationInstrument.xrplugin/Contents/Resources/Automation.tracetemplate"

#echo "UDID: $UDID"
test -p "$PIPE" || mkfifo "$PIPE"

case "$1" in
	instruments)
		exec instruments -w ${UDID:?} -t "$TRACETEMPLATE" $BUNDLE_ID -e UIASCRIPT $TEST
		;;
	run)
		shift
		/bin/echo "$@" >> $PIPE
		exec /usr/bin/head -n1 $PIPE
		;;
	get)
		shift
		/usr/bin/head -n1 $PIPE
		;;
	put)
		shift
		/bin/echo "$@" >> $PIPE
		;;
	reset)
		/bin/rm -f $PIPE
		;;
	*)
		/bin/echo "Usage: $0 <instruments|run|get|put|reset> [ARGS]"
		;;
esac

