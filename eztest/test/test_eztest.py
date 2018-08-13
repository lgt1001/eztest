import datetime
import unittest
import argparse
import eztest
from eztest import _to_datetime, _is_matched, _parser_args, __version__
from eztest.utility import SysStandardOutput


class TestEZTest(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        super(TestEZTest, self).__init__(*args, **kwargs)
        self.maxDiff = None

    def test_to_datetime(self):
        self.assertEqual(_to_datetime('2018-06-01 12:13:14'), datetime.datetime(2018, 6, 1, 12, 13, 14))
        with self.assertRaises(argparse.ArgumentTypeError):
            _to_datetime('2018-06-01 12:13:14.1234')
        with self.assertRaises(argparse.ArgumentTypeError):
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


    def test_parser(self):
        options = '{test,stop,calc,server,dump}'

        with SysStandardOutput() as f1, self.assertRaises(SystemExit):
            _parser_args(['eztest'])
        self.assertIn('usage: eztest [-h] [--version] {}'.format(options), f1.output)

        with SysStandardOutput() as f2, self.assertRaises(SystemExit):
            _parser_args(['eztest', 'abc'])
        self.assertIn("invalid choice: 'abc'", f2.output)

        with SysStandardOutput() as f1, self.assertRaises(SystemExit):
            _parser_args(['eztest', '-v'])
        self.assertIn(__version__, f1.output)

        with SysStandardOutput() as f2, self.assertRaises(SystemExit):
            _parser_args(['eztest', '--version'])
        self.assertIn(f1.output, f2.output)

        with SysStandardOutput() as f1, self.assertRaises(SystemExit):
            _parser_args(['eztest', '--help'])
        self.assertIn('usage: eztest [-h] [--version] {}'.format(options), f1.output)
        self.assertIn('positional arguments', f1.output)
        self.assertIn('optional arguments', f1.output)

        with SysStandardOutput() as f2, self.assertRaises(SystemExit):
            _parser_args(['eztest', '-h'])
        self.assertEqual(f1.output, f2.output)

        with SysStandardOutput() as f1, self.assertRaises(SystemExit):
            _parser_args(['eztest', 'test', '-h'])
        self.assertIn('usage: eztest test [-h] --target TARGET', f1.output)

        with SysStandardOutput() as f1, self.assertRaises(SystemExit):
            _parser_args(['eztest', 'test', '-h'])
        self.assertIn('usage: eztest test [-h] --target TARGET', f1.output)

        with SysStandardOutput() as f1, self.assertRaises(SystemExit):
            _parser_args(['eztest', 'test'])
        self.assertIn('error: the following arguments are required: --target/-t', f1.output)

        with SysStandardOutput() as f1, self.assertRaises(SystemExit):
            _parser_args(['eztest', 'test', '--target'])
        self.assertIn('error: argument --target/-t: expected one argument', f1.output)
        with SysStandardOutput() as f2, self.assertRaises(SystemExit):
            _parser_args(['eztest', 'test', '-t'])
        self.assertIn(f1.output, f2.output)

        with SysStandardOutput() as f1, self.assertRaises(SystemExit):
            _parser_args(['eztest', 'calc'])
        self.assertIn('error: the following arguments are required: --path/-p', f1.output)

        with SysStandardOutput() as f1, self.assertRaises(SystemExit):
            _parser_args(['eztest', 'calc', '--path'])
        self.assertIn('argument --path/-p: expected at least one argument', f1.output)
        with SysStandardOutput() as f2, self.assertRaises(SystemExit):
            _parser_args(['eztest', 'calc', '-p'])
        self.assertIn(f1.output, f2.output)

        def get_args(args):
            args = vars(args)
            args['func'] = args['func'].__name__
            print(str(args))

        eztest.dump = get_args
        eztest.calc = get_args
        eztest.test = get_args
        eztest.stop = get_args
        eztest.start_server = get_args
        eztest.stop_server = get_args

        expect_data = dict(eztest='test',
                           target='target',
                           classes=None,
                           not_classes=None,
                           cases=None,
                           not_cases=None,
                           mode='normal',
                           stress=1,
                           repeat=1,
                           interval=0,
                           limit=0,
                           starts=None,
                           duration=None,
                           ends=None,
                           report_folder=None,
                           report_server=None,
                           noreport=False,
                           nolog=False,
                           mail_config=None,
                           func='get_args')
        with SysStandardOutput() as f1:
            _parser_args(['eztest', 'test', '--target', 'target'])
        self.assertDictEqual(eval(f1.output), expect_data)

        expect_data = dict(eztest='test',
                           target='target',
                           classes=['class1', 'class2'],
                           not_classes=['class3', 'class4'],
                           cases=['case1', 'case2'],
                           not_cases=['case3', 'case4'],
                           mode='continuous',
                           stress=10,
                           repeat=11,
                           interval=12,
                           limit=13,
                           starts=datetime.datetime(2018, 1, 2, 3, 4, 5),
                           duration=1,
                           ends=datetime.datetime(2018, 11, 12, 13, 14, 15),
                           report_folder='report_folder',
                           report_server='report_server:1234',
                           noreport=True,
                           nolog=True,
                           mail_config='mail_config',
                           func='get_args')
        with SysStandardOutput() as f1:
            _parser_args(['eztest', 'test',
                          '--target', 'target',
                          '--classes', 'class1', 'class2',
                          '--not-classes', 'class3', 'class4',
                          '--cases', 'case1', 'case2',
                          '--not-cases', 'case3', 'case4',
                          '--mode', 'continuous',
                          '--stress', '10',
                          '--repeat', '11',
                          '--interval', '12',
                          '--limit', '13',
                          '--starts', '2018-01-02 03:04:05',
                          '--duration', '1',
                          '--ends', '2018-11-12 13:14:15',
                          '--report-folder', 'report_folder',
                          '--report-server', 'report_server:1234',
                          '--noreport',
                          '--nolog',
                          '--mail-config', 'mail_config'
                          ])
        self.assertDictEqual(eval(f1.output), expect_data)

if __name__ == '__main__':
    unittest.main()