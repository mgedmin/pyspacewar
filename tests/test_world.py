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
        >>> o.world is w
        True

    You can remove objects

        >>> w.remove(o)
        >>> w.objects
        []
        >>> o.world is None
        True

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

        >>> o5.world is w
        True

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
        [o1, o3, o5, o4]

        >>> o1.world is w
        True
        >>> o2.world is None
        True
        >>> o4.world is w
        True

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


def doctest_Ship_direction():
    """Tests for Ship.direction property.

        >>> from world import Ship, Vector
        >>> ship = Ship(Vector(0, 0), size=10, direction=45)
        >>> ship.direction
        45

        >>> ship.direction -= 90
        >>> ship.direction
        315
        >>> print ship.direction_vector
        (0.707, -0.707)

        >>> ship.direction += 45
        >>> ship.direction
        0
        >>> print ship.direction_vector
        (1.000, 0.000)

    """


def doctest_Ship_controls():
    """Tests for Ship.turn_left, turn_right, accelerate, backwards.

        >>> from world import Ship
        >>> ship = Ship()
        >>> ship.left_thrust, ship.right_thrust
        (0, 0)
        >>> ship.forward_thrust, ship.rear_thrust
        (0, 0)

    You can tell the ship what to do

        >>> ship.turn_right()
        >>> print ship.left_thrust, ship.right_thrust
        0 5

    You can do several things simultaneously

        >>> ship.accelerate()
        >>> print ship.left_thrust, ship.right_thrust
        0 5
        >>> print ship.forward_thrust, ship.rear_thrust
        0.1 0

        >>> ship.turn_left()
        >>> print ship.left_thrust, ship.right_thrust
        5 5
        >>> print ship.forward_thrust, ship.rear_thrust
        0.1 0

        >>> ship.backwards()
        >>> print ship.left_thrust, ship.right_thrust
        5 5
        >>> print ship.forward_thrust, ship.rear_thrust
        0.1 0.05

    These commands are remembered and executed when you call ``move``, not
    immediatelly.

        >>> ship.velocity
        Vector(0, 0)
        >>> ship.direction
        0

    You cannot control a dead ship

        >>> ship = Ship()
        >>> ship.dead = True

        >>> ship.accelerate()
        >>> ship.backwards()
        >>> ship.turn_left()
        >>> ship.turn_right()
        >>> print ship.left_thrust, ship.right_thrust
        0 0
        >>> print ship.forward_thrust, ship.rear_thrust
        0 0

    """


def doctest_Ship_movement():
    """Tests for Ship.move.

        >>> from world import Ship, Vector
        >>> ship = Ship(Vector(0, 0), size=10, direction=45)
        >>> ship.left_thrust = 10
        >>> ship.right_thrust = 5
        >>> ship.forward_thrust = 8
        >>> ship.rear_thrust = 2

        >>> ship.move(1.0)
        >>> ship.direction
        50.0
        >>> ship.velocity.length()
        6.0
        >>> ship.velocity.direction()
        50.0
        >>> print ship.position
        (3.857, 4.596)

        >>> ship.left_thrust, ship.right_thrust
        (0, 0)
        >>> ship.forward_thrust, ship.rear_thrust
        (0, 0)

    """


def doctest_Ship_gravity():
    """Tests for Ship.gravitate.

        >>> from world import Ship, Planet, World, Vector
        >>> ship = Ship()
        >>> ship.world = World()
        >>> sun = Planet(position=Vector(10, 15), mass=200)

    Ships come with equipped with anti-gravity engines

        >>> ship.gravitate(sun, 1.0)
        >>> ship.velocity
        Vector(0, 0)

    When a ship is killed, the engine stops working

        >>> ship.dead = True
        >>> ship.gravitate(sun, 1.0)
        >>> print ship.velocity
        (0.003, 0.005)

    """

def doctest_Ship_collision():
    """Tests for Ship.collision.

        >>> from world import Ship, Vector, Planet, Debris, Missile, World
        >>> ship = Ship(position=Vector(3, 5), velocity=Vector(10, 10))
        >>> ship.world = World()

    Debris is easily deflected

        >>> ship.collision(Debris())
        >>> print ship.health
        1.0

    Missiles cause more damage, but no bouncing

        >>> ship.collision(Missile())
        >>> print ship.health
        0.4
        >>> print ship.velocity
        (10.000, 10.000)

    Other objects cause slight damage and bouncing

        >>> ship.collision(Planet())
        >>> print ship.health
        0.35
        >>> print ship.velocity
        (-3.706, -12.176)

    When health falls under 0, the ship dies

        >>> def croak(who):
        ...     print "Ship died"
        >>> ship.die = croak

        >>> ship.collision(Missile())
        Ship died
        >>> print ship.health
        -0.25

    A ship can die only once

        >>> ship.dead = True
        >>> ship.collision(Missile())
        >>> print ship.health
        -0.85

    """


def doctest_Ship_death():
    """Tests for Ship.die.

        >>> from world import Ship, World

    A ship can die from natural causes

        >>> ship = Ship()
        >>> ship.world = World()
        >>> ship.die(None)
        >>> ship.dead
        True
        >>> ship.frags
        -1

    or from stupidity

        >>> ship = Ship()
        >>> ship.world = World()
        >>> ship.die(ship)
        >>> ship.dead
        True
        >>> ship.frags
        -1

    or be killed by another ship

        >>> ship = Ship()
        >>> ship.world = World()
        >>> attacker = Ship()
        >>> ship.die(attacker)
        >>> ship.dead
        True
        >>> ship.frags
        0
        >>> attacker.frags
        1

    A dying ship leaves some debris behind

        >>> len(ship.world.objects) > 1
        True

    """


def doctest_Ship_launch():
    """Tests for Ship.launch.

        >>> from world import Ship, Vector, World
        >>> ship = Ship(velocity=Vector(10, 20), direction=90)
        >>> ship.world = World()
        >>> ship.launch()

        >>> len(ship.world.objects)
        1
        >>> missile, = ship.world.objects
        >>> missile.velocity
        Vector(10.0, 23.0)

    Dead ships launch no missiles

        >>> ship.dead = True
        >>> ship.launch()
        >>> len(ship.world.objects)
        1

    """


def doctest_Missile_movement():
    """Tests for Missile.move.

        >>> from world import Missile, Vector, World
        >>> missile = Missile(velocity=Vector(1, 0), time_limit=3)
        >>> world = World()
        >>> world.add(missile)

        >>> missile.move(1.0)
        >>> missile.position
        Vector(1.0, 0.0)
        >>> missile.move(1.0)
        >>> missile.position
        Vector(2.0, 0.0)
        >>> missile in world.objects
        True
        >>> missile.time_limit
        1.0

    When the time limit expires, the missile self-destructs

        >>> missile.move(1.5)
        >>> missile.position
        Vector(3.5, 0.0)

        >>> missile in world.objects
        False

    """


def doctest_Missile_explode():
    """Tests for Missile.explode.

        >>> from world import Missile, World
        >>> missile = Missile()
        >>> world = World()
        >>> world.add(missile)

    When a missile hits something, it explodes and leaves some debris behind.

        >>> missile.explode()
        >>> missile in world.objects
        False
        >>> len(world.objects) > 0
        True

    """


def doctest_Object_add_debris():
    """Tests for Object.add_debris.

        >>> from world import Object, World, Debris, Vector
        >>> missile = Object(Vector(100, 200), velocity=Vector(50, -20))
        >>> missile.world = World()
        >>> missile.add_debris(time=5.0, maxdistance=3.0)

        >>> len(missile.world.objects) > 2
        True
        >>> for obj in missile.world.objects:
        ...     assert isinstance(obj, Debris)
        ...     assert (obj.velocity - missile.velocity * 0.3).length() <= 3.0
        ...     assert obj.position == missile.position
        ...     assert obj.time_limit == 5.0

    """


def doctest_Debris():
    """Tests for Debris.

        >>> from world import Debris, Vector, World
        >>> junk = Debris(velocity=Vector(1, 0), time_limit=3)
        >>> world = World()
        >>> world.add(junk)

        >>> junk.move(1.0)
        >>> junk.position
        Vector(1.0, 0.0)
        >>> junk.move(1.0)
        >>> junk.position
        Vector(2.0, 0.0)
        >>> junk in world.objects
        True
        >>> junk.time_limit
        1.0

    When the time limit expires, the debris disappears

        >>> junk.move(1.5)
        >>> junk.position
        Vector(3.5, 0.0)

        >>> junk in world.objects
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
