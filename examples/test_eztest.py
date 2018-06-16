import os

import eztest


def target_is_test_function():
    """Target is a file, and it contains "test_*" functions."""
    file_path = os.path.join('target_is_test_func', 'test_case.py')
    eztest.main(['', '--target', file_path])


def continuous_test():
    """Continuous testing, define repeat times."""
    file_path = os.path.join('target_is_test_func', 'test_case.py')
    eztest.main(['', '-m', 'continuous',
                 '-t', file_path,
                 '-r', '2',
                 '--nolog'])


def simultaneous_test():
    """Simultaneous testing, define stress count and repeat times."""
    file_path = os.path.join('target_is_test_func', 'test_case.py')
    eztest.main(['', '-m', 'simultaneous',
                 '-t', file_path,
                 '-r', '2',
                 '-s', '2',
                 '--nolog'])


def concurrency_test():
    """Concurrency testing, define stress count and ends datetime."""
    file_path = os.path.join('target_is_test_func', 'test_case.py')
    eztest.main(['', '-m', 'concurrency',
                 '-t', file_path,
                 '-s', '2',
                 '--duration', '1',
                 '--nolog'])


def frequent_test():
    """Frequent testing, define stress count and repeat times and internal in second."""
    file_path = os.path.join('target_is_test_func', 'test_case.py')
    eztest.main(['', '-m', 'frequent',
                 '-t', file_path,
                 '-d', '1',
                 '-s', '2',
                 '-i', '1',
                 '--nolog'])


def ignore_cases():
    """Define cases to be ignored."""
    file_path = os.path.join('target_is_test_func', 'test_case.py')
    eztest.main(['', '-m', 'simultaneous',
                 '-t', file_path,
                 '--not-cases', 'test_hello',
                 '-r', '2',
                 '-s', '2',
                 '--nolog'])


def target_is_unittest():
    """Target is a file, and it contains classes inherit from unittest.TestCase."""
    file_path = os.path.join('target_is_unittest', 'test_case.py')
    eztest.main(['', '-t', file_path])


def target_is_module():
    """Target is a module, and has CASES variable defined."""
    eztest.main(['', '-t', 'target_is_module'])


def target_is_module_not_base_case():
    """Target is a module, and has not CASES variable defined."""
    eztest.main(['', '-t', 'target_is_test_func.test_case'])


def target_is_file():
    """Target is a file, and has CASES variable defined."""
    file_path = os.path.join('target_is_file', 'my_case.py')
    eztest.main(['', '-t', file_path])


def target_is_folder_with_base_case():
    """Target is a module, and has CASES variable defined."""
    eztest.main(['', '-t', os.path.join(os.getcwd(), 'target_is_module')])


if __name__ == '__main__':
    # simultaneous_test()
    # continuous_test()
    # target_is_test_function()
    # target_is_unittest()
    # target_is_module()
    # target_is_module_not_base_case()
    # target_is_file()
    # target_is_folder_with_base_case()
    # run from command
    # os.system('eztest -t "{}"'.format(os.path.join('target_is_test_func', 'test_case.py')))
    pass