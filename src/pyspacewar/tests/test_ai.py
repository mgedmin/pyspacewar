#!/usr/bin/env python

import unittest
import doctest
import sys
import os


def doctest_AIController_chooseEnemy():
    """Tests for AIController.chooseEnemy.

        >>> from ai import AIController
        >>> from world import Ship, World, Object, Vector

    In a world with only two ships

        >>> ship = Ship()
        >>> other = Ship()
        >>> world = World()
        >>> world.add(ship)
        >>> world.add(other)
        >>> world.add(Object())

    the other ship is your enemy

        >>> ai = AIController(ship)
        >>> ai.chooseEnemy() is other
        True

    If there are several enemy ships, let's engage the closest one

        >>> third = Ship()
        >>> world.add(third)
        >>> ship.position = Vector(10, 10)
        >>> other.position = Vector(-10, 5)
        >>> third.position = Vector(10, 15)
        >>> ai.chooseEnemy() is third
        True

    but if we already have an enemy, keep after it

        >>> ai.enemy = other
        >>> ai.chooseEnemy() is other
        True

    unles it goes too far away

        >>> other.position = Vector(-50, -50)
        >>> ai.chooseEnemy() is third
        True

    If the closest enemy is already dead, switch to a live one

        >>> ai.enemy = third
        >>> third.dead = True
        >>> ai.chooseEnemy() is other
        True

    """


def test_suite():
    path = os.path.join(os.path.dirname(__file__), os.path.pardir)
    if path not in sys.path:
        sys.path.append(path)
    return doctest.DocTestSuite()


if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
