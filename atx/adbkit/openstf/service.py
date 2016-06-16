#-*- encoding: utf-8 -*-
# python client for openstf STFService & Agent.
#
# Api:
#   start(adbprefix=None, service_port=1100, agent_port=1090)
#   stop(adbprefix=None, service_port=1100, agent_port=1090)
#
#   wake()              # return None
#   type(text)          # return None
#   ascii_type(text)                    # return None
#   keyevent(key, event='PRESS')        # return None
#   keyboard(char, holdtime=None)       # return None
#
#   identify()                          # return bool(success or not)
#   set_rotation(rotation, lock=False)  # return bool(success or not)
#   set_wifi_enabled(True)              # return bool(success or not)
#   get_wifi_status()                   # return a dict
#   get_display()                       # return a dict
#   get_properties(*args)               # return a dict
#
#   on_battery_event(callback)      # callback accept a dict argument
#   on_rotation_event(callback)     # callback accept a int argument
#   on_connectivity_event(callback) # callback accept a dict argument

import time
import subprocess
import select
import socket
import traceback
import Queue
import threading
import warnings

#from google.protobuf.descriptor import FieldDescriptor
from google.protobuf.internal import encoder, decoder

import stfwire_pb2 as wire
import keycode


__all__ = ['start', 'stop', 'isalive', 'identify', 'type', 'keyevent', 'get_wifi_status', 'set_wifi_enabled', 
    'set_rotation', 'get_display', 'get_properties', 'on_battery_event', 'on_rotation_event']

messages = {
    wire.DO_IDENTIFY : (wire.DoIdentifyRequest, wire.DoIdentifyResponse),
    wire.DO_KEYEVENT : (wire.KeyEventRequest, None),
    wire.DO_TYPE: (wire.DoTypeRequest, None),
    wire.DO_WAKE: (wire.DoWakeRequest, None),
    wire.DO_ADD_ACCOUNT_MENU: (wire.DoAddAccountMenuRequest, wire.DoAddAccountMenuResponse),
    wire.DO_REMOVE_ACCOUNT: (wire.DoRemoveAccountRequest, wire.DoRemoveAccountResponse),
    wire.GET_ACCOUNTS: (wire.GetAccountsRequest, wire.GetAccountsResponse),
    wire.GET_BROWSERS: (wire.GetBrowsersRequest, wire.GetBrowsersResponse),
    wire.GET_CLIPBOARD: (wire.GetClipboardRequest, wire.GetClipboardResponse),
    wire.GET_DISPLAY: (wire.GetDisplayRequest, wire.GetDisplayResponse),
    wire.GET_PROPERTIES: (wire.GetPropertiesRequest, wire.GetPropertiesResponse),
    wire.GET_RINGER_MODE: (wire.GetRingerModeRequest, wire.GetRingerModeResponse),
    wire.GET_SD_STATUS: (wire.GetSdStatusRequest, wire.GetSdStatusResponse),
    wire.GET_VERSION: (wire.GetVersionRequest, wire.GetVersionResponse),
    wire.GET_WIFI_STATUS: (wire.GetWifiStatusRequest, wire.GetWifiStatusResponse),
    wire.SET_CLIPBOARD: (wire.SetClipboardRequest, wire.SetClipboardResponse),
    wire.SET_KEYGUARD_STATE: (wire.SetKeyguardStateRequest, wire.SetKeyguardStateResponse),
    wire.SET_RINGER_MODE: (wire.SetRingerModeRequest, wire.SetRingerModeResponse),
    wire.SET_ROTATION: (wire.SetRotationRequest, None),
    wire.SET_WAKE_LOCK: (wire.SetWakeLockRequest, wire.SetWakeLockResponse),
    wire.SET_WIFI_ENABLED: (wire.SetWifiEnabledRequest, wire.SetWifiEnabledResponse),
    wire.SET_MASTER_MUTE: (wire.SetMasterMuteRequest, wire.SetMasterMuteResponse),
    wire.EVENT_AIRPLANE_MODE: (None, wire.AirplaneModeEvent),
    wire.EVENT_BATTERY: (None, wire.BatteryEvent),
    wire.EVENT_CONNECTIVITY: (None, wire.ConnectivityEvent),
    wire.EVENT_PHONE_STATE: (None, wire.PhoneStateEvent),
    wire.EVENT_ROTATION: (None, wire.RotationEvent),
    wire.EVENT_BROWSER_PACKAGE: (None, wire.BrowserPackageEvent),
}

def pack(mtype, request, rid=None):
    '''pack request to delimited data'''
    envelope = wire.Envelope() 
    if rid is not None:
        envelope.id = rid
    envelope.type = mtype
    envelope.message = request.SerializeToString()
    data = envelope.SerializeToString()
    data = encoder._VarintBytes(len(data)) + data
    return data

def unpack(data):
    '''unpack from delimited data'''
    size, position = decoder._DecodeVarint(data, 0)
    envelope = wire.Envelope() 
    envelope.ParseFromString(data[position:position+size])
    return envelope

def _id_generator():
    request_id = [0]
    def _next():
        if request_id[0] == 0xffffffff: #uint32
            request_id[0] = 0
        request_id[0] += 1
        return request_id[0]
    return _next

get_request_id = _id_generator()

eventhooks = {}     # called when events arrived
# initialize eventhooks
for mtype, (req_class, _) in messages.iteritems():
    if req_class is None:
        eventhooks[mtype] = []
del mtype, req_class

responses = {}      # save service call response, for synchronize
service_response_lock = threading.Lock()

def route(envelope):
    _, resp_class = messages[envelope.type]
    resp = resp_class()
    resp.ParseFromString(envelope.message)
    # service calls should have id
    if envelope.id:
        with service_response_lock:
            rid = envelope.id
            # remove placeholder if the response is not needed
            if rid in responses:
                del responses[rid]
            else:
                responses[rid] = resp
        return
    # handle events
    hooks = eventhooks.get(envelope.type)
    if hooks is not None:
        for func in hooks:
            try:
                func(resp)
            except:
                traceback.print_exc()
        return
    # no handler found
    warnings.warn('No handler found for %s(%s)' % (resp_class.DESCRIPTOR.name, envelope.type))

def wait_response(rid, timeout=1):
    timeout = time.time() + timeout
    while timeout > time.time():
        with service_response_lock:
            if rid in responses:
                return responses.pop(rid)
        time.sleep(0.1)
    # cleanup timeouted response, avoid memory leak by add a placeholder!
    with service_response_lock:
        if rid in responses:
            del responses[rid]
        else:
            responses[rid] = None

def register_eventhook(mtype, callback):
    global eventhooks
    eventhooks[mtype].append(callback)

def start_stf_service(adbprefix=None, port=1100):
    if adbprefix is None: 
        adbprefix = ['adb']
    cmds = [['shell', 'am', 'startservice'],
            ['--user', '0'],
            ['-a', 'jp.co.cyberagent.stf.ACTION_START', '-n', 'jp.co.cyberagent.stf/.Service']]
    
    command = adbprefix + cmds[0] + cmds[1] + cmds[2]

    print subprocess.check_output(command)
    # if falied, using:
    # command = cmds[0] + cmds[2]
    command = adbprefix + ['forward', 'tcp:%s' % port, 'tcp:1100'] # remote port use default 1100, although it can be changed
    subprocess.call(command)

def stop_stf_service(adbprefix=None, port=1100):
    if adbprefix is None: 
        adbprefix = ['adb']
    command = adbprefix + ['forward', '--remove', 'tcp:%s' % port]
    subprocess.call(command)

    command = adbprefix + ['shell', 'am', 'stopservice', '-n', 'jp.co.cyberagent.stf/.Service']
    subprocess.call(command)

def check_stf_agent(adbprefix=None, kill=False):
    '''return True if agent is alive.'''
    if adbprefix is None: 
        adbprefix = ['adb']
    command = adbprefix + ['shell', 'ps']
    out = subprocess.check_output(command).strip()
    out = out.splitlines()
    if len(out) > 1:
        first, out = out[0], out[1:]
        idx = first.split().index('PID')
        pid = None
        for line in out:
            if 'stf.agent' in line:
                pid = line.split()[idx]
                print 'stf.agent is running, pid is', pid
                break
        if pid is not None:
            if kill:
                print 'killing', pid
                command = adbprefix + ['shell', 'kill', '-9', pid]
                subprocess.call(command)
                return False
            return True
    return False

def start_stf_agent(adbprefix=None, restart=False, port=1090):
    if adbprefix is None: 
        adbprefix = ['adb']
    if check_stf_agent(adbprefix, kill=restart):
        return

    command = adbprefix + ['shell', 'pm', 'path', 'jp.co.cyberagent.stf']
    out = subprocess.check_output(command).strip()
    path = out.split(':')[-1]
    print 'stf agent path', repr(path)
    
    command = adbprefix + ['shell', 'CLASSPATH="%s"' % path, 
            'app_process', '/system/bin', 'jp.co.cyberagent.stf.Agent']
    p = subprocess.Popen(command, stdout=subprocess.PIPE)
    # IMPORTANT! wait for agent to start listening.
    p.stdout.readline()

    command = adbprefix + ['forward', 'tcp:%s' % port, 'tcp:1090'] # remote port is 1090, cannot change
    subprocess.call(command)

def stop_stf_agent(adbprefix=None, port=1090):
    if adbprefix is None: 
        adbprefix = ['adb']
    command = adbprefix + ['forward', '--remove', 'tcp:%s' % port]
    subprocess.call(command)

    check_stf_agent(adbprefix, kill=True)

service_queue = Queue.Queue()
agent_queue = Queue.Queue()
stop_event = threading.Event()

def isalive():
    return stop_event.isSet()

def listen_service(service_port=1100): 
    # service, send & recv, use timeout
    def _service():
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect(('127.0.0.1', service_port))
            while not stop_event.isSet():
                r, w, _ = select.select([s], [s], [], 0.1) 
                if s in r:
                    data = s.recv(1024)
                    if not data:
                        continue
                    try:
                        envelope = unpack(data)
                        route(envelope)
                    except:
                        print 'error while handle response'
                        traceback.print_exc()
                if s in w:
                    try:
                        message = service_queue.get_nowait()
                    except Queue.Empty:
                        pass
                    else:
                        s.sendall(message)
        except:
            traceback.print_exc()
        finally:
            s.close()
            print 'Service socket closed'
            stop_event.set()

    t = threading.Thread(target=_service)
    t.setDaemon(True)
    t.start()

def listen_agent(agent_port=1090):
    # just send, no recv
    def _agent():
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect(('127.0.0.1', agent_port))
            while not stop_event.isSet():
                message = agent_queue.get() 
                s.sendall(message)
        except:
            traceback.print_exc()
        finally:
            s.close()
            print 'Agent socket closed.'
            stop_event.set()

    t = threading.Thread(target=_agent)
    t.setDaemon(True)
    t.start()

#--------------------------- API functions ----------------------------

def start(adbprefix=None, service_port=1100, agent_port=1090):
    start_stf_service(adbprefix, port=service_port)
    start_stf_agent(adbprefix, port=agent_port)
    stop_event.clear()
    listen_service(service_port)
    listen_agent(agent_port)

def stop(adbprefix=None, service_port=1100, agent_port=1090):
    stop_event.set()
    stop_stf_service(adbprefix, port=service_port)
    stop_stf_agent(adbprefix, port=agent_port)

# agent 
def keyevent(key, event=wire.PRESS, shift=False, ctrl=False, alt=False, meta=False, 
        sym=False, function=False, capslock=False, scrolllock=False, numlock=False):
    if isinstance(event, basestring):
        event = event.upper()
        assert event in ('DOWN', 'UP', 'PRESS')
        event = getattr(wire, event)
    if isinstance(key, basestring):
        if not key.startswith('KEYCODE_'):
            key = 'KEYCODE_%s' % key
        key = getattr(keycode, key)
    req = wire.KeyEventRequest()
    req.event = event
    req.keyCode = key
    req.shiftKey = shift
    req.ctrlKey = ctrl
    req.altKey = alt
    req.metaKey = meta
    req.symKey = sym
    req.functionKey = function
    req.capsLockKey = capslock
    req.scrollLockKey = scrolllock
    req.numLockKey = numlock
    msg = pack(wire.DO_KEYEVENT, req)
    agent_queue.put(msg)

# simple keyboard input
def keyboard(char, holdtime=None):
    shift = False
    ctrl = False
    if len(char) > 1:
        char = char.upper()
        if not char.startswith('KEYCODE_'):
            char = 'KEYCODE_%s' % char
        code = getattr(keycode, char, None)
        if code is None:
            print 'invalid keycode', char
            return
    elif char in 'abcdefghijklmnopqrstuvwxyz1234567890':
        code = getattr(keycode, 'KEYCODE_%s' % char.upper())
    elif char in 'ABCDEFGHIJLKMNOPQRSTUVWXYZ':
        code = getattr(keycode, 'KEYCODE_%s' % char)
        shift = True
    elif char in keycode.SHIFTED_KEYS:
        code = keycode.SHIFTED_KEYS[char]
        shift = True
    elif char in keycode.KEYBOARD_KEYS:
        code = keycode.KEYBOARD_KEYS[char]
    elif char in keycode.CTRLED_KEYS:
        code = keycode.CTRLED_KEYS[char]
        ctrl = True
    else:
        print 'invalid char', repr(char)
        return

    if holdtime is None:
        req = wire.KeyEventRequest(event=wire.PRESS, keyCode=code, shiftKey=shift, ctrlKey=ctrl)
        msg = pack(wire.DO_KEYEVENT, req)
        agent_queue.put(msg)
    else:
        # keydown
        req = wire.KeyEventRequest(event=wire.DOWN, keyCode=code, shiftKey=shift, ctrlKey=ctrl)
        msg = pack(wire.DO_KEYEVENT, req)
        agent_queue.put(msg)
        # wait
        time.sleep(holdtime)
        # keyup
        req = wire.KeyEventRequest(event=wire.UP, keyCode=code, shiftKey=shift, ctrlKey=ctrl)
        msg = pack(wire.DO_KEYEVENT, req)
        agent_queue.put(msg)

# agent, can input asciis only
def ascii_type(text):
    msg = pack(wire.DO_TYPE, wire.DoTypeRequest(text=text))
    agent_queue.put(msg)

# agent
def set_rotation(rotation, lock=False):
    msg = pack(wire.SET_ROTATION, wire.SetRotationRequest(rotation=rotation, lock=lock))
    agent_queue.put(msg)

# agent
def wake():
    msg = pack(wire.DO_WAKE, wire.DoWakeRequest())
    agent_queue.put(msg)

# use both agent & service to input unicode characters
# TODO make it atomic, maybe use another queue?
def type(text):
    rid = get_request_id()
    msg = pack(wire.SET_CLIPBOARD, wire.SetClipboardRequest(type=wire.TEXT, text=text), rid)
    service_queue.put(msg)
    # wait for clipboard result
    resp = wait_response(rid)
    if resp and resp.success:
        keyevent(keycode.KEYCODE_V, wire.PRESS, ctrl=True)
        return True
    return False

def identify():
    rid = get_request_id()
    serial = ""
    msg = pack(wire.DO_IDENTIFY, wire.DoIdentifyRequest(serial=serial), rid)
    service_queue.put(msg)
    resp = wait_response(rid)
    return resp and resp.success

def get_wifi_status():
    # return True if wifi is enabled.
    rid = get_request_id()
    msg = pack(wire.GET_WIFI_STATUS, wire.GetWifiStatusRequest(), rid)
    service_queue.put(msg)
    resp = wait_response(rid)
    return resp and resp.success and resp.status

def set_wifi_enabled(enabled):
    rid = get_request_id()
    msg = pack(wire.SET_WIFI_ENABLED, wire.SetWifiEnabledRequest(enabled=bool(enabled)), rid)
    service_queue.put(msg)
    resp = wait_response(rid, timeout=5) # may ask for user permission
    return resp and resp.success

def get_display(deviceid=0):
    rid = get_request_id()
    msg = pack(wire.GET_DISPLAY, wire.GetDisplayRequest(id=deviceid), rid)
    service_queue.put(msg)
    resp = wait_response(rid)
    if not resp or not resp.success:
        return {}
    fields = [f.name for f in wire.GetDisplayResponse.DESCRIPTOR.fields]
    data = dict([(f, getattr(resp, f)) for f in fields])
    return data

def get_properties(*args):
    rid = get_request_id()
    msg = pack(wire.GET_PROPERTIES, wire.GetPropertiesRequest(properties=["ro.product.device"]))
    service_queue.put(msg)
    resp = wait_response(rid)
    res = {}
    if not resp or not resp.success:
        return res
    for prop in resp.properties:
        res[prop.name] = prop.value
    return res

def on_battery_event(callback):
    fields = [f.name for f in wire.BatteryEvent.DESCRIPTOR.fields]
    def _cb(resp):
        data = dict([(f, getattr(resp, f)) for f in fields])
        callback(data)
    register_eventhook(wire.EVENT_BATTERY, _cb)

def on_rotation_event(callback):
    def _cb(resp):
        callback(resp.rotation)
    register_eventhook(wire.EVENT_ROTATION, _cb)

def on_connectivity_event(callback):
    fields = [f.name for f in wire.ConnectivityEvent.DESCRIPTOR.fields]
    def _cb(resp):
        data = dict([(f, getattr(resp, f)) for f in fields])
        callback(data)
    register_eventhook(wire.EVENT_CONNECTIVITY, _cb)
