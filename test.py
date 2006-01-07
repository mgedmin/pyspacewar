#!/usr/bin/env python
"""
Run all unit tests.
"""

import unittest
import glob
import os


def main():
    suite = unittest.TestSuite()
    for filename in glob.glob('tests/test_*.py'):
        name = os.path.basename(filename)[:-3]
        module = __import__('tests.' + name, {}, {}, ('',))
        suite.addTest(module.test_suite())
    runner = unittest.TextTestRunner(verbosity=1)
    runner.run(suite)


if __name__ == '__main__':
    main()
