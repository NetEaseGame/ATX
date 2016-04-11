#-*- encoding: utf-8 -*-

import os
import time

from test_record import get_device

__dir__ = os.path.dirname(os.path.abspath(__file__))
capture_tmpdir = os.path.join(os.getcwd(), 'screenshots', time.strftime("%Y%m%d"))

def main():
    d = get_device()
    d.image_path = [os.path.join('screenshots', time.strftime("%Y%m%d"))]
    script = os.path.join(capture_tmpdir, 'steps.py')
    try:
        execfile(script)
    except Exception as e:
        raise

if __name__ == '__main__':
    main()