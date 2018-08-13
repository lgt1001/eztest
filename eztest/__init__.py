"""eztest - A Python package and execution used for performance/load testing.

Copyright (C) 2014 lgt, version 1.0 by lgt
* https://github.com/lgt1001/eztest
"""
import argparse
import datetime
import importlib
import inspect
import os
import re
import socket
import sys
import traceback

import psutil

from . import calc_report, ini, mail, report, testcase, testmode, utility

__version__ = '2.0.2'
module_name = 'eztest'
version = '{} v{}'.format(module_name, __version__)
__all__ = ['calc_report', 'ini', 'report', 'stringbuilder', 'testcase', 'utility']


class CaseType(object):
    """Case types."""
    ClassCase = 0
    FunctionCase = 1
    UnittestCase = 2


def _is_matched(name, match_parts=None, ignore_match_parts=None):
    """Is class/case matched.

    :param str name: class/case name.
    :param list match_parts: pattern for classes/cases to be collected.
    :param list ignore_match_parts: pattern for classes/cases to be ignored.
    :return bool: Whether class/case is matched.
    """
    is_matched = False
    if match_parts is not None:
        for match_part in match_parts:
            if match_part.find('*') >= 0:
                match_pattern = match_part.replace('*', '.+?')
                if re.match(match_pattern, name, flags=re.IGNORECASE):
                    is_matched = True
                    break
            else:
                if utility.compare_str(match_part, name, True) == 0:
                    is_matched = True
                    break
    else:
        is_matched = True
    if is_matched and ignore_match_parts is not None:
        for match_part in ignore_match_parts:
            if match_part.find('*') >= 0:
                match_pattern = match_part.replace('*', '.+?')
                if re.match(match_pattern, name, flags=re.IGNORECASE):
                    is_matched = False
                    break
            else:
                if utility.compare_str(match_part, name, True) == 0:
                    is_matched = False
                    break
    return is_matched


def _load_class_cases(module_obj, match_parts=None, ignore_match_parts=None):
    """Load cases from module.

    :param module_obj: module object.
    :param list match_parts: pattern for cases to be collected.
    :param list ignore_match_parts: pattern for cases to be ignored.
    :return dict: a dictionary of "type", "setup_module", "teardown_module", "cases".
    """
    result = dict(type=CaseType.ClassCase)
    if hasattr(module_obj, 'setup_module'):
        result['setup_module'] = module_obj.setup_module
    if hasattr(module_obj, 'teardown_module'):
        result['teardown_module'] = module_obj.teardown_module
    cases = module_obj.CASES
    result['cases'] = [c for c in cases if _is_matched(c.id, match_parts, ignore_match_parts)]
    return result


def _load_test_cases(funcs, match_parts=None, ignore_match_parts=None, is_unittest=False):
    """Load cases from functions.

    :param list funcs: a list of functions.
    :param list match_parts: pattern for cases to be collected.
    :param list ignore_match_parts: pattern for cases to be ignored.
    :param bool is_unittest: Whether functions are unittest.TestCase.
    :return dict: a dictionary of "type", "setup_module", "teardown_module", "setup_function", "teardown_function", "cases".
    """
    result = dict(type=CaseType.UnittestCase if is_unittest else CaseType.FunctionCase)
    cases = []
    for func in funcs:
        func_name = func[0]
        func_attr = func[1]
        if func_name.startswith('_'):
            continue
        func_name_upper = func_name.upper()
        if func_name_upper in ['SETUP_MODULE', 'SETUPCLASS']:
            result['setup_module'] = func_attr
        elif func_name_upper in ['TEARDOWN_MODULE', 'TEARDOWNCLASS']:
            result['teardown_module'] = func_attr
        elif func_name_upper in ['SETUP_FUNCTION', 'SETUP']:
            result['setup_function'] = func_attr
        elif func_name_upper in ['TEARDOWN_FUNCTION', 'TEARDOWN']:
            result['teardown_function'] = func_attr
        elif func_name_upper.startswith('TEST_'):
            if _is_matched(func_name, match_parts, ignore_match_parts):
                cases.append(func_attr)
    result['cases'] = cases
    return result


def _load_cases(target, case_matches=None, ignore_match_parts=None, class_matches=None, ignore_class_matches=None):
    """Load cases from target.

    :param str target: Target can be file path, or module name.
    :param list case_matches: pattern for cases to be collected.
    :param list ignore_match_parts: pattern for cases to be ignored.
    :param class_matches: pattern for classes to be collected.
    :param ignore_class_matches: pattern for classes to be ignored.
    :return list: a list of dictionary which contains "module_name", "type", "setup_module", "teardown_module",
        "setup_function", "teardown_function", "cases".
    """
    if os.path.isfile(target):
        t = utility.import_module(target)
    elif os.path.isdir(target):
        target = target.rstrip('/\\')
        dir_name = os.path.dirname(target)
        if not os.path.isabs(dir_name):
            dir_name = os.path.normpath(os.path.join(os.getcwd(), dir_name))
        sys.path.append(dir_name)
        t = importlib.import_module(os.path.basename(target))
    else:
        m_name = re.sub(r'[/\\]', '.', target).strip('.')
        try:
            t = importlib.import_module(m_name)
        except(SystemError, ImportError):
            sys.path.append(os.getcwd())
            t = importlib.import_module(m_name)

    results = []
    if hasattr(t, 'CASES'):
        result = _load_class_cases(t, case_matches, ignore_match_parts)
        result['module_name'] = t.__name__
        results.append(result)
    else:
        funcs = inspect.getmembers(t, predicate=inspect.isfunction)
        result = _load_test_cases(funcs, case_matches, ignore_match_parts, False)
        result['module_name'] = t.__name__
        results.append(result)
        classes = inspect.getmembers(t, predicate=inspect.isclass)
        for classobj in classes:
            class_name = classobj[0]
            if _is_matched(class_name, class_matches, ignore_class_matches):
                obj = getattr(t, class_name)()
                funcs = inspect.getmembers(obj, predicate=inspect.ismethod)
                result = _load_test_cases(funcs, case_matches, ignore_match_parts, True)
                result['module_name'] = '%s:%s' % (t.__name__, class_name)
                results.append(result)
    return results


def _get_report_server(report_server):
    host_port = report_server.split(':')
    if len(host_port) > 1:
        host, port = host_port[0], int(host_port[1])
    else:
        host, port = report_server, 8765
    return host, port


def _get_test_mode(mode):
    """Get test mode from command line.

    :param str mode: mode.
    :return: test mode.
    """
    test_mode = testmode.NORMAL
    mode = mode.upper()
    if mode in ['1', 'CONTINUOUS']:
        test_mode = testmode.CONTINUOUS
    elif mode in ['2', 'SIMULTANEOUS']:
        test_mode = testmode.SIMULTANEOUS
    elif mode in ['3', 'CONCURRENCY']:
        test_mode = testmode.CONCURRENCY
    elif mode in ['4', 'FREQUENT']:
        test_mode = testmode.FREQUENT
    return test_mode


def _get_mail_configuration(mail_config):
    """Get mail configuration.

    :param str mail_config: mail configuration file path in command line.
    :return mail.Mail: mail object.
    """
    if mail_config is not None:
        _ini = ini.INI(mail_config)
        if _ini.contains('SMTP'):
            mal = mail.Mail()
            _ini.get('SMTP').to_object(mal)
            return mal


def dump(args):
    """Dump data from report server."""
    print('Dumping from report server: {} ...'.format(args.report_server))
    s = None
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.sendto(b'dump', _get_report_server(args.report_server))
        data, _ = s.recvfrom(65535)
        print(data.decode('utf-8'))
    except ConnectionError:
        print('ConnectionError: unable to connect to {}'.format(args.report_server))
    except Exception as e:
        print('{}: {}'.format(type(e).__name__, str(e)))
    finally:
        if s:
            s.close()


def calc(args):
    """Calculate by grouping case results with [group-minutes] minutes."""
    calc_report.calc(args.path, group_minutes=args.group_minutes)


def test(args):
    """Start eztest for target cases, classes, modules."""
    mode = _get_test_mode(args.mode)
    mal = _get_mail_configuration(args.mail_config)
    results = _load_cases(args.target,
                          case_matches=args.cases,
                          ignore_match_parts=args.not_cases,
                          class_matches=args.classes,
                          ignore_class_matches=args.not_classes)
    for result in results:
        cases = result.get('cases')
        if not cases:
            continue
        if result.get('type') == CaseType.ClassCase:
            for c in cases:
                c.no_log = args.nolog
                if args.report_folder:
                    c.log_folder = args.report_folder
            n_cases = cases
        else:
            from ._funccase import BuildCase
            n_cases = []
            for c in cases:
                bc = BuildCase()
                bc.id = '{}:{}'.format(result.get('module_name'), c.__name__)
                bc.description = bc.id
                bc.no_log = args.nolog
                if args.report_folder:
                    c.log_folder = args.report_folder
                if 'setup_function' in result:
                    bc.initialize = result.get('setup_function')
                if 'teardown_function' in result:
                    bc.dispose = result.get('teardown_function')
                bc.run = c
                n_cases.append(bc)
        if mode == testmode.NORMAL:
            nt = testmode.NormalTest()
        elif mode == testmode.CONTINUOUS:
            nt = testmode.ContinuousTest()
            nt.repeat_times = args.repeat
            nt.interval_seconds = args.interval
        elif mode == testmode.SIMULTANEOUS:
            nt = testmode.SimultaneousTest()
            nt.thread_count = args.stress
            nt.repeat_times = args.repeat
            nt.interval_seconds = args.interval
        elif mode == testmode.CONCURRENCY:
            nt = testmode.ConcurrencyTest()
            nt.thread_count = args.stress
            nt.interval_seconds = args.interval
        else:
            nt = testmode.FrequentTest()
            nt.thread_count = args.stress
            nt.max_thread_count = args.limit
            nt.interval_seconds = args.interval
        nt.starts_time = args.starts
        if args.ends:
            nt.ends_time = args.ends
        elif args.duration is not None and args.duration > 0:
            dtnow = datetime.datetime.now()
            nt.ends_time = (args.starts if args.starts and args.starts > dtnow else dtnow) + datetime.timedelta(minutes=args.duration)
        nt.no_report = args.noreport
        if args.report_folder:
            nt.report_folder = args.report_folder
        if args.report_server:
            nt.report_server = _get_report_server(args.report_server)
        nt.mail = mal
        if 'setup_module' in result:
            nt.setup = result.get('setup_module')
        if 'teardown_module' in result:
            nt.teardown = result.get('teardown_module')
        nt.cases = n_cases
        nt.run()
        if mode == testmode.NORMAL:
            print('*' * 80)
            print('Summary of %s:' % result.get('module_name'))
            for c in n_cases:
                print('%s\t%s' % (c.id, 'Pass' if c.status else 'Fail'))
            print('*' * 80)


def stop(args):
    """Stop eztest and its report server."""
    processes = []
    for pr in psutil.process_iter():
        try:
            cmd = ' '.join(pr.cmdline())
        except psutil.AccessDenied:
            continue
        if 'eztest' in cmd and 'stop' not in cmd:
            processes.append(pr)

    if processes:
        print('Stopping eztest processes ...')
        for pr in processes:
            pr.kill()
    else:
        print('No eztest process found.')


def start_server(args):
    """Start report server."""
    print('Starting eztest report server ...')
    report.start_udp_report_server(args.port, args.handler, args.group_minutes)


def stop_server(args):
    """Stop report server."""
    for pr in psutil.process_iter():
        try:
            cmd = ' '.join(pr.cmdline())
        except psutil.AccessDenied:
            continue
        if 'eztest' in cmd and 'server' in cmd and 'start' in cmd:
            print('Stopping eztest report server ...')
            pr.kill()
            break
    else:
        print('No eztest report server process found.')


def _to_datetime(date_string):
    """Convert datetime string to datetime object.

    :param str date_string: datetime string.
    :return datetime.datetime: datetime object.
    """
    try:
        return datetime.datetime.strptime(date_string, '%Y-%m-%d %H:%M:%S')
    except ValueError:
        raise argparse.ArgumentTypeError('Input "{}" is not datetime format(year-month-day hour:minute:second).'.format(date_string))


def _define_parser():
    parser = argparse.ArgumentParser(prog=module_name, description=module_name)
    parser.add_argument('--version', '-v', action='version', version=__version__)

    sub_parsers = parser.add_subparsers(dest='eztest')
    test_parser = sub_parsers.add_parser('test', help='Start eztest for target cases, classes, modules.')
    case_group = test_parser.add_argument_group('Case Group', 'Define arguments of case related.')
    case_group.add_argument('--target', '-t', required=True,
                            help='Folder or file path, or a module, a __init__.py file is required under that folder/module.')
    case_group.add_argument('--classes', '-cl', nargs='+',
                            help='Class names to be tested. It will be considered if target is file.')
    case_group.add_argument('--not-classes', '-ncl', nargs='+',
                            help='Class names to be ignored. It will be considered if target is file.')
    case_group.add_argument('--cases', '-c', nargs='+',
                            help='''Case names to be tested. It can be whole case name or part of them(e.g.: "*a", "a*", "*a*").''')
    case_group.add_argument('--not-cases', '-nc', nargs='+',
                            help='''Case names to be ignored. It can be whole case name or part of them(e.g.: "*a", "a*", "*a*").''')

    test_group = test_parser.add_argument_group('Test Mode Group', 'Define arguments of test mode related.')
    test_group.add_argument('--mode', '-m', default='normal',
                            choices=['0', '1', '2', '3', '4', 'normal', 'continuous', 'simultaneous', 'concurrency', 'frequent'],
                            help='''(a)0 or normal: Run selected cases only once. 
    (b)1 or continuous: Run cases [repeat] times with [interval] seconds' sleeping. 
    (c)2 or simultaneous: Start [stress] threads and run cases in each thread, sleep [interval] seconds after all cases are finished, and then start testing again with [repeat] times. 
    (d)3 or concurrency: Start [stress] threads and each thread will continuously run cases with [interval] seconds' sleeping. 
    (e)4 or frequent: Start [stress] threads per [interval] seconds. And only can have [limit] available threads running.''')
    test_group.add_argument('--stress', '-s', type=int, default=1,
                            help='Start [stress] threads in each round of testing. Default value is 1.')
    test_group.add_argument('--repeat', '-r', type=int, default=1,
                            help='Repeat [repeat] times of testing. Default value is 1')
    test_group.add_argument('--interval', '-i', type=int, default=0,
                            help='Sleep [interval] seconds after one round of testing. Default value is 0.')
    test_group.add_argument('--limit', '-l', type=int, default=0,
                            help='Only can have [limit] count of running threads. No limitation if this is less than or equals to [stress].')
    test_group.add_argument('--starts', '-st', type=_to_datetime,
                            help='''Testing will be started at [starts]. It is datetime string(e.g.: "2014-01-02 03:04:05").''')
    test_group.add_argument('--duration', '-d', type=int,
                            help='''Testing will continue with [duration] minutes. Will be ignored if 'ends' is provided.''')
    test_group.add_argument('--ends', '-et', type=_to_datetime,
                            help='''Testing will be stopped at [ends]. It is datetime string(e.g.: "2014-01-02 03:04:05").''')

    log_group = test_parser.add_argument_group('Report/Log Group', 'Define arguments of report or log related.')
    log_group.add_argument('--report-folder', '-rf',
                           help='Report and log files will be saved under [report-folder].')
    log_group.add_argument('--report-server', '-rs',
                           help='Report server. The format is "host_name:port_number" or "host_name" with default port number 8765.')
    log_group.add_argument('--noreport', '-nr', action='store_true',
                           help='No report file will be generated if [noreport] is clarified.')
    log_group.add_argument('--nolog', '-nl', action='store_true',
                           help='No log file will be generated if [nolog] is clarified.')
    log_group.add_argument('--mail-config', '-mc',
                           help='''Mail configuration file which contains mail server information etc. 
    It should be INI format file(http://en.wikipedia.org/wiki/INI_file). 
    Will send report by mail only if mail-config is provided and report file is generated. 
    Section is "SMTP" and properties can be "server", "from_mail", "to_mails", "cc_mails", "bcc_mails", "username", "password", "need_authentication" and "subject". 
    "server", "from_mail" and "to_mails" are mandatory. 
    "to_mails", "cc_mails" and "bcc_mails" can be multiple values separated by comma. 
    "need_authentication" is boolean, "username" and "password" are required if "need_authentication" is True.''')

    test_parser.set_defaults(func=test)

    stoptest_parser = sub_parsers.add_parser('stop', help='Stop eztest and its report server.')
    stoptest_parser.set_defaults(func=stop)

    group_minutes_argument = argparse.ArgumentParser(add_help=False)
    group_minutes_argument.add_argument('--group-minutes', '-gm', type=int, default=60,
                                        help='Calculate by grouping case results with [group-minutes] minutes. Default is 60 minutes.')
    port_handler_argument = argparse.ArgumentParser(add_help=False)
    port_handler_argument.add_argument('--port', '-p', type=int, default=8765, help='Port number.')
    port_handler_argument.add_argument('--handler', '-hl',
                                       help='Custom handler. The format is: "file_path:handler_class_name", or "module_name:handler_class_name".')

    calc_parser = sub_parsers.add_parser('calc', help='Calculate report files generated by eztest.', parents=[group_minutes_argument])
    calc_parser.add_argument('--path', '-p', required=True, nargs='+',
                             help='Report folders or files to be calculated.')
    calc_parser.set_defaults(func=calc)

    report_parser = sub_parsers.add_parser('server', help='Start|Stop|Restart report server.')
    report_sub = report_parser.add_subparsers(dest='server')

    start_parser = report_sub.add_parser('start', parents=[port_handler_argument, group_minutes_argument])
    start_parser.set_defaults(func=start_server)

    stop_parser = report_sub.add_parser('stop')
    stop_parser.set_defaults(func=stop_server)

    dump_parser = sub_parsers.add_parser('dump', help='Dump data from report server.')
    dump_parser.add_argument('--report-server', '-rs', default='localhost:8765',
                             help='Report server. The format is "host_name:port_number" or "host_name" with default port number 8765.')
    dump_parser.set_defaults(func=dump)

    return parser, report_parser


def _parser_args(args=None):
    """Parse arguments.

    :param list args: arguments.
    """
    parser, report_parser = _define_parser()
    args = args or sys.argv
    all_args = parser.parse_args(args[1:])
    if all_args.eztest is None:
        parser.print_help()
        sys.exit(2)
    elif all_args.eztest == 'server' and all_args.server is None:
        report_parser.print_help()
        sys.exit(2)
    else:
        all_args.func(all_args)


def main(args=None):
    """Main function. Load arguments, cases from target, build test mode and start testing."""
    try:
        _parser_args(args)
    except Exception:
        traceback.print_exc()
        sys.exit(2)


if __name__ == '__main__':
    main()