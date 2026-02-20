import unittest


def load_tests(loader, tests, pattern):
    return loader.discover("tests", pattern="test_*.py")


if __name__ == "__main__":
    unittest.main()
