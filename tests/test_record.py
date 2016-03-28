#-*- encoding: utf-8 -*-

# first, attach a transparent window W infront of 
# the watched one. W will watch all mouse & keyboard
# events for the window

# second, on each input event, we check the differences
# between the window screens before and after the event. 

# the differences indicates a shape which is the one
# user touched. We can translate the event into a
# testcase.

# the event response time is crucial and may be varing
# between games & even ui-parts in one game. 

import os
import time

from atx.device.windows import WindowsDevice, find_process_id
from atx.cmds.record import RecorderGUI

"""
static PyObject *PyPumpWaitingMessages(PyObject *self, PyObject *args)
{
    MSG msg;
    long result = 0;
    // Read all of the messages in this next loop, 
    // removing each message as we read it.
    Py_BEGIN_ALLOW_THREADS
    while (PeekMessage(&msg, NULL, 0, 0, PM_REMOVE)) {
        // If it's a quit message, we're out of here.
        if (msg.message == WM_QUIT) {
            result = 1;
            break;
        }
        // Otherwise, dispatch the message.
        DispatchMessage(&msg); 
    } // End of PeekMessage while loop
    Py_END_ALLOW_THREADS
    return PyInt_FromLong(result);
}

// @pymethod |pythoncom|PumpMessages|Pumps all messages for the current thread until a WM_QUIT message.
static PyObject *pythoncom_PumpMessages(PyObject *self, PyObject *args)
{
    MSG msg;
    int rc;
    Py_BEGIN_ALLOW_THREADS
    while ((rc=GetMessage(&msg, 0, 0, 0))==1) {
        TranslateMessage(&msg); // needed?
        DispatchMessage(&msg);
    }
    Py_END_ALLOW_THREADS
    if (rc==-1)
        return PyWin_SetAPIError("GetMessage");
    Py_INCREF(Py_None);
    return Py_None;
}
"""

def main():
    exe_file = "C:\\Windows\\System32\\calc.exe"
    if not find_process_id(exe_file):
        os.startfile(exe_file)
        time.sleep(3)

    win = WindowsDevice(exe_file=exe_file)

    r = RecorderGUI(win)
    r.mainloop()

if __name__ == '__main__':
    main()