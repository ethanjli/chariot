import unittest
import os

_PACKAGE_PATH = os.path.dirname(os.path.abspath(__file__))

if __name__ == '__main__':
    test_loader = unittest.defaultTestLoader.discover(_PACKAGE_PATH, pattern='*.py')
    unittest.TextTestRunner().run(test_loader)

