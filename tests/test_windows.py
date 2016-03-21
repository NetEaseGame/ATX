#-*- encoding: utf-8 -*-

import os
import time

from atx.windevice import Window, WindowsDevice

##print dir(self._memdc)
#'AbortDoc', 'Arc', 'AttachObject', 'BeginPath', 
#'BitBlt', 'Chord', 'CreateCompatibleDC', 'CreatePrinterDC', 
#'DPtoLP', 'DeleteDC', 'Draw3dRect', 'DrawFocusRect', 
#'DrawFrameControl', 'DrawIcon', 'DrawText', 'Ellipse', 
#'EndDoc', 'EndPage', 'EndPath', 'ExtTextOut', 'FillPath', 
#'FillRect', 'FillSolidRect', 'FrameRect', 'GetAttachedObject', 
#'GetBrushOrg', 'GetClipBox', 'GetCurrentPosition', 'GetDeviceCaps', 
#'GetHandleAttrib', 'GetHandleOutput', 'GetMapMode', 'GetNearestColor', 
#'GetPixel', 'GetSafeHdc', 'GetTextExtent', 'GetTextExtentPoint', 
#'GetTextFace', 'GetTextMetrics', 'GetViewportExt', 'GetViewportOrg', 
#'GetWindowExt', 'GetWindowOrg', 'IntersectClipRect', 'IsPrinting', 
#'LPtoDP', 'LineTo', 'MoveTo', 'OffsetViewportOrg', 'OffsetWindowOrg', 
#'PatBlt', 'Pie', 'PolyBezier', 'Polygon', 'Polyline', 'RealizePalette', 
#'RectVisible', 'Rectangle', 'RestoreDC', 'SaveDC', 'ScaleViewportExt', 
#'ScaleWindowExt', 'SelectClipRgn', 'SelectObject', 'SelectPalette', 
#'SetBkColor', 'SetBkMode', 'SetBrushOrg', 'SetGraphicsMode', 'SetMapMode', 
#'SetPixel', 'SetPolyFillMode', 'SetROP2', 'SetTextAlign', 'SetTextColor', 
#'SetViewportExt', 'SetViewportOrg', 'SetWindowExt', 'SetWindowOrg', 
#'SetWorldTransform', 'StartDoc', 'StartPage', 'StretchBlt', 
#'StrokeAndFillPath', 'StrokePath', 'TextOut'

##print dir(bmp)
#'AttachObject', 'CreateCompatibleBitmap', 'GetAttachedObject', 
#'GetBitmapBits', 'GetHandle', 'GetInfo', 'GetSize', 'LoadBitmap', 
#'LoadBitmapFile', 'LoadPPMFile', 'Paint', 'SaveBitmapFile'

def test():
    name = u"Windows 任务管理器"
    filepath = "C:\\Windows\\System32\\calc.exe"
    # win = Window(name.encode("gbk"))
    win = Window(exe_file=filepath)
    print win.position
    print win.size
    win.test()


if __name__ == '__main__':
    test()    