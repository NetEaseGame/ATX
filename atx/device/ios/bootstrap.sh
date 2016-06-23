#!/bin/bash -
#
set -e
WORKDIR=$PWD
cd $(dirname $0)

BUNDLE_ID=${BUNDLE_ID:?}
UDID=${UDID:-$(idevice_id -l)}
TEST="./instruments-test.js"

TRACETEMPLATE="/Applications/Xcode.app/Contents/Applications/Instruments.app/Contents/PlugIns/AutomationInstrument.xrplugin/Contents/Resources/Automation.tracetemplate"

QUEUE="python -m atx.taskqueue --room $UDID"
#echo "UDID: $UDID"

test -d $RESULTPATH || mkdir $RESULTPATH
case "$1" in
	instruments)
		# python -m atx.taskqueue web &>/tmp/atx.taskqueue.log &
		exec instruments -w ${UDID:?} -t "Automation" -D $WORKDIR/cli.trace $BUNDLE_ID -e UIASCRIPT $TEST # -e UIARESULTSPATH $RESULTPATH
		#exec instruments -w ${UDID:?} -t "$TRACETEMPLATE" $BUNDLE_ID -e UIASCRIPT $TEST # -e UIARESULTSPATH $RESULTPATH
		;;
	run)
		shift
		TASK_ID=$($QUEUE post "$1")
		exec $QUEUE delete "$TASK_ID"
		;;
	get)
		shift
		$QUEUE get
		;;
	put)
		shift
		# $1: task_id, $2: data
		$QUEUE put "$1" "$2"
		;;
	reset)
		# todo, maybe quit too much
		$QUEUE quit
		;;
	*)
		/bin/echo "Usage: $0 <instruments|run|get|put|reset> [ARGS]"
		;;
esac

