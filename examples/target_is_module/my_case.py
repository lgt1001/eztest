import time

from eztest import testcase


class MyCase(testcase.BaseCase):
    def __init__(self):
        super(MyCase,self).__init__()
        self.url = None

    def __deepcopy__(self, obj):
        new = super(MyCase, self).__deepcopy__(obj)
        new.url = self.url
        return new

    def initialize(self):
        self.log('Doing case %s' % self.description)
        return True

    def run(self):
        self.log('Calling {}...'.format(self.url))
        time.sleep(5)
        return True

    def verify(self):
        self.status = True
        self.log('Verifying...')
