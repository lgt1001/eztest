"""eztest - A python package to do load test

Copyright (C) 2014 lgt, version 1.0 by lgt
* https://github.com/lgt1001/eztest
"""
import datetime
import enum
import importlib
import inspect
import os
import re
import sys
import traceback

from . import ini, mail, testcase, testmode, utility

__version__ = "1.0.2"
module_name = "eztest"
version = "{} v{}".format(module_name, __version__)
__all__ = ["ini", "stringbuilder", "testcase", "utility"]


_version_info = sys.version_info
_is_option_parser = False
if _version_info < (2, 7) or (3, 0) <= _version_info < (3, 2):
    import optparse

    _is_option_parser = True
else:
    import argparse


class CaseType(enum.Enum):
    """Case types."""
    ClassCase = 0
    FunctionCase = 1
    UnittestCase = 2


def _load_mail_section(section):
    """Load mail section in INI file.

    :param ini.Section section: section.
    :return mail.Mail: mail object.
    """
    mal = mail.Mail()
    section.convert2obj(mal)
    return mal


def _to_datetime(date_string):
    """Convert datetime string to datetime object.

    :param str date_string: datetime string.
    :return datetime.datetime: datetime object.
    """
    return datetime.datetime.strptime(date_string, "%Y-%m-%d %H:%M:%S")


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
    :return dict: a dictionary of 'type', 'setup_module', 'teardown_module', 'cases'.
    """
    result = dict(type=CaseType.ClassCase)
    if hasattr(module_obj, "setup_module"):
        result['setup_module'] = module_obj.setup_module
    if hasattr(module_obj, "teardown_module"):
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
    :return dict: a dictionary of 'type', 'setup_module', 'teardown_module', 'setup_function', 'teardown_function', 'cases'.
    """
    result = dict(type=CaseType.UnittestCase if is_unittest else CaseType.FunctionCase)
    cases = []
    for func in funcs:
        func_name = func[0]
        func_attr = func[1]
        if func_name.startswith("_"):
            continue
        func_name_upper = func_name.upper()
        if func_name_upper in ["SETUP_MODULE", "SETUPCLASS"]:
            result['setup_module'] = func_attr
        elif func_name_upper in ["TEARDOWN_MODULE", "TEARDOWNCLASS"]:
            result['teardown_module'] = func_attr
        elif func_name_upper in ["SETUP_FUNCTION", "SETUP"]:
            result['setup_function'] = func_attr
        elif func_name_upper in ["TEARDOWN_FUNCTION", "TEARDOWN"]:
            result['teardown_function'] = func_attr
        elif func_name_upper.startswith("TEST_"):
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
    :return list: a list of dictionary which contians 'module_name', 'type', 'setup_module', 'teardown_module',
        'setup_function', 'teardown_function', 'cases'.
    """
    if os.path.isfile(target):
        t = utility.import_module(target)
    elif os.path.isdir(target):
        target = target.rstrip('/\\')
        dirname = os.path.dirname(target)
        if not os.path.isabs(dirname):
            dirname = os.path.normpath(os.path.join(os.getcwd(), dirname))
        sys.path.append(dirname)
        t = importlib.import_module(os.path.basename(target))
    else:
        m_name = re.sub(r'[/\\]', ".", target).strip('.')
        try:
            t = importlib.import_module(m_name)
        except(SystemError, ImportError):
            sys.path.append(os.getcwd())
            t = importlib.import_module(m_name)

    results = []
    if hasattr(t, "CASES"):
        result = _load_class_cases(t, case_matches, ignore_match_parts)
        result["module_name"] = target
        results.append(result)
    else:
        funcs = inspect.getmembers(t, predicate=inspect.isfunction)
        result = _load_test_cases(funcs, case_matches, ignore_match_parts, False)
        result["module_name"] = target
        results.append(result)
        classes = inspect.getmembers(t, predicate=inspect.isclass)
        for classobj in classes:
            class_name = classobj[0]
            if _is_matched(class_name, class_matches, ignore_class_matches):
                obj = getattr(t, class_name)()
                funcs = inspect.getmembers(obj, predicate=inspect.ismethod)
                result = _load_test_cases(funcs, case_matches, ignore_match_parts, True)
                result["module_name"] = "%s:%s" % (target, class_name)
                results.append(result)
    return results


def _add_argument(group, long_option, short_option, required=False, **kwargs):
    """Add argument.

    :param group: argument group.
    :param str long_option: long option.
    :param str short_option: short option
    :param bool required: is argument required.
    :param kwargs: additional parameters.
    """
    if _is_option_parser and long_option != "--version":
        if "type" in kwargs and kwargs["type"] is _to_datetime:
            del kwargs["type"]
        group.add_option(long_option, **kwargs)
    else:
        group.add_argument(long_option, short_option, required=required, **kwargs)


def _add_argument_group(parser, title, description=None):
    """Add argument group.

    :param parser: argument parser.
    :param str title: title
    :param str description: description
    :return: argument group.
    """
    if _is_option_parser:
        group = optparse.OptionGroup(parser, title, description)
        parser.add_option_group(group)
    else:
        group = parser.add_argument_group(title, description)
    return group


def _parser_args(args=None):
    """Parse arguments.

    :param list args: arguments.
    :return tuple: (values : Values, args : [string])
    """
    if _is_option_parser:
        parser = optparse.OptionParser(prog=module_name, description=module_name, version=__version__)
    else:
        parser = argparse.ArgumentParser(prog=module_name, description=module_name)

    case_group = _add_argument_group(parser, "Case Group", "Define arguments of case related.")
    _add_argument(case_group, long_option="--target", short_option="-t", required=True, dest="target",
                  help="Folder or file path, or a module, a __init__.py file is required under that folder/module.")
    _add_argument(case_group, long_option="--classes", short_option="-cl", dest="classes", nargs="+",
                  help="Class names to be tested. It will be considered if target is file.")
    _add_argument(case_group, long_option="--not-classes", short_option="-ncl", dest="not_classes", nargs="+",
                  help="Class names to be ignored. It will be considered if target is file.")
    _add_argument(case_group, long_option="--cases", short_option="-c", dest="cases", nargs="+",
                  help="""Case names to be tested. It can be whole case name or part of them(e.g.: "*a", "a*", "*a*").""")
    _add_argument(case_group, long_option="--not-cases", short_option="-nc", dest="not_cases", nargs="+",
                  help="""Case names to be ignored. It can be whole case name or part of them(e.g.: "*a", "a*", "*a*").""")

    test_group = _add_argument_group(parser, "Test Mode Group", "Define arguments of test mode related.")
    _add_argument(test_group, long_option="--mode", short_option="-m", dest="mode", default="normal",
                  choices=['0', '1', '2', '3', '4', "normal", "continuous", "simultaneous", "concurrency", "frequent"],
                  help="""(a)0 or normal: Run selected cases only once. 
(b)1 or continuous: Run cases [repeat] times with [interval] seconds' sleeping. 
(c)2 or simultaneous: Start [stress] threads and run cases in each thread, sleep [interval] seconds after all cases are finished, and then start testing again with [repeat] times. 
(d)3 or concurrency: Start [stress] threads and each thread will continuously run cases with [interval] seconds' sleeping. 
(e)4 or frequent: Start [stress] threads per [interval] seconds and do this [repeat] times. And only can have [limit] available threads running.""")
    _add_argument(test_group, long_option="--stress", short_option="-s", dest="stress", type=int, default=1,
                  help="Start [stress] threads in each round of testing. Default value is 1.")
    _add_argument(test_group, long_option="--repeat", short_option="-r", dest="repeat", type=int, default=1,
                  help="Repeat [repeat] times of testing. Default value is 1")
    _add_argument(test_group, long_option="--interval", short_option="-i", dest="interval", type=int, default=0,
                  help="Sleep [interval] seconds after one round of testing. Default value is 0.")
    _add_argument(test_group, long_option="--limit", short_option="-l", dest="limit", type=int, default=0,
                  help="Only can have [limit] count of running threads. No limitation if this is less than or equals to \"stress\".")
    _add_argument(test_group, long_option="--starts", short_option="-st", dest="starts", type=_to_datetime,
                  help="""Testing will be started at [starts]. It is datetime string(e.g.: "2014-01-02 03:04:05").""")
    _add_argument(test_group, long_option="--duration", short_option="-d", dest="duration", type=int,
                  help="""Testing will continue with [duration] minutes. Will be ignored if "ends" is provided.""")
    _add_argument(test_group, long_option="--ends", short_option="-et", dest="ends", type=_to_datetime,
                  help="""Testing will be stopped at [ends]. It is datetime string(e.g.: "2014-01-02 03:04:05").""")

    log_group = _add_argument_group(parser, "Report/Log Group", "Define arguments of report or log related.")
    _add_argument(log_group, long_option="--mail-config", short_option="-mc", dest="mail_config",
                  help="""Mail configuration file which contains mail server information etc. 
It should be INI format file(http://en.wikipedia.org/wiki/INI_file). 
Will send report by mail only if mail-config is provided and report file is generated. 
Section is "SMTP" and properties can be "server", "from_mail", "to_mails", "cc_mails", "bcc_mails", "username", "password", "need_authentication" and "subject". 
"server", "from_mail" and "to_mails" are mandatory. 
"to_mails", "cc_mails" and "bcc_mails" can be multiple values separated by comma. 
"need_authentication" is boolean, "username" and "password" are required if "need_authentication" is True.""")
    _add_argument(log_group, long_option="--report-folder", short_option="-rf", dest="report_folder",
                  help="Report and log files will be saved under [report-folder].")
    _add_argument(log_group, long_option="--noreport", short_option="-nr", dest="no_report", action='store_true',
                  help="No report file will be generated if [noreport] is clarified.")
    _add_argument(log_group, long_option="--nolog", short_option="-nl", dest="no_log", action='store_true',
                  help="No log file will be generated if [nolog] is clarified.")

    if args is None:
        args = sys.argv
    if _is_option_parser:
        (options, args) = parser.parse_args(args)
        if not options.target:
            parser.error('target is not given.')
        if options.starts is not None:
            options.starts = _to_datetime(options.starts)
        if options.ends is not None:
            options.ends = _to_datetime(options.ends)
        return options
    else:
        parser.add_argument("--version", "-v", action='version', version=__version__)
        return parser.parse_args(args[1:])


def main(args=None):
    """Main function. Load arguments, cases from target, build test mode and start testing."""
    try:
        args = _parser_args(args)
        mode = testmode.NORMAL
        args.mode = args.mode.upper()
        if args.mode in ['1', 'CONTINUOUS']:
            mode = testmode.CONTINUOUS
        elif args.mode in ['2', 'SIMULTANEOUS']:
            mode = testmode.SIMULTANEOUS
        elif args.mode in ['3', 'CONCURRENCY']:
            mode = testmode.CONCURRENCY
        elif args.mode in ['4', 'FREQUENT']:
            mode = testmode.FREQUENT
        mal = None
        if args.mail_config is not None:
            _ini = ini.INI(args.mail_config)
            if _ini.contains("SMTP"):
                mal = _load_mail_section(_ini.get("SMTP"))
        results = _load_cases(args.target, case_matches=args.cases, ignore_match_parts=args.not_cases,
                              class_matches=args.classes, ignore_class_matches=args.not_classes)
        for result in results:
            cases = result.get("cases")
            if not cases:
                continue
            if result.get("type") == CaseType.ClassCase:
                for c in cases:
                    c.no_log = args.no_log
                    if args.report_folder:
                        c.log_folder = args.report_folder
                n_cases = cases
            else:
                from ._funccase import BuildCase
                n_cases = []
                for c in cases:
                    bc = BuildCase()
                    bc.id = c.__name__
                    bc.description = "{} in {}".format(bc.id, result.get('module_name'))
                    bc.no_log = args.no_log
                    if args.report_folder:
                        c.log_folder = args.report_folder
                    if "setup_function" in result:
                        bc.initialize = result.get("setup_function")
                    if "teardown_function" in result:
                        bc.dispose = result.get("teardown_function")
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
            nt.no_report = args.no_report
            if args.report_folder:
                nt.report_folder = args.report_folder
            nt.mail = mal
            if "setup_module" in result:
                nt.setup = result.get("setup_module")
            if "teardown_module" in result:
                nt.teardown = result.get("teardown_module")
            nt.cases = n_cases
            nt.run()
            if mode == testmode.NORMAL:
                print("*" * 80)
                print("Summary of %s:" % result.get("module_name"))
                for c in n_cases:
                    print("%s\t%s" % (c.id, "Pass" if c.status else "Fail"))
                print("*" * 80)
    except Exception:
        traceback.print_exc()
        sys.exit(2)


if __name__ == "__main__":
    sys.exit(main())
