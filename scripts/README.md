airtest recorder
==================

## how to use
### record
```sh
adb shell getevent -l | python airtest_recorder.py > main.py
```

### playback
```sh
python main.py
```

# other record tool: monkey runer
monkey_record.py and monkey_playback from
<https://github.com/miracle2k/android-platform_sdk/tree/master/monkeyrunner/scripts>

### AndroidManifest.xml parser
python-androguard: <https://code.google.com/p/androguard/wiki/Usage#Androaxml>

