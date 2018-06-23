"""Calculate failure rate and average of time taken for report files, and print results.
examples:
from eztest.calc_report import calc
calc(["a.csv", "b.csv"], 30)
calc("a.csv")
calc("folder_a")

# Or run from command line
eztest --calc "a.csv" "b.csv" --group-minutes 30
eztest --calc "a.csv"
eztest --calc "folder_a"

Output:
Case Id,Fail Count,Total Count,Failure Rate,Minimum Time Taken,Maximum Time Taken,Average Time Taken
case1,136,7670,1.7731%,3.69,26.583,16.610214623718797
case2,0,4,0.0000%,16.461,26.072,20.065125

Case Id,Group Index,Start Time,End Time,Fail Count,Total Count,Failure Rate,Minimum Time Taken,Maximum Time Taken,Average Time Taken
case1,1,2018-06-18 10:32:00,2018-06-18 11:02:00,30,1938,1.5480%,3.83,26.583,16.469082024050984
case1,2,2018-06-18 11:02:00,2018-06-18 11:32:00,42,2000,2.1000%,3.72,18.932,16.959928979894286
case1,3,2018-06-18 11:32:00,2018-06-18 12:02:00,38,1932,1.9669%,3.69,25.363,16.23456723705196
case1,4,2018-06-18 12:02:00,2018-06-18 12:32:00,26,1798,1.4461%,3.72,20.412,16.72942924743759
case1,5,2018-06-18 12:32:00,2018-06-18 13:02:00,0,2,0.0000%,16.491,16.491,16.491
case2,1,2018-06-18 10:32:00,2018-06-18 11:02:00,0,2,0.0000%,26.072,26.072,26.072
case2,2,2018-06-18 11:02:00,2018-06-18 11:32:00,0,0,0.0000%,,,
case2,3,2018-06-18 11:32:00,2018-06-18 12:02:00,0,2,0.0000%,16.461,16.461,16.461
"""
import datetime
import os
import re

from eztest import utility

try:
    from _collections import OrderedDict
except ImportError:
    from collections import OrderedDict


AVERAGE = 'average'
FAIL_COUNT = 'fail_count'
ID = 'id'
MAX_TIME = 'max_time'
MIN_TIME = 'min_time'
PASS_COUNT = 'pass_count'
START_TIME = 'start_time'
STATUS_PATTERN = re.compile(r'^"\d+","(.+?)",".+?","(Pass|Fail)"')
TIME_PATTERN = re.compile(r'"(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d{6})","(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d{6})","([\d\\.]+)"')
TOTAL_COUNT = 'total_count'


def _add_to_group_summary(summary, case_id, start_time, time_taken=None, is_case_pass=None):
    """Add to group summary.

    :param dict summary: group summary.
    :param str case_id: case id.
    :param datetime.datetime start_time: start datetime.
    :param float time_taken: time taken in second.
    :param bool is_case_pass: is case pass.
    """
    key = '{}_{}'.format(case_id, utility.date2str(start_time, '%Y%m%d%H%M%S'))
    if time_taken is None:
        if key not in summary:
            summary[key] = {ID: case_id,
                            START_TIME: start_time}
    elif key not in summary:
        summary[key] = {ID: case_id,
                        START_TIME: start_time,
                        AVERAGE: time_taken,
                        TOTAL_COUNT: 1,
                        FAIL_COUNT: 0 if is_case_pass else 1,
                        MIN_TIME: time_taken,
                        MAX_TIME: time_taken
                        }
    else:
        summary[key][TOTAL_COUNT] += 1
        if not is_case_pass:
            summary[key][FAIL_COUNT] += 1
        summary[key][AVERAGE] = (summary[key][AVERAGE] + time_taken) / 2.0
        summary[key][MIN_TIME] = min(summary[key][MIN_TIME], time_taken)
        summary[key][MAX_TIME] = max(summary[key][MAX_TIME], time_taken)


def _add_to_case_summary(summary, case_id, time_taken, is_case_pass):
    """Add to case summary.

    :param dict summary: case summary.
    :param str case_id: case id.
    :param float time_taken: time taken in second.
    :param bool is_case_pass: is case pass.
    """
    if case_id not in summary:
        summary[case_id] = {AVERAGE: time_taken,
                            TOTAL_COUNT: 1,
                            FAIL_COUNT: 0 if is_case_pass else 1,
                            MIN_TIME: time_taken,
                            MAX_TIME: time_taken}
    else:
        summary[case_id][TOTAL_COUNT] += 1
        if not is_case_pass:
            summary[case_id][FAIL_COUNT] += 1
        summary[case_id][AVERAGE] = (summary[case_id][AVERAGE] + time_taken) / 2.0
        summary[case_id][MIN_TIME] = min(summary[case_id][MIN_TIME], time_taken)
        summary[case_id][MAX_TIME] = max(summary[case_id][MAX_TIME], time_taken)


def _get_start_time(summary, case_id):
    for key, value in summary.items():
        if key.startswith(case_id + '_'):
            return value.get(START_TIME)
    else:
        return None


def calc(file_paths, group_minutes=60):
    """Analyze report files and calculate failure rate, average of time taken.

    :param list|str file_paths: file paths.
    :param int group_minutes: calculate failure rate and average of time taken by grouping case results with [group_minutes] minutes.
    """
    if not file_paths:
        raise ValueError('Please provide file path.')
    group_gap = datetime.timedelta(seconds=group_minutes * 60)
    if not isinstance(file_paths, list):
        file_paths = [file_paths]
    file_list = []
    for file_path in file_paths:
        if os.path.isfile(file_path):
            file_list.append(file_path)
        elif os.path.isdir(file_path):
            file_list.extend([os.path.join(file_path, f) for f in os.listdir(file_path) if os.path.isfile(os.path.join(file_path, f))])
        else:
            print('Error: cannot find {}.'.format(file_path))

    group_summary = OrderedDict()
    case_summary = dict()
    for file_path in file_list:
        print('Calculating for {}...'.format(file_path))
        start_times, case_id, is_pass = dict(), None, None
        try:
            with open(file_path, 'r') as f:
                line = f.readline()
                if not line or not line.startswith('"Repeat Index","Id","Description","Status"'):
                    print('Not report file, ignore file: {}'.format(file_path))
                    continue
                while True:
                    line = f.readline()
                    if not line:
                        break
                    status_match = STATUS_PATTERN.match(line)
                    time_match = TIME_PATTERN.search(line)
                    if status_match:
                        case_id = status_match.group(1)
                        is_pass = True if status_match.group(2) == 'Pass' else False

                    if time_match:
                        start_date, end_date = utility.str2date(time_match.group(1)), utility.str2date(time_match.group(2))
                        time_taken = float(time_match.group(3))
                        _add_to_case_summary(case_summary, case_id, time_taken, is_pass)

                        if case_id not in start_times:
                            exited_start_time = _get_start_time(group_summary, case_id)
                            if exited_start_time:
                                start_times[case_id] = exited_start_time
                            else:
                                start_times[case_id] = start_date.replace(second=0, microsecond=0)
                        my_start_time = start_times[case_id]

                        if my_start_time + group_gap >= end_date:
                            _add_to_group_summary(group_summary, case_id, my_start_time, time_taken, is_pass)
                        else:
                            while True:
                                my_start_time += group_gap
                                start_times[case_id] = my_start_time
                                if my_start_time + group_gap < end_date:
                                    _add_to_group_summary(group_summary, case_id, my_start_time)
                                else:
                                    break
                            _add_to_group_summary(group_summary, case_id, my_start_time, time_taken, is_pass)
        except Exception:
            print('Not report file, ignore file: {}'.format(file_path))

    if not group_summary:
        print('No report result found.')
    else:
        print(os.linesep)
        print('Case Id,Fail Count,Total Count,Failure Rate,Minimum Time Taken,Maximum Time Taken,Average Time Taken')
        groups = []
        for case_id, value in case_summary.items():
            print('{},{},{},{},{},{},{}'.format(
                case_id,
                value[FAIL_COUNT],
                value[TOTAL_COUNT],
                '{:.4f}%'.format(value[FAIL_COUNT]/(1 if value[TOTAL_COUNT] == 0 else value[TOTAL_COUNT]) * 100),
                value[MIN_TIME],
                value[MAX_TIME],
                value[AVERAGE]
            ))
            index = 1
            for key, group_value in group_summary.items():
                if key.startswith(case_id):
                    groups.append('{},{},{},{},{},{},{},{},{},{}'.format(
                        case_id,
                        index,
                        utility.date2str(group_value[START_TIME], '%Y-%m-%d %H:%M:%S'),
                        utility.date2str(group_value[START_TIME] + group_gap, '%Y-%m-%d %H:%M:%S'),
                        group_value.get(FAIL_COUNT, 0),
                        group_value.get(TOTAL_COUNT, 0),
                        '{:.4f}%'.format(group_value[FAIL_COUNT] / (1 if group_value[TOTAL_COUNT] == 0 else group_value[TOTAL_COUNT]) * 100
                                         if FAIL_COUNT in group_value else 0),
                        group_value.get(MIN_TIME, ""),
                        group_value.get(MAX_TIME, ""),
                        group_value.get(AVERAGE, "")
                    ))
                    index += 1
        print(os.linesep)
        print('Case Id,Group Index,Start Time,End Time,Fail Count,Total Count,Failure Rate,Minimum Time Taken,Maximum Time Taken,Average Time Taken')
        for group in groups:
            print(group)
