#!/usr/bin/python3.3
"""
Prepare internal ejudge xml runlog to import runs in another contest
This script converts names of problems and moves time of runs to another reference frame
"""
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

if len(sys.argv) > 2:
    prob_prefix = sys.argv[2]
else:
    prob_prefix = input('problem name prefix: ')

convert_prob_name = lambda x: prob_prefix + x

for run in runlog_root[0]:
    run_time = int(run.attrib['time']) + int(time_offset)
    run.set('time', str(run_time))

    run_prob_name = convert_prob_name(run.attrib['prob_short'])
    run.set('prob_short', run_prob_name)

runlog.write('new_' + path)