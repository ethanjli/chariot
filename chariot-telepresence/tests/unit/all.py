import unittest
import os

_PACKAGE_PATH = os.path.dirname(os.path.abspath(__file__))

test_loader = unittest.defaultTestLoader.discover(_PACKAGE_PATH, pattern='*.py')
test_runner = unittest.TextTestRunner()
test_runner.run(test_loader)

