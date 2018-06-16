import time

from eztest import testcase


class MyCase(testcase.BaseCase):
    def __init__(self, url):
        super(MyCase,self).__init__()
        self.url = url

    def __deepcopy__(self, obj):
        new = super(MyCase, self).__deepcopy__(obj)
        new.url = self.url
        return new

    def initialize(self):
        self.log("-"*80, True)
        self.log("Doing case %s: %s" % (self.id, self.description), True)
        return True

    def run(self):
        print("Calling {}...".format(self.url))
        time.sleep(5)
        return True

    def verify(self):
        self.status = True
        self.log("Verifying...", True)


def setup_module():
    print("Setup module")


def teardown_module():
    print("Teardown module")


CASES = []
for i in range(2):
    c = MyCase('https://eztest/%d' % i)
    c.id = "case %d" % i
    c.description = "case desc %d" % i
    CASES.append(c)