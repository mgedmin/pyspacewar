#!/usr/bin/env python

import unittest
import doctest
import sys
import os


class TimeSourceStub(object):

    delta = 10

    def __init__(self):
        self.counter = 0

    def now(self):
        self.counter += 1
        return self.counter

    def wait(self, time_point):
        print "Waiting for %s" % time_point
        self.counter = max(self.counter, time_point)


class Ticker(object):
    """Fake world object."""

    mass = 0
    radius = 0

    def move(self, dt):
        print "Tick (%s)" % dt


def doctest_PythonTimeSource():
    """Tests for PythonTimeSource

        >>> from game import PythonTimeSource
        >>> ts = PythonTimeSource(40)
        >>> ts.ticks_per_second
        40
        >>> round(ts.delta * ts.ticks_per_second, 3)
        1.0

    You can get a current timestamp and wait for the future

        >>> back_then = ts.now()
        >>> future = back_then + ts.delta
        >>> ts.wait(future)
        >>> now = ts.now()
        >>> eps = 0.01
        >>> now >= future - eps or 'error: %r < %r' % (now, future)
        True

    You can safely wait for the past

        >>> ts.wait(back_then)

    """


def doctest_Game():
    """Tests for Game

        >>> from game import Game
        >>> g = Game()
        >>> g.world.objects
        []
        >>> g.time_source.ticks_per_second == Game.TICKS_PER_SECOND
        True

    """


def doctest_Game_randomly_place():
    """Tests for Game.randomly_place

    Let us create a screaming brick for this test

        >>> from world import Object
        >>> class Brick(Object):
        ...     def collision(self, other):
        ...         print "Aaaaargh!"

    The game is able to position objects randomly so that they never overlap

        >>> from game import Game
        >>> g = Game()
        >>> for n in range(100):
        ...     g.randomly_place(Brick(radius=10))
        >>> len(g.world.objects)
        100
        >>> g.world.update(1)

    """


def doctest_Game_wait_for_tick():
    """Tests for Game.wait_for_tick

        >>> from game import Game
        >>> g = Game()
        >>> ts = g.time_source = TimeSourceStub()
        >>> g.world.add(Ticker())

    Initial call to g.wait_for_tick remembers the current time.  All other
    calls wait the necessary amount.  Each call also causes an update in the
    game world.

        >>> g.wait_for_tick()
        >>> g.wait_for_tick()
        Tick (0.2)
        Waiting for 11
        >>> g.wait_for_tick()
        Tick (0.2)
        Waiting for 21
        >>> g.wait_for_tick()
        Tick (0.2)
        Waiting for 31

    The waiting time is independent of outside delays

        >>> ts.counter += 5
        >>> g.wait_for_tick()
        Tick (0.2)
        Waiting for 41
        >>> ts.counter += 105
        >>> g.wait_for_tick()
        Tick (0.2)
        Waiting for 51

    """


def doctest_Game_new():
    """Tests for Game.new

        >>> from game import Game
        >>> g = Game.new()

    """


def test_suite():
    path = os.path.join(os.path.dirname(__file__), os.path.pardir)
    if path not in sys.path:
        sys.path.append(path)
    return unittest.TestSuite([
                        doctest.DocTestSuite('game'),
                        doctest.DocTestSuite()])


if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
