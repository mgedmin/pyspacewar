#!/usr/bin/env python
"""
Run all unit tests.
"""

import unittest
import glob
import sys
import os


def main():
    sys.path.insert(0, 'src')
    suite = unittest.TestSuite()
    for filename in glob.glob('src/pyspacewar/tests/test_*.py'):
        name = os.path.basename(filename)[:-3]
        module = __import__('pyspacewar.tests.' + name, {}, {}, ('',))
        suite.addTest(module.test_suite())
    runner = unittest.TextTestRunner(verbosity=1)
    result = runner.run(suite)
    sys.exit(not result.wasSuccessful())


if __name__ == '__main__':
    main()
