import datetime
import re
import sys
import unittest

from eztest import utility


class TestUtility(unittest.TestCase):
    def test_date2str(self):
        dtnow = datetime.datetime(2018, 6, 1, 12, 13, 14, 123456)
        self.assertEqual(utility.date2str(dtnow), '2018-06-01 12:13:14.123456')
        self.assertEqual(utility.date2str(dtnow, '%Y-%m-%d'), '2018-06-01')

        dtnow = datetime.datetime(2018, 6, 1)
        self.assertEqual(utility.date2str(dtnow), '2018-06-01 00:00:00.000000')

    def test_str2date(self):
        self.assertEqual(utility.str2date('2018-06-01 12:13:14.123456', '%Y-%m-%d %H:%M:%S.%f'), datetime.datetime(2018, 6, 1, 12, 13, 14, 123456))
        with self.assertRaises(ValueError):
            utility.str2date('2018-06-01 12:13:14.123456', '%Y-%m-%d')

        self.assertEqual(utility.str2date('2018-06-01', '%Y-%m-%d'), datetime.datetime(2018, 6, 1))
        self.assertEqual(utility.str2date('2018-06-01'), datetime.datetime(2018, 6, 1))
        self.assertEqual(utility.str2date('2018/06/01'), datetime.datetime(2018, 6, 1))
        self.assertEqual(utility.str2date('01/06/2018'), datetime.datetime(2018, 6, 1))
        self.assertEqual(utility.str2date('2018 Jun 1'), datetime.datetime(2018, 6, 1))
        self.assertEqual(utility.str2date('Jun 1 2018'), datetime.datetime(2018, 6, 1))
        self.assertEqual(utility.str2date('1 Jun 2018'), datetime.datetime(2018, 6, 1))
        self.assertEqual(utility.str2date('Jun 1, 2018'), datetime.datetime(2018, 6, 1))
        self.assertEqual(utility.str2date('1. Jun 2018'), datetime.datetime(2018, 6, 1))
        self.assertEqual(utility.str2date('1.6.2018'), datetime.datetime(2018, 6, 1))
        self.assertEqual(utility.str2date('2018.6.1'), datetime.datetime(2018, 6, 1))
        self.assertEqual(utility.str2date('Thursday, June 1, 2018'), datetime.datetime(2018, 6, 1))

        self.assertEqual(utility.str2date('2018-06-01 12:13:14.123456'), datetime.datetime(2018, 6, 1, 12, 13, 14, 123456))
        self.assertEqual(utility.str2date('2018-06-01 12:13:14.123456 PDT'), datetime.datetime(2018, 6, 1, 12, 13, 14, 123456))
        self.assertEqual(utility.str2date('2018-06-01T12:13:14.123Z'), datetime.datetime(2018, 6, 1, 12, 13, 14, 123000))
        self.assertEqual(utility.str2date('2018-06-01 12:13:14.123'), datetime.datetime(2018, 6, 1, 12, 13, 14, 123000))
        self.assertEqual(utility.str2date('2018-06-01 12:13:14'), datetime.datetime(2018, 6, 1, 12, 13, 14))
        self.assertEqual(utility.str2date('2018-06-01 12:13'), datetime.datetime(2018, 6, 1, 12, 13))
        self.assertEqual(utility.str2date('2018-06-01 06:13 PM'), datetime.datetime(2018, 6, 1, 18, 13))
        self.assertEqual(utility.str2date('2018-06-01 06:13 AM'), datetime.datetime(2018, 6, 1, 6, 13))
        self.assertEqual(utility.str2date('2018-06-01 12:13:14 +08:00'), datetime.datetime(2018, 6, 1, 12, 13, 14))
        self.assertEqual(utility.str2date('Thursday, June 1, 2018 12:13:14.123 PDT'), datetime.datetime(2018, 6, 1, 12, 13, 14, 123000))

    def test_tostr(self):
        self.assertEqual(utility.tostr(None), '')
        self.assertEqual(utility.tostr([1, 2, 3]), '[1, 2, 3]')
        self.assertEqual(utility.tostr((1, 2, 3)), '(1, 2, 3)')
        self.assertEqual(utility.tostr(dict(a=1)), '''{'a': 1}''')
        self.assertEqual(utility.tostr(bytearray('123', encoding='utf-8')), '123')
        if sys.version_info >= (3, 0):
            self.assertEqual(utility.tostr(bytes('123', encoding='utf-8')), '123')

    def test_total_seconds(self):
        self.assertEqual(utility.total_seconds(
            datetime.datetime(2018, 6, 1, 12, 13, 14, 123000),
            datetime.datetime(2018, 6, 2, 13, 14, 14, 123456)
        ), 90060.000456)
        self.assertEqual(utility.total_seconds(
            '2018-06-01 12:13:14.123',
            datetime.datetime(2018, 6, 2, 13, 14, 14, 123456)
        ), 90060.000456)
        self.assertEqual(utility.total_seconds(
            datetime.datetime(2018, 6, 1, 12, 13, 14, 123000),
            '2018-06-02 13:14:14.123456'
        ), 90060.000456)
        self.assertEqual(utility.total_seconds(
            '2018-06-01 12:13:14.123',
            '2018-06-02 13:14:14.123456'
        ), 90060.000456)

        with self.assertRaises(ValueError):
            utility.total_seconds(None, datetime.datetime(2018, 6, 2, 13, 14, 14, 123456))
        with self.assertRaises(ValueError):
            utility.total_seconds(datetime.datetime(2018, 6, 1, 12, 13, 14, 123000), None)
        with self.assertRaises(ValueError):
            utility.total_seconds(None, None)

    def test_compare_str(self):
        str1 = 'Abc'
        str2 = 'abc'
        str3 = 'Acd'

        self.assertEqual(utility.compare_str(str1, str1), 0)
        self.assertEqual(utility.compare_str(str1, str2), -1)
        self.assertEqual(utility.compare_str(str1, str3), -1)
        self.assertEqual(utility.compare_str(str1, str2, ignore_case=True), 0)

        self.assertEqual(utility.compare_str(None, None), 0)
        self.assertEqual(utility.compare_str(str1, None), 1)
        self.assertEqual(utility.compare_str(None, str1), -1)

    def test_choice(self):
        c = utility.Choice()
        self.assertTupleEqual(c.choices, ())

        c = utility.Choice(1, 2, 3)
        self.assertTupleEqual(c.choices, (1, 2, 3))
        self.assertIn(1, c.choices)
        self.assertIn(2, c.choices)
        self.assertIn(3, c.choices)
        self.assertNotIn(4, c.choices)

        self.assertEqual(str(c), '(1, 2, 3)')
        self.assertEqual(repr(c), 'Choice(*(1, 2, 3))')

    def test_to_boolean(self):
        self.assertEqual(utility.to_boolean(1), True)
        self.assertEqual(utility.to_boolean(0), False)
        self.assertEqual(utility.to_boolean(10), False)
        self.assertEqual(utility.to_boolean('1'), True)
        self.assertEqual(utility.to_boolean('True'), True)
        self.assertEqual(utility.to_boolean('true'), True)
        self.assertEqual(utility.to_boolean('tttt'), False)
        self.assertEqual(utility.to_boolean(None), False)

    def test_to_dict(self):
        a = '{"a": 1}'
        b = '''{'a': 1}'''
        self.assertDictEqual(utility.to_dict(a), dict(a=1))
        with self.assertRaises(ValueError):
            utility.to_dict(b)
        self.assertEqual(utility.to_dict('123'), 123)
        self.assertEqual(utility.to_dict('[1, 2, 3]'), [1, 2, 3])

    def test_get_matched(self):
        a = '<html><head>abc</head><body></body></html>'
        self.assertEqual(utility.get_matched(a, r'<head>(.+)?</head>'), 'abc')
        self.assertEqual(utility.get_matched(a, r'<head2>(.+)?</head2>'), None)
        self.assertEqual(utility.get_matched(a, r'<HEAD>(.+)?</HEAD>', ignore_case=True), 'abc')
        self.assertEqual(utility.get_matched(a, r'<HEAD>(.+)?</HEAD>', ignore_case=False), None)

    def test_sys_standard_output(self):
        with utility.SysStandardOutput() as f:
            print('Hello World')
            print('Bob and Tom')
        self.assertEqual(str(f), 'Hello World\nBob and Tom\n')
        self.assertEqual(len(f), 24)
        self.assertIn('Hello World', f)

    def test_find_item_by_dict_keys(self):
        data = [dict(a=1, b=2), dict(a=11, b=22)]
        exp_item1 = dict(a=1)
        exp_item2 = dict(a=1, b=2)
        exp_item3 = dict(a=1, b=3)
        exp_item4 = dict(a=4, b=3)
        self.assertEqual(utility.find_item_by_dict_keys(data, exp_item1, 'a'), 0)
        self.assertEqual(utility.find_item_by_dict_keys(data, exp_item2, 'a'), 0)
        self.assertEqual(utility.find_item_by_dict_keys(data, exp_item3, 'a'), 0)
        with self.assertRaises(AssertionError):
            utility.find_item_by_dict_keys(data, exp_item4, 'a')
        self.assertEqual(utility.find_item_by_dict_keys(data, exp_item1, ('a', 'b')), None)
        self.assertEqual(utility.find_item_by_dict_keys(data, exp_item2, ('a', 'b')), 0)
        with self.assertRaises(AssertionError):
            utility.find_item_by_dict_keys(data, exp_item3, ('a', 'b'))

        self.assertEqual(utility.find_item_by_dict_keys(data, exp_item1, ['a', 'b']), None)
        self.assertEqual(utility.find_item_by_dict_keys(data, exp_item2, ['a', 'b']), 0)
        with self.assertRaises(AssertionError):
            utility.find_item_by_dict_keys(data, exp_item3, ['a', 'b'])

        self.assertEqual(utility.find_item_by_dict_keys(data, exp_item1, 'c'), None)

    def test_verify_dictionary(self):
        data = [dict(a=1, b=2), dict(a=1, b=3), dict(a=11, b=22)]
        utility.verify_dictionary(data, [dict(a=1, b=utility.Choice(2, 3))], key_in_list='a', count_in_list=False)
        with self.assertRaises(AssertionError):
            utility.verify_dictionary(data, [dict(a=1, b=22)], key_in_list='a', count_in_list=False)
        with self.assertRaises(AssertionError):
            utility.verify_dictionary(data, [dict(a=1, b=2)], key_in_list='a', count_in_list=True)
        utility.verify_dictionary(data, [dict(a=1, b=22)], key_in_list='a', count_in_list=False, ignore_key_list='b')
        utility.verify_dictionary(data, [dict(a=1, b=2)], key_in_list=('a', 'b'), count_in_list=False)

        data = [dict(a='1', b='2'), dict(a='1', b='3'), dict(a='11', b='22')]
        utility.verify_dictionary(data, [dict(a='1', b=re.compile(r'2|33'))], key_in_list='a', count_in_list=False)

        utility.verify_dictionary(dict(a='1', b='2'), dict(a='1', b=re.compile(r'2|33')))
        utility.verify_dictionary(dict(a='1', b='2'), dict(a='1', b='2'))
        with self.assertRaises(AssertionError):
            utility.verify_dictionary(dict(a='1', b='2'), dict(a='1', b='3'))

        result = dict(root=[dict(a=1, b=2), dict(a=2, b=3)])
        expect = dict(root=[dict(a=2, b=3), dict(a=1, b=2)])
        utility.verify_dictionary(result, expect, key_in_list='a')

        utility.verify_dictionary([1, 2, 3], [3, 2, 1])
        with self.assertRaises(AssertionError):
            utility.verify_dictionary([1,2,3], [3,4,5])


if __name__ == '__main__':
    unittest.main()