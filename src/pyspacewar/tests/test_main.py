#!/usr/bin/env python

import unittest
import doctest
import os
import sys


class FakeGameUI(object):

    counter = 3

    def load_settings(self):
        pass

    def init(self):
        pass

    def wait_for_tick(self):
        pass

    def interact(self):
        self.counter -= 1
        if self.counter <= 0:
            sys.exit()

    def draw(self):
        pass

    def save_settings(self):
        pass


def doctest_main():
    """Test for main

        >>> from pyspacewar.main import main
        >>> main(['-f', '-d', '--no-sound', '--no-music', '-m', '640x480'])

        >>> main(['-m', 'lalala'])
        Traceback (most recent call last):
          ...
        SystemExit: pyspacewar: error: invalid mode: lalala

    """


def setUp(test=None):
    from pyspacewar import main
    main.GameUI = FakeGameUI


def test_suite():
    path = os.path.normpath(
        os.path.join(os.path.dirname(__file__), '..', '..'))
    if path not in sys.path:
        sys.path.append(path)
    return doctest.DocTestSuite(setUp=setUp)


if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
