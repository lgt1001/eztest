import copy
import datetime
import json
import os
import re
import sys

from io import StringIO


DATE_MAPPING = {
    r'^(\d+)-(\d+)-(\d+)': [1, 2, 3],                           # yyyy-m-d          1996-4-22
    r'^(\d+)/(\d+)/(\d{4})': [3, 2, 1],                         # d/m/yyyy          22/4/1996
    r'^(\d{4})/(\d+)/(\d+)': [1, 2, 3],                         # yyyy/m/d
    r'^(\d{4}) ([a-zA-Z]+) (\d+)': [1, 2, 3],                   # yyyy mmmm d       1996 April 22
    r'^(\d+) ([a-zA-Z]+) (\d{4})': [3, 2, 1],                   # d mmmm yyyy       22 April 1996
    r'^([a-zA-Z]+, )?([a-zA-Z]+) (\d+),? (\d{4})': [4, 2, 3],   # mmmm d, yyyy      April 22, 1996  Thursday, April 10, 2008
    r'^(\d+)\. ?(\d+|[a-zA-Z]+)\.? ?(\d{4})': [3, 2, 1],        # dd.mm.yyyy|d. month yyyy
    r'^(\d{4})\.(\d+)\.(\d+)': [1, 2, 3],                       # yyyy.m.d
}
MONTHS = ['jan', 'feb', 'mar', 'apr', 'may', 'jun', 'jul', 'aug', 'sep', 'oct', 'nov', 'dec']


def date2str(date_time, date_format='%Y-%m-%d %H:%M:%S.%f', only_millisecond=False):
    """Convert datetime to string.

    :param datetime.datetime date_time : datetime.
    :param str date_format : date format string.
    :param bool only_millisecond : only need milliseconds in datetime string.
    :return str: datetime string.
    """
    if date_time is None:
        return ''
    if isinstance(date_time, datetime.datetime):
        dtstr = date_time.strftime(date_format)
        if only_millisecond:
            return dtstr[:-3]
        else:
            return dtstr
    elif isinstance(date_time, str):
        return date_time
    else:
        return str(date_time)


def str2date(date_time_str, date_format=None):
    """Convert string to datetime.
    Format of date part:
    yyyy-m-d            1996-4-22
    d/m/yyyy            22/4/1996
    yyyy/m/d            1996/4/22
    yyyy mmmm d         1996 April 22   or  1996 Apr 22
    d mmmm yyyy         22 April 1996   or  22 Apr 1996
    mmmm d, yyyy        April 22, 1996 or Monday, April 22, 1996    or  Apr 22, 1996
    dd.mm.yyyy          22.04.1996
    d. month yyyy       4. April 1996   or  4. Apr 1996
    yyyy.m.d            1996.4.22

    Format of time part:
    HH:MM
    HH:MM:SS
    HH:MM AM or HH:MM PM
    HH:MM:SS.FFF
    HH:MM:SS.FFFFFF
    HH:MM:SSZ
    HH:MM:SS UTC
    HH:MM:SS+00:00
    HH:MM:SS+0000
    :param str date_time_str: datetime string.
    :param str date_format: date format string.
    :return datetime.datetime: datetime.
    """
    if date_format:
        return datetime.datetime.strptime(date_time_str, date_format)

    year, month, day = None, None, None
    hour, minute, second, microsecond = 0, 0, 0, 0
    for pattern, groups in DATE_MAPPING.items():
        g = re.match(pattern, date_time_str)
        if g:
            year, month, day = map(g.group, groups)
            break
    if not year or not month or not day:
        raise ValueError('Invalid date string, cannot convert to datetime.')
    if not month.isdigit():
        month = next(index+1 for index, m in enumerate(MONTHS) if month.lower().startswith(m))
    else:
        month = int(month)
    year, day = int(year), int(day)

    g = re.search(r'(\d+):(\d+)(:(\d+)((\.|,)(\d+))?)?( (AM|PM))? ?([a-zA-Z]+|[+-]\d{4}|[+-]\d+:\d+)?$', date_time_str)
    if g:
        hour, minute, second, microsecond, am_pm = map(g.group, [1, 2, 4, 7, 9])
        if am_pm and am_pm.upper() == 'PM':
            hour = int(hour) + 12
        else:
            hour = int(hour)
        minute, second = int(minute), 0 if second is None else int(second)
        if microsecond:
            microsecond = int(microsecond) * 1000 if len(microsecond) == 3 else int(microsecond)
        else:
            microsecond = 0

    return datetime.datetime(year, month, day, hour, minute, second, microsecond)


def tostr(value, encoding='utf-8'):
    """Convert value to string.

    :param value: input value.
    :param str encoding: encoding.
    :return str: string.
    """
    if value is None:
        return ''
    if isinstance(value, bytearray) or (sys.version_info >= (3, 0) and isinstance(value, bytes)):
        return value.decode(encoding=encoding)
    elif not isinstance(value, str):
        return str(value)
    return value


def total_seconds(start_date, ends_date, date_format=None):
    """Return total seconds between two date times.

    :param datetime.datetime|str start_date: starts datetime.
    :param datetime.datetime|str ends_date: ends datetime.
    :param str date_format: date format string.
    :return float: total seconds.
    """
    if start_date is None or ends_date is None:
        raise ValueError('both start_date and ends_date cannot be null')
    if not isinstance(start_date, datetime.datetime):
        start_date = str2date(start_date, date_format)
    if not isinstance(ends_date, datetime.datetime):
        ends_date = str2date(ends_date, date_format)
    timedelta = ends_date - start_date
    return (timedelta.microseconds + (timedelta.seconds + timedelta.days * 24 * 3600) * 10.0 ** 6) / 10.0 ** 6


def compare_str(string1, string2, ignore_case=False):
    """Compare two strings.
    1 : first string is larger than the second
    0 : they are the same
    -1: first string is less than the second.

    :param str string1: the first string.
    :param str string2: the second string
    :param bool ignore_case: should ignore character case or not.
    :return int: 0-Equal, 1-Greater than, -1: Less than.
    """
    if string1 is None and string2 is None:
        return 0
    elif string1 is None:
        return -1
    elif string2 is None:
        return 1
    if ignore_case:
        if not isinstance(string1, str):
            string1 = str(string1)
        if not isinstance(string2, str):
            string2 = str(string2)
        string1 = string1.upper()
        string2 = string2.upper()

    if string1 == string2:
        return 0
    elif string1 > string2:
        return 1
    else:
        return -1


class Choice(object):
    """Choice class.

    e.g.:
    a = Choice(1, 2, 3)

    1 in a
    >True

    '1' in a
    >False

    str(a)
    >(1, 2, 3)

    repr(a)
    >Choice(*(1, 2, 3))
    """
    __slots__ = ['choices']

    def __init__(self, *choices):
        self.choices = choices if choices else ()

    def __contains__(self, item):
        return item in self.choices

    def __str__(self):
        return str(self.choices)

    def __repr__(self):
        return 'Choice(*%s)' % self.__str__()


def find_item_by_dict_keys(result_items, expect_item, keys):
    """Find matched item from a list of dict.

    :param list result_items: a list of dict.
    :param dict expect_item: expect dict value.
    :param tuple|list|str keys: keys in dict.
    :return int: matched index in result_items.
    """
    if isinstance(keys, tuple) or isinstance(keys, list):
        for key_item in keys:
            if key_item not in expect_item:
                break
        else:
            for result_index, result_item in enumerate(result_items):
                for key_item in keys:
                    if result_item.get(key_item) != expect_item[key_item]:
                        break
                else:
                    return result_index
            else:
                raise AssertionError('result does not contain: %s' % expect_item)
    elif keys in expect_item:
        expect_item_key = expect_item[keys]
        for result_index, result_item in enumerate(result_items):
            if (keys in result_item) and result_item.get(keys) == expect_item_key:
                return result_index
        else:
            raise AssertionError('result does not contain[by %s=%s]: %s' % (keys, expect_item_key, expect_item))


def _verify_list(result_value, expect_value, key_in_list=None, count_in_list=True, ignore_key_list=None):
    assert isinstance(result_value, list)
    if count_in_list:
        assert len(expect_value) == len(result_value), 'result\'s length(%s) does not match expect\'s length(%s)' % (len(result_value), len(expect_value))
    else:
        assert len(expect_value) <= len(result_value), 'result\'s length(%s) is less than expect\'s length(%s)' % (len(result_value), len(expect_value))
    for index, expect_item in enumerate(expect_value):
        if isinstance(expect_item, dict):
            result_index, key_in_list2 = None, None
            if key_in_list is not None:
                if isinstance(key_in_list, list):
                    key_in_list2 = copy.deepcopy(key_in_list)
                    dict_key = key_in_list2.pop(0)
                else:
                    dict_key = key_in_list
                    key_in_list2 = key_in_list
                result_index = find_item_by_dict_keys(result_value, expect_item, dict_key)
            if result_index is not None:
                verify_dictionary(result_value[result_index], expect_item, key_in_list2, count_in_list, ignore_key_list)
            else:
                result_matched_item = result_value[index]
                verify_dictionary(result_matched_item, expect_item, key_in_list, count_in_list, ignore_key_list)
        else:
            assert expect_item in result_value, 'result does not contain: %s' % expect_item


def verify_dictionary(result, expect, key_in_list=None, count_in_list=True, ignore_key_list=None):
    """Verify 2 dictionaries.

    :param dict|list result : Input dictionary which will be verified with the expected dictionary.
    :param dict|list expect: Expected dictionary
            it supports regular expression OBJECT as one of your expect value.
            e.g.: dict(a=re.compile(r'hello.+world'))
            wrong example: dict(a=r'hello.+world'), it will know regular expression as normal string.
    :param key_in_list : if dictionary contains list, and list item is dictionary, it requires keys to
        fetch matched item from result to compare with. it is a list of these keys in order.
        keys can be str, a tuple/list of sub-key.
    :param count_in_list : if value in dict is a list, and it will do exact count match if True, otherwise,
        it only will the count in result dict is not less than count in expect dict,
        and then search each element in result's value
    :param ignore_key_list : a list of keys should be ignored for verification.
    """
    if expect is None:
        assert result is None
    else:
        assert result is not None

    if isinstance(expect, list):
        _verify_list(result, expect, key_in_list, count_in_list, ignore_key_list)
    else:
        for k in expect:
            if ignore_key_list and k in ignore_key_list:
                continue
            assert k in result, 'result does not contains %s' % k
            expect_value = expect.get(k)
            result_value = result.get(k)
            if expect_value is None:
                assert result_value is None, 'the value of %s is not None' % k
            else:
                assert result_value is not None, 'the value of %s is None' % k

                if isinstance(expect_value, dict):
                    result_value = result_value[0] if isinstance(result_value, list) else result_value
                    assert isinstance(result_value, dict), 'the value of %s in result is not a dict' % k
                    verify_dictionary(result_value, expect_value, key_in_list, count_in_list, ignore_key_list)
                elif isinstance(expect_value, list):
                    _verify_list(result_value, expect_value, key_in_list, count_in_list, ignore_key_list)
                elif isinstance(expect_value, Choice):
                    assert result_value in expect_value, '%s=%s in result is not one of %s' % (k, result_value, expect_value)
                elif 'SRE_Pattern' in str(type(expect_value)):
                    assert expect_value.match(str(result_value)) is not None, '%s=%s in result does mot match expected regular expression: %s' % (k, result_value, expect_value.pattern)
                else:
                    assert result_value == expect_value, '%s=%s in result does not match the expected %s=%s' % (k, result_value, k, expect_value)


def to_boolean(value):
    """Convert value to boolean, "1" or "true" is True, others are False.

    :param value: input value.
    :return bool: bool value.
    """
    return value is not None and (value == 1 or value == '1' or str(value).upper() == 'TRUE')


def to_dict(input_data):
    """Convert to dict.

    :param str input_data:
    :return dict: dict.
    """
    if not isinstance(input_data, dict):
        try:
            return json.loads(input_data)
        except Exception:
            raise ValueError('Input data is not json format.')
    return input_data


def get_matched(text, pattern, ignore_case=True):
    """Get matched value by regular expression.

    :param str text : input text.
    :param str pattern : regular expression.
    :param bool ignore_case : ignore case.
    :return str: matched value.
    """
    result = re.findall(pattern, text, re.I if ignore_case else 0)
    if result and len(result) > 0:
        return result[0]


def import_module(file_path):
    """Import module from file.

    :param str file_path : file path.
    :return: module object.
    """
    if not os.path.isabs(file_path):
        file_path = os.path.normpath(os.path.join(os.getcwd(), file_path))
    module = os.path.splitext(os.path.basename(file_path))[0]
    if sys.version_info < (3, 3):
        import imp
        fn, filename, data = imp.find_module(module, [os.path.dirname(file_path)])
        t = imp.load_module(module, fn, filename, data)
        if fn is not None and not fn.closed:
            fn.close()
        return t
    else:
        from importlib import machinery
        loader = machinery.SourceFileLoader(module, file_path)
        return loader.load_module()


class SysStandardOutput(object):
    """Capture sys.stdout."""
    def __init__(self):
        self.output = None
        self._stdout = None
        self._stringio = None

    def __enter__(self):
        self.output = None
        self._stdout = sys.stdout
        sys.stdout = self._stringio = StringIO()
        return self

    def __exit__(self, *args):
        self.output = self._stringio.getvalue()
        del self._stringio
        sys.stdout = self._stdout

    def __str__(self):
        return self.output

    def __len__(self):
        return len(self.output)

    def __contains__(self, item):
        """Return key in self.

        :param str item: item.
        :return bool: True or False
        """
        return item in self.output
