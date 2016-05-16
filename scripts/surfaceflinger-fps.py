# coding: utf-8
#
# author: codeskyblue
# created: 2016-05-16
#
# code reference from chromiumwebapps/chromium
#
# It is insteresting to know this way which can calculate not only fps, but also every frame use time.
# Is it really useful, I don't know, really don't know.
# so code just stop here.

import time
import subprocess


nanoseconds_per_second = 1e9

view = 'SurfaceView'

def init_frame_data():
    out = subprocess.check_output(['adb', 'shell', 'dumpsys', 'SurfaceFlinger', '--latency-clear', view])
    if out.strip() != '':
        raise RuntimeError("Not supported.")
    time.sleep(0.1)
    (refresh_period, timestamps) = frame_data()
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


def frame_data():
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
    refresh_period, base_timestamp, timestamps = init_frame_data()
    while True:
        refresh_period, tss = frame_data()
        last_index = 0
        if timestamps:
            recent_timestamp = timestamps[-2]
            last_index = tss.index(recent_timestamp)
        timestamps = timestamps[:-2] + tss[last_index:]
        time.sleep(1.5)
        ajusted_timestamps = []
        for seconds in timestamps[-4:]:
            seconds -= base_timestamp
            if seconds > 1e6: # too large, just ignore
                continue
            ajusted_timestamps.append(seconds)
        print ajusted_timestamps


if __name__ == '__main__':
    continue_collect_frame_data()
