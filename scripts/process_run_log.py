#!/usr/bin/python3.3
import sys

__author__ = 'ksg'

from xml.etree import ElementTree
import time

if len(sys.argv) > 1:
    path = sys.argv[1]
else:
    path = input('path to runlog: ')

runlog = ElementTree.parse(path)
runlog_root = runlog.getroot()

# 'start_time': '2014/01/15 10:00:00'
cur_start_time = time.mktime(time.strptime(runlog_root.attrib['start_time'], '%Y/%m/%d %H:%M:%S'))
archive_start_time = time.mktime(time.strptime('2013/10/07 23:08:14', '%Y/%m/%d %H:%M:%S'))
time_offset = cur_start_time - archive_start_time

prob_pref = 'omsu13-14-r1_'

for run in runlog_root[0]:
    run_time = int(run.attrib['time']) + int(time_offset)
    run.set('time', str(run_time))

    run_prob_id = prob_pref + run.attrib['prob_short']
    run.set('prob_short', run_prob_id)

runlog.write('new_' + path)