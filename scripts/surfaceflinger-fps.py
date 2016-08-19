# coding: utf-8
#
# author: codeskyblue(hzsunshx)
# created: 2016-05-16
# modified: 2016-08-19
#
# Experiment of caculate FPS of android without root
# code reference from chromiumwebapps/chromium
#
# It is insteresting to know this way which can calculate not only fps, but also every frame use time.
# Is it really useful, I don't know, really don't know.
# so code just stop here.

import time
import subprocess
import re

nanoseconds_per_second = 1e9

# view = 'SurfaceView'

def get_top_view():
    out = subprocess.check_output(['adb', 'shell', 'dumpsys', 'SurfaceFlinger'])
    lines = out.replace('\r\n', '\n').splitlines()
    max_area = 0
    top_view = None
    for index, line in enumerate(lines):
        line = line.strip()
        if not line.startswith('+ Layer '):
            continue
        m = re.search(r'\((.+)\)', line)
        if not m:
            continue
        view_name = m.group(1)
        (x0, y0, x1, y1) = map(int, re.findall(r'(\d+)', lines[index+4]))
        cur_area = (x1-x0) * (y1-y0)
        if cur_area > max_area:
            max_area = cur_area
            top_view = view_name
    return top_view


def init_frame_data(view):
    out = subprocess.check_output(['adb', 'shell', 'dumpsys', 'SurfaceFlinger', '--latency-clear', view])
    if out.strip() != '':
        raise RuntimeError("Not supported.")
    time.sleep(0.1)
    (refresh_period, timestamps) = frame_data(view)
    base_timestamp = 0
    base_index = 0
    for timestamp in timestamps:
        if timestamp != 0:
            base_timestamp = timestamp
            break
        base_index += 1

    if base_timestamp == 0:
        raise RuntimeError("Initial frame collect failed")
    return (refresh_period, base_timestamp, timestamps[base_index:])


def frame_data(view):
    out = subprocess.check_output(['adb', 'shell', 'dumpsys', 'SurfaceFlinger', '--latency', view])
    results = out.splitlines()
    refresh_period = long(results[0]) / nanoseconds_per_second
    timestamps = []
    for line in results[1:]:
        fields = line.split()
        if len(fields) != 3:
            continue
        (start, submitting, submitted) = map(int, fields)
        if submitting == 0:
            continue

        timestamp = submitting/nanoseconds_per_second
        timestamps.append(timestamp)
    return (refresh_period, timestamps)


def continue_collect_frame_data():
    view = get_top_view()
    if view is None:
        raise RuntimeError("Fail to get current SurfaceFlinger view")
    print 'Current view:', view

    refresh_period, base_timestamp, timestamps = init_frame_data(view)
    while True:
        refresh_period, tss = frame_data(view)
        last_index = 0
        if timestamps:
            recent_timestamp = timestamps[-2]
            last_index = tss.index(recent_timestamp)
        timestamps = timestamps[:-2] + tss[last_index:]
        
        time.sleep(1.5)
        
        ajusted_timestamps = []
        for seconds in timestamps[:]:
            seconds -= base_timestamp
            if seconds > 1e6: # too large, just ignore
                continue
            ajusted_timestamps.append(seconds)

        from_time = ajusted_timestamps[-1] - 1.0
        fps_count = 0
        for seconds in ajusted_timestamps:
            if seconds > from_time:
                fps_count += 1
        print fps_count, len(ajusted_timestamps)

        # print ajusted_timestamps


if __name__ == '__main__':
    continue_collect_frame_data()
