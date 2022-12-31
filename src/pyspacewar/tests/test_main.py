#!/usr/bin/env python

import sys

import pytest


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


@pytest.fixture(scope='module', autouse=True)
def fake_game_ui(test=None):
    from pyspacewar import main
    main.GameUI = FakeGameUI
