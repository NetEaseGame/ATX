adb push hello /data/local/tmp
adb shell chmod 755 /data/local/tmp/hello
adb shell /data/local/tmp/hello test
