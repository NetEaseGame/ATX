from airtest import jsonlog
import json
import os

def test_logdict():
    log = jsonlog.JSONLog('test.log')
    log.writeline({'type':'message'})
    j = json.loads(open('test.log').readlines()[-1])
    assert j.get('type') == 'message'
    os.unlink('test.log')

