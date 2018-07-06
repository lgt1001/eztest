from .my_case import MyCase


def setup_module():
    print('Setup module')


def teardown_module():
    print('Teardown module')


CASES = []
for i in range(2):
    c = MyCase()
    c.url = 'https://eztest/%d' % i
    c.id = 'case %d' % i
    c.description = 'case desc %d' % i
    CASES.append(c)
