import datetime
import re
import sys
import unittest

from eztest import _to_datetime, _is_matched


class TestEZTest(unittest.TestCase):
    def test_to_datetime(self):
        self.assertEqual(_to_datetime('2018-06-01 12:13:14'), datetime.datetime(2018, 6, 1, 12, 13, 14))
        with self.assertRaises(ValueError):
            _to_datetime('2018-06-01 12:13:14.1234')
        with self.assertRaises(ValueError):
            _to_datetime('2018-06-01 12:13')

    def test_is_matched(self):
        self.assertTrue(_is_matched('hello', None, None))
        self.assertTrue(_is_matched('hello', ['hello'], None))
        self.assertTrue(_is_matched('hello', ['*llo'], None))
        self.assertTrue(_is_matched('hello', ['hel*'], None))
        self.assertTrue(_is_matched('hello', ['*el*'], None))
        self.assertTrue(_is_matched('hello', ['world', '*el*'], None))

        self.assertFalse(_is_matched('hello', None, ['hello']))
        self.assertFalse(_is_matched('hello', None, ['*llo']))
        self.assertFalse(_is_matched('hello', None, ['hel*']))
        self.assertFalse(_is_matched('hello', None, ['*el*']))
        self.assertFalse(_is_matched('hello', None, ['world', '*el*']))
        self.assertFalse(_is_matched('hello', ['world', '*el*'], ['hello']))


if __name__ == '__main__':
    unittest.main()