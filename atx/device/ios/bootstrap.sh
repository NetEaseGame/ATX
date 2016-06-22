#!/bin/bash -
#
set -e
cd $(dirname $0)

BUNDLE_ID=${BUNDLE_ID:?}
UDID=${UDID:-$(idevice_id -l)}
TEST="./instruments-test.js"
PIPE=${PIPE:-"/tmp/atx.instruments.$UDID.pipe"}

TRACETEMPLATE="/Applications/Xcode.app/Contents/Applications/Instruments.app/Contents/PlugIns/AutomationInstrument.xrplugin/Contents/Resources/Automation.tracetemplate"

QUEUE="python -m atx.taskqueue --room $UDID"
#echo "UDID: $UDID"
# test -p "$PIPE" || mkfifo "$PIPE"

case "$1" in
	instruments)
		# python -m atx.taskqueue web &>/tmp/atx.taskqueue.log &
		exec instruments -w ${UDID:?} -t "$TRACETEMPLATE" $BUNDLE_ID -e UIASCRIPT $TEST
		;;
	run)
		shift
		TASK_ID=$($QUEUE post "$1")
		exec $QUEUE delete "$TASK_ID"
		# /bin/echo "$@" >> $PIPE
		# exec /usr/bin/head -n1 $PIPE
		;;
	get)
		shift
		$QUEUE get
		# /usr/bin/head -n1 $PIPE
		;;
	put)
		shift
		# $1: task_id, $2: data
		$QUEUE put "$1" "$2"
		# /bin/echo "$@" >> $PIPE
		;;
	reset)
		# todo, maybe quit too much
		$QUEUE quit
		;;
	*)
		/bin/echo "Usage: $0 <instruments|run|get|put|reset> [ARGS]"
		;;
esac

