set -eux
TARGET=/data/local/tmp
GOARCH=arm go build airinput.go
adb push airinput $TARGET/
adb shell chmod 755 $TARGET/airinput
#adb shell rm $TARGET/devices.json
#adb shell $TARGET/airinput test
