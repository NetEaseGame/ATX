
import time

from airtest import patch

def test_go():
    d = {}
    @patch.go
    def echo_hello(d):
        time.sleep(0.02)
        d['name'] = 'nice'
    p = echo_hello(d)
    assert d.get('name') == None
    p.join()
    assert d.get('name') == 'nice'

