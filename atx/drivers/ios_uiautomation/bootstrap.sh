#!/bin/bash -
#

set -e
WORKDIR=$PWD
cd $(dirname $0)

export PATH="/usr/local/bin":$PATH

BUNDLE_ID=${BUNDLE_ID:?}
UDID=${UDID:-$(idevice_id -l)}
TEST="./instruments-test.js"

TRACETEMPLATE="/Applications/Xcode.app/Contents/Applications/Instruments.app/Contents/PlugIns/AutomationInstrument.xrplugin/Contents/Resources/Automation.tracetemplate"

SOCKPATH="/tmp/atx-taskqueue.sock"
QUEUE="/usr/local/bin/python -m atx.taskqueue --unix $SOCKPATH --room $UDID"

test -d $RESULTPATH || mkdir $RESULTPATH
case "$1" in
	instruments)
		echo "Start python taskqueue"
		python -m atx.taskqueue web &>/tmp/atx-taskqueue.log &
		echo "Start instruments"
		exec instruments -w ${UDID:?} -t "Automation" -D $WORKDIR/cli.trace $BUNDLE_ID -e UIASCRIPT $TEST &>/tmp/atx-instruments.log # -e UIARESULTSPATH $RESULTPATH
		#exec instruments -w ${UDID:?} -t "$TRACETEMPLATE" $BUNDLE_ID -e UIASCRIPT $TEST # -e UIARESULTSPATH $RESULTPATH
		;;
	run)
		shift
		NOWAIT=
		if test "$1" = "--nowait"
		then
			shift
			NOWAIT=true
		fi
		TASK_ID=$($QUEUE post "$1")
		if test -z "$NOWAIT"
		then
			exec $QUEUE retr "$TASK_ID"
		fi
		;;
	get)
		shift
		# use curl instead of python -m atx.taskqueue get
		curl -ss --unix-socket $SOCKPATH -X GET http:/rooms/$UDID
		;;
	put)
		shift
		# $1: task_id, $2: data
		# echo "{\"id\": \"$1\", \"result\": $2}" | curl -ss --unix-socket $SOCKPATH -X POST http:/rooms/$UDID
		$QUEUE put "$1" "$2"
		;;
	reset)
		# todo, maybe quit too much
		# $QUEUE quit
		$QUEUE clean
		;;
	test)
		$0 run '{"command": 1}'
		;;
	*)
		/bin/echo "Usage: $0 <instruments|run|get|put|reset> [ARGS]"
		;;
esac

