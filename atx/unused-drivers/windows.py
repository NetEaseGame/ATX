#!/usr/bin/env python
# -*- coding: utf-8 -*-
 
 
#from zope.interface import Interface
from PIL import ImageGrab
import win32api,win32con,win32gui,win32process
import autopy
import ctypes,ctypes.wintypes
import pygame
import os
import time


class RECT(ctypes.Structure):# classtype for window position
    _fields_ = [('left', ctypes.c_long),
                ('top', ctypes.c_long),
                ('right', ctypes.c_long),
                ('bottom', ctypes.c_long)]
    def __str__(self):
        return str((self.left, self.top, self.right, self.bottom))

# The following two dictionaries don't contain all the characters; please check before you use them
# A dictionary to hold the characters, which may be used in text, and their corresponding key values
OriginalCodes = {
           '\n':0x0D, #enter
           ' ':0x20, #spacebar
           '\t':0x09, #TAB
           '0':0x30,
           '1':0x31,
           '2':0x32,
           '3':0x33,
           '4':0x34,
           '5':0x35,
           '6':0x36,
           '7':0x37,
           '8':0x38,
           '9':0x39,
           'a':0x41,
           'b':0x42,
           'c':0x43,
           'd':0x44,
           'e':0x45,
           'f':0x46,
           'g':0x47,
           'h':0x48,
           'i':0x49,
           'j':0x4A,
           'k':0x4B,
           'l':0x4C,
           'm':0x4D,
           'n':0x4E,
           'o':0x4F,
           'p':0x50,
           'q':0x51,
           'r':0x52,
           's':0x53,
           't':0x54,
           'u':0x55,
           'v':0x56,
           'w':0x57,
           'x':0x58,
           'y':0x59,
           'z':0x5A,
           '+':0xBB,
           ',':0xBC,
           '-':0xBD,
           '.':0xBE,
           '/':0xBF,
           '`':0xC0,
           ';':0xBA,
           '[':0xDB,
           '\\':0xDC,
           ']':0xDD,
           "'":0xDE,
           '`':0xC0}
# A dictionary which contains the characters should be typed with shift
ShiftCodes = {  
           'A':0x41,
           'B':0x42,
           'C':0x43,
           'D':0x44,
           'E':0x45,
           'F':0x46,
           'G':0x47,
           'H':0x48,
           'I':0x49,
           'J':0x4A,
           'K':0x4B,
           'L':0x4C,
           'M':0x4D,
           'N':0x4E,
           'O':0x4F,
           'P':0x50,
           'Q':0x51,
           'R':0x52,
           'S':0x53,
           'T':0x54,
           'U':0x55,
           'V':0x56,
           'W':0x57,
           'X':0x58,
           'Y':0x59,
           'Z':0x5A,
           ')':0x30,
           '!':0x31,
           '@':0x32,
           '#':0x33,
           '$':0x34,
           '%':0x35,
           '^':0x36,
           '&':0x37,
           '*':0x38,
           '(':0x39,
           '?':0xBF,
           '~':0xC0,
           ':':0xBA,
           '{':0xDB,
           '|':0xDC,
           '}':0xDD,
           "\"":0xDE}


#class Device(Interface):
class Device():
    ''' Interface documentation '''
    def __init__(self,filename=None):
        if '.exe' != filename[-4:len(filename)]:#check the name has postfix ".exe" or not; if not, add ".exe" to the end
            self.filename = filename+".exe"
        else:
            self.filename = filename
        HWND=self._getHandleThroughFilename()
        self.HWND = self._chosegamehandle(HWND)
        # print 'HWND:', self.HWND
        if not self.HWND:
            raise Exception('Can not find target application process')
        
    def _getHandleThroughFilename(self):
        Psapi = ctypes.WinDLL('Psapi.dll')
        EnumProcesses = Psapi.EnumProcesses
        EnumProcesses.restype = ctypes.wintypes.BOOL
        GetProcessImageFileName = Psapi.GetProcessImageFileNameA
        GetProcessImageFileName.restype = ctypes.wintypes.DWORD

        Kernel32 = ctypes.WinDLL('kernel32.dll')
        OpenProcess = Kernel32.OpenProcess
        OpenProcess.restype = ctypes.wintypes.HANDLE
        TerminateProcess = Kernel32.TerminateProcess
        TerminateProcess.restype = ctypes.wintypes.BOOL
        CloseHandle = Kernel32.CloseHandle
        

        MAX_PATH = 260
        PROCESS_TERMINATE = 0x0001
        PROCESS_QUERY_INFORMATION = 0x0400

        count = 32
        while True:
            ProcessIds = (ctypes.wintypes.DWORD*count)()
            cb = ctypes.sizeof(ProcessIds)
            BytesReturned = ctypes.wintypes.DWORD()
            if EnumProcesses(ctypes.byref(ProcessIds), cb, ctypes.byref(BytesReturned)):
                if BytesReturned.value<cb:
                    break
                else:
                    count *= 2
            else:
                raise Exception('Call to EnumProcesses failed')

        for index in range(BytesReturned.value / ctypes.sizeof(ctypes.wintypes.DWORD)):
            ProcessId = ProcessIds[index]
            hProcess = OpenProcess(PROCESS_TERMINATE | PROCESS_QUERY_INFORMATION, False, ProcessId)
            if hProcess:
                ImageFileName = (ctypes.c_char*MAX_PATH)()
                if GetProcessImageFileName(hProcess, ImageFileName, MAX_PATH)>0:
                    filename = os.path.basename(ImageFileName.value)
                    if filename == self.filename:
                        break
                #TerminateProcess(hProcess, 1)
                CloseHandle(hProcess)
                
        def get_hwnds_for_pid(pid):
            def callback (hwnd, hwnds):
                if win32gui.IsWindowVisible (hwnd) and win32gui.IsWindowEnabled (hwnd):
                    _, found_pid = win32process.GetWindowThreadProcessId (hwnd)
                    if found_pid == pid:
                        hwnds.append (hwnd)
                    return True
            hwnds = []
            win32gui.EnumWindows(callback, hwnds)
            return hwnds
        return get_hwnds_for_pid(ProcessId)
    
    def _chosegamehandle(self,HWND):
            if not HWND : return HWND
            else:
                for handle in HWND:
                    windowtext = win32gui.GetWindowText(handle)
                    if ":" not in windowtext: 
                        return handle
                        
    
        
    def _range(self):
        ''' Get Windows rectangle position '''
        rect = RECT()
        ctypes.windll.user32.GetWindowRect(self.HWND,ctypes.byref(rect))
        range_ = (rect.left+2,rect.top+2,rect.right-2,rect.bottom-2)
        return range_

    def _resetpt(self, x, y):
        left, top, _, _ = self._range()
        x, y = left+x, top+y
        return x, y
    
    def snapshot(self, filename=None ):
        ''' Capture device screen '''
        range_ = self._range()
        win32gui.SetForegroundWindow(self.HWND)
        time.sleep(0.1)
        pic = ImageGrab.grab(range_)
        if filename !=None:
            pic.save(filename)
        return pic
        
    def touch(self, x, y, duration=0.1):
        ''' Simulate touch '''
        (ox, oy) = self.mouseposition() # remember mouse position
        x, y = self._resetpt(x, y)
        win32api.SetCursorPos((x,y))

        win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN,0,0)
        time.sleep(duration)
        win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP,0,0)
        win32api.SetCursorPos((ox,oy)) # move back mouse position

        
    def drag(self, (x1, y1), (x2, y2), duration=0.5):
        ''' Simulate drag '''
        (ox, oy) = self.mouseposition() # remember mouse position
        x1, y1 = self._resetpt(x1, y1)
        x2, y2 = self._resetpt(x2, y2)
        win32api.SetCursorPos((x1, y1))
        win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN,0,0)
        autopy.mouse.smooth_move(x2, y2)
        win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP,0,0)
        win32api.SetCursorPos((ox,oy)) # move back mouse position
        
    def type(self, text):
        ''' Type text into device '''
        
        for c in text:
            if c in ShiftCodes:  #judge the character is a capital letter or not; 16 is the value of shift
                win32api.keybd_event(16,win32api.MapVirtualKey(16,0),0,0)
                win32api.keybd_event(ShiftCodes[c],win32api.MapVirtualKey(ShiftCodes[c],0),0,0)
                win32api.keybd_event(16,win32api.MapVirtualKey(16,0),win32con.KEYEVENTF_KEYUP,0)
                win32api.keybd_event(ShiftCodes[c],win32api.MapVirtualKey(ShiftCodes[c],0),win32con.KEYEVENTF_KEYUP,0)
            elif c in OriginalCodes:    #judge the character is a capital letter or not
                win32api.keybd_event(OriginalCodes[c],win32api.MapVirtualKey(OriginalCodes[c],0),0,0)
                win32api.keybd_event(OriginalCodes[c],win32api.MapVirtualKey(OriginalCodes[c],0),win32con.KEYEVENTF_KEYUP,0)
    
    def shape(self):
        ''' Return (width, height) '''
        pic = self.snapshot(filename=None)
        (width, height) =  pic.size
        return (width, height)
    
    def cutimage(self, filename=None):
        '''Cut picture from target window'''
        pic = self.snapshot(filename=None)
        mode = pic.mode
        size = pic.size
        data = pic.tostring()
        surface = pygame.image.fromstring(data, size, mode)
        s=pygame.display.set_mode(surface.get_size())
        box=k=0
        c=1
        while c:
            for evt in pygame.event.get():
                evt_type=evt.type
                if evt_type==5: x1,y1=evt.pos;k=1        # mouse down
                if evt_type==4 and k: x2,y2=evt.pos; box=(x1,y1,x2-x1,y2-y1) #mouse up and calculate the box range
                if evt_type==6: c=0
                s.blit(surface,(0,0))
                if box and c:pygame.draw.rect(s,0,box,1) 
                pygame.display.flip()
        q=s.subsurface(box)
        if filename!=None:
            pygame.image.save(q,filename)
        pygame.quit()
        
    def mouseposition(self):
        '''Get the current position of mouse'''
        class POINT(ctypes.Structure):
            _fields_ = [
                        ("x", ctypes.c_ulong),
                        ("y", ctypes.c_ulong)
                        ]
        point = POINT()
        ctypes.windll.User32.GetCursorPos(ctypes.byref(point))
        return point.x, point.y 
    
    def windowposition(self):
        '''Get the position of target window while given its name'''
        rect = RECT()
        ctypes.windll.user32.GetWindowRect(self.HWND,ctypes.byref(rect))
        return rect.left,rect.top,rect.right,rect.bottom
    
    def start(self, appname, extra={}):
        '''Start an app, TODO(not good now)'''
        '''appname is not used in windows interferences'''
        Path = extra.get('path')
        os.system('cd /d '+Path+' && '+'start '+self.filename)
        HWND=self._getHandleThroughFilename()
        self.HWND = self._chosegamehandle(HWND)
        if self.HWND==0:
            raise Exception(u'Target application is not successfully started')
        
    def stop(self, appname, extra={}):
        '''appname is not used in windows interferences'''
        win32gui.SendMessage(self.HWND,win32con.WM_CLOSE,0,0)
        
    def getCpu(self, appname):
        ''' Return cpu: float (Cpu usage for app) '''
        return 0.0
        
    def getMem(self, appname):
        ''' Return mem: float (unit MB, memory usage for app) '''
        return {}
