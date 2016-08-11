#-*- encoding: utf-8 -*-

import os
import os.path
import time

from atx.record.android import RecordDevice, AndroidRecorder
from atx.record.draft_editor import run as run_draft_editor

def main(serial=None, host=None, port=None, workdir=".", nonui_activities=None, edit_mode=False):
    workdir = os.path.abspath(workdir)
    
    if edit_mode:
        run_draft_editor(workdir, None)
        return

    if not os.path.exists(workdir):
        os.makedirs(workdir)

    d = RecordDevice(serialno=serial, host=host, port=port)

    rec = AndroidRecorder(d, workdir)
    if nonui_activities:
        for a in nonui_activities:
            rec.add_nonui_activity(a)

    rec.start()

    try:
        time.sleep(4)
        print '-'*20 + ' STARTED ' + '-'*20
        print 'Please operate on the phone. Press Ctrl+C to stop.'
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        pass
        
    rec.stop()
    print '-'*20 + ' STOPPED ' + '-'*20

    if len(rec.frames) > 0:
        print 'start web service to modify recorded case'
        run_draft_editor(workdir, None)
    else:
        print 'No action recorded.'

if __name__ == '__main__':
    main()
