#!/usr/bin/env python

import unittest
import doctest
import sys
import os


class Object(object):

    def __init__(self, name, mass=0):
        self.name = name
        self.mass = mass

    def __repr__(self):
        return self.name

    def gravitate(self, massive_obj, dt):
        print "%s attracts %s for %s time units" % (massive_obj.name,
                                                    self.name, dt)

    def move(self, dt):
        print "Moving %s for %s time units" % (self.name, dt)


def doctest_World():
    """Tests for basic World functions

        >>> from world import World
        >>> w = World()

    At the beginning the universe was empty

        >>> w.time
        0.0
        >>> w.objects
        []

    You can add objects to it

        >>> o = Object('o')
        >>> w.add(o)
        >>> w.objects
        [o]

    You can remove objects

        >>> w.remove(o)
        >>> w.objects
        []

    All the interesting things happen when time ticks

        >>> w.update(0.1)
        >>> print w.time
        0.1

    well, the interesting things only happen if you have interesting objects
    in the universe

        >>> w.add(Object('brick1'))
        >>> w.add(Object('brick2'))
        >>> w.update(0.1)
        Moving brick1 for 0.1 time units
        Moving brick2 for 0.1 time units

    Some objects have mass and thus attract other objects (even those that have
    no mass)

        >>> w.add(Object('planet', mass=100))
        >>> w.update(0.1)
        planet attracts brick1 for 0.1 time units
        planet attracts brick2 for 0.1 time units
        Moving brick1 for 0.1 time units
        Moving brick2 for 0.1 time units
        Moving planet for 0.1 time units

        >>> w.add(Object('sun', mass=1e20))
        >>> w.update(0.1)
        planet attracts brick1 for 0.1 time units
        planet attracts brick2 for 0.1 time units
        planet attracts sun for 0.1 time units
        sun attracts brick1 for 0.1 time units
        sun attracts brick2 for 0.1 time units
        sun attracts planet for 0.1 time units
        Moving brick1 for 0.1 time units
        Moving brick2 for 0.1 time units
        Moving planet for 0.1 time units
        Moving sun for 0.1 time units

    """


def doctest_World_collision_detection():
    """Tests for collision detection

        >>> from world import World
        >>> w = World()

    You can check whether to objects collide.

        >>> o1 = Object('o1')
        >>> o2 = Object('o2')
        >>> w.collide(o1, o2)
        False

    """


def test_suite():
    path = os.path.join(os.path.dirname(__file__), os.path.pardir)
    if path not in sys.path:
        sys.path.append(path)
    return unittest.TestSuite([
                        doctest.DocTestSuite('world'),
                        doctest.DocTestSuite()])


if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
