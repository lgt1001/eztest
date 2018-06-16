import unittest


class UserTestOne(unittest.TestCase):
    def setUp(self):
        print('Setup function in one')

    @classmethod
    def setUpClass(cls):
        print('Setup class in one')

    def tearDown(self):
        print('Teardown function in one')

    @classmethod
    def tearDownClass(cls):
        print('Teardown class in one')

    def test_hello(self,):
        print("Hello in one")
        self.assertTrue(1 == 0)

    def test_world(self):
        print("World in one")


class UserTestTwo(unittest.TestCase):
    def setUp(self):
        print('Setup function in two')

    @classmethod
    def setUpClass(cls):
        print('Setup class in two')

    def tearDown(self):
        print('Teardown function in two')

    @classmethod
    def tearDownClass(cls):
        print('Teardown class in two')

    def test_hello(self,):
        print("Hello in two")
        self.assertTrue(1 == 0)

    def test_world(self):
        print("World in two")