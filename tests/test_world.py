#!/usr/bin/env python

import unittest
import doctest
import sys
import os


def test_suite():
    path = os.path.join(os.path.dirname(__file__), os.path.pardir)
    if path not in sys.path:
        sys.path.append(path)
    return doctest.DocTestSuite('world')


if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
