import time


def setup_module():
    print("Setup module")


def teardown_module():
    print("Teardown module")


def setup_function():
    print("Setup_function")


def teardown_function():
    time.sleep(1)
    print("Teardown_function")


def test_hello():
    print("Hello")
    assert 1 == 0


def test_world():
    print("World")