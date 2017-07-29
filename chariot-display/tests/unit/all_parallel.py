import unittest
from concurrencytest import ConcurrentTestSuite, fork_for_tests
import os
import multiprocessing

_PACKAGE_PATH = os.path.dirname(os.path.abspath(__file__))
NUM_CORES = multiprocessing.cpu_count()

if __name__ == '__main__':
    print('Testing with ' + str(NUM_CORES) + ' cores')
    test_loader = unittest.defaultTestLoader.discover(_PACKAGE_PATH, pattern='*.py')
    unittest.TextTestRunner().run(ConcurrentTestSuite(test_loader, fork_for_tests(NUM_CORES)))

