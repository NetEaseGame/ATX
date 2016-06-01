#-*- encoding: utf-8 -*-

import time
import service

def on_battery(info):
    print 'on battery info', info

def on_rotation(rot):
    print 'on rotation', rot

def test():
    serial = "DU2SSE1467010532"; #hwH60

    from random import randint
    import stfwire_pb2 as wire

    reqs = [
        (wire.GET_VERSION, wire.GetVersionRequest()),
        (wire.DO_IDENTIFY, wire.DoIdentifyRequest(serial=serial)),
        (wire.DO_ADD_ACCOUNT_MENU, wire.DoAddAccountMenuRequest()),
        (wire.DO_REMOVE_ACCOUNT, wire.DoRemoveAccountRequest(type="nsdfjslfs")),
        (wire.GET_ACCOUNTS, wire.GetAccountsRequest(type="root")),
        (wire.GET_BROWSERS, wire.GetBrowsersRequest()),
        (wire.GET_CLIPBOARD, wire.GetClipboardRequest(type=wire.TEXT)),
        (wire.GET_DISPLAY, wire.GetDisplayRequest(id=0)),
        (wire.GET_PROPERTIES, wire.GetPropertiesRequest(properties=["ro.product.device"])),
        (wire.GET_RINGER_MODE, wire.GetRingerModeRequest()),
        (wire.GET_SD_STATUS, wire.GetSdStatusRequest()),
        (wire.GET_WIFI_STATUS, wire.GetWifiStatusRequest()),
        (wire.SET_CLIPBOARD, wire.SetClipboardRequest(type=wire.TEXT, text="hello world")),
        (wire.SET_KEYGUARD_STATE, wire.SetKeyguardStateRequest(enabled=False)),
        (wire.SET_RINGER_MODE, wire.SetRingerModeRequest(mode=wire.VIBRATE)),
        (wire.SET_WAKE_LOCK, wire.SetWakeLockRequest(enabled=False)),
        (wire.SET_WIFI_ENABLED, wire.SetWifiEnabledRequest(enabled=True)),
        (wire.SET_MASTER_MUTE, wire.SetMasterMuteRequest(enabled=True)),
    ]

    total = len(reqs)

    idx = 0
    queue = service.service_queue
    pack = service.pack
    while True:

        if randint(1, 10) < 3 and idx < total:
            mtype, request = reqs[idx]
            msg = pack(mtype, request, idx)
            queue.put(msg)
            idx += 1
        time.sleep(1)

def test_type():
    import sys
    import tty
    import termios
    import locale

    def getchar():
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(sys.stdin.fileno())
            ch = sys.stdin.read(1)
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        return ch

    _, encoding = locale.getdefaultlocale()
    buf = ''
    while True:
        ch = getchar()
        if ch == '\x03': # Ctrl+C
            break
        buf += ch
        try:
            text = buf.decode(encoding)
        except:
            pass
        else:
            print 'try to input', repr(text)
            if len(buf) == 1:
                service.keyboard(buf)
            else:
                service.type(text)
            buf = ''
    
if __name__ == '__main__':
    service.start()

    service.on_battery_event(on_battery)
    service.on_rotation_event(on_rotation)

    service.identify()
    time.sleep(1)
    service.keyevent('KEYCODE_HOME')
    time.sleep(1)

    print service.get_wifi_status()
    print 'disable', service.set_wifi_enabled(False)
    print service.get_wifi_status()
    print 'enable', service.set_wifi_enabled(True)
    print service.get_wifi_status()
    time.sleep(1)

    print service.set_rotation(1)
    print service.set_rotation(2)
    print service.set_rotation(3)
    print service.set_rotation(0)
    time.sleep(1)

    print 'display', service.get_display()
    time.sleep(1)

    print 'test type, please input'
    test_type()

    service.stop()
