#!/usr/bin/env python

import unittest
import doctest
import sys
import os


class Object(object):

    def __init__(self, name, mass=0, radius=0):
        self.name = name
        self.mass = mass
        self.radius = radius

    def __repr__(self):
        return self.name

    def distanceTo(self, other):
        return 1e100

    def gravitate(self, massive_obj, dt):
        print "%s attracts %s for %s time units" % (massive_obj.name,
                                                    self.name, dt)

    def move(self, dt):
        print "Moving %s for %s time units" % (self.name, dt)

    def collision(self, other):
        print "%s collides with %s" % (self.name, other.name)


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


def doctest_World_collision_detection_in_update():
    """Tests for collicition detection

        >>> from world import World, Vector
        >>> w = World()

        >>> o1, o2, o3 = map(Object, ['o1', 'o2', 'o3'])
        >>> w.add(o1)
        >>> w.add(o2)
        >>> w.add(o3)

        >>> w.collide = lambda a, b: a is o1 and b is o3
        >>> w.update(1.0)
        Moving o1 for 1.0 time units
        Moving o2 for 1.0 time units
        Moving o3 for 1.0 time units
        o1 collides with o3
        o3 collides with o1

    """


def doctest_World_death_and_birth_in_update():
    """Test for spawning and removing objects during update

        >>> from world import World, Vector
        >>> w = World()

        >>> o1, o2, o3, o4, o5 = map(Object, ['o1', 'o2', 'o3', 'o4', 'o5'])
        >>> w.add(o1)
        >>> w.add(o2)
        >>> w.add(o3)

    You can add new objects in the middle of an update.

        >>> orig_move = o2.move
        >>> def my_move(dt):
        ...     orig_move(dt)
        ...     w.add(o4)
        ...     w.add(o5)
        >>> o2.move = my_move
        >>> w.update(1.0)
        Moving o1 for 1.0 time units
        Moving o2 for 1.0 time units
        Moving o3 for 1.0 time units

        >>> w.objects
        [o1, o2, o3, o4, o5]

    You can remove objects in the middle of an update.

        >>> o2.move = orig_move
        >>> orig_move = o3.move
        >>> def my_move(dt):
        ...     orig_move(dt)
        ...     w.remove(o2)
        ...     w.remove(o4)
        >>> o3.move = my_move
        >>> w.update(1.0)
        Moving o1 for 1.0 time units
        Moving o2 for 1.0 time units
        Moving o3 for 1.0 time units
        Moving o4 for 1.0 time units
        Moving o5 for 1.0 time units

        >>> w.objects
        [o1, o3, o5]

    You can even do insane combinations of addition and removal

        >>> def my_move(dt):
        ...     orig_move(dt)
        ...     w.remove(o1)
        ...     w.add(o2)
        ...     w.add(o4)
        ...     w.remove(o2)
        ...     w.add(o1)
        >>> o3.move = my_move
        >>> w.update(1.0)
        Moving o1 for 1.0 time units
        Moving o3 for 1.0 time units
        Moving o5 for 1.0 time units

        >>> w.objects
        [o3, o5, o4, o1]

    """


def doctest_World_collision_detection():
    """Tests for collision detection

        >>> from world import World, Vector
        >>> w = World()

    You can check whether two objects collide.  Collision detection is pretty
    basic, and assumes all objects are circular.

        >>> o1 = Object('o1', radius=1)
        >>> o2 = Object('o2', radius=2)

        >>> o1.distanceTo = lambda o2: 3.5
        >>> w.collide(o1, o2)
        False

        >>> o1.distanceTo = lambda o2: 2.5
        >>> w.collide(o1, o2)
        True

        >>> o1.distanceTo = lambda o2: 3.0
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
