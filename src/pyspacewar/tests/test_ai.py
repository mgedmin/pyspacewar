#!/usr/bin/env python


def effect(msg):
    def callback(*args):
        print(msg)
    return callback


def doctest_AIController_choose_enemy():
    """Tests for AIController.choose_enemy.

        >>> from pyspacewar.ai import AIController
        >>> from pyspacewar.world import Ship, World, Object, Vector

    In a world with only two ships

        >>> ship = Ship()
        >>> other = Ship()
        >>> world = World()
        >>> world.add(ship)
        >>> world.add(other)
        >>> world.add(Object())

    the other ship is your enemy

        >>> ai = AIController(ship)
        >>> ai.choose_enemy() is other
        True

    If there are several enemy ships, let's engage the closest one

        >>> third = Ship()
        >>> world.add(third)
        >>> ship.position = Vector(10, 10)
        >>> other.position = Vector(-10, 5)
        >>> third.position = Vector(10, 15)
        >>> ai.choose_enemy() is third
        True

    but if we already have an enemy, keep after it

        >>> ai.enemy = other
        >>> ai.choose_enemy() is other
        True

    unles it goes too far away

        >>> other.position = Vector(-50, -50)
        >>> ai.choose_enemy() is third
        True

    If the closest enemy is already dead, switch to a live one

        >>> ai.enemy = third
        >>> third.dead = True
        >>> ai.choose_enemy() is other
        True

    """


def doctest_AIController_control():
    """Tests for AIController.control.

        >>> from pyspacewar.ai import AIController
        >>> from pyspacewar.world import Ship, World, Vector
        >>> ship = Ship(velocity=Vector(30, 0))
        >>> world = World()
        >>> world.add(ship)
        >>> ai = AIController(ship)

    Not much to do in an empty world.

        >>> ai.control()
        >>> ship.engage_brakes
        True

    But if we find other ships, we can engage them!

        >>> other = Ship(position=Vector(100, 20))
        >>> world.add(other)
        >>> ai.control()

    unless we're dead

        >>> ship.dead = True
        >>> ai.control()

    """


def doctest_AIController_target():
    """Tests for AIController.target.

        >>> from pyspacewar.ai import AIController
        >>> from pyspacewar.world import Ship, World, Vector
        >>> ship = Ship(position=Vector(0, 0))
        >>> other = Ship(position=Vector(10, 20))
        >>> world = World()
        >>> world.add(ship)
        >>> world.add(other)
        >>> ai = AIController(ship)
        >>> ai.maybe_fire = effect('Foom!')

    The AI has to be able to turn the ship towards the enemy

        >>> ai.target(other)
        >>> ship.right_thrust
        0
        >>> ship.left_thrust > 0
        True

    We'll fire when we're turning across the enemy

        >>> ship.direction = 90
        >>> ai.target(other)
        Foom!

        >>> ship.direction = 45
        >>> ai.target(other)
        Foom!

    """


def doctest_AIController_evade():
    """Tests for AIController.evade.

        >>> from pyspacewar.ai import AIController
        >>> from pyspacewar.world import Ship, World, Planet, Vector
        >>> ship = Ship(position=Vector(0, 0))
        >>> other = Ship(position=Vector(10, 20))
        >>> sun = Planet(position=Vector(35, 20), radius=5)
        >>> world = World()
        >>> world.add(ship)
        >>> world.add(other)
        >>> world.add(sun)
        >>> ai = AIController(ship)

    In order not to crash into planets we need to take evasive action
    sometimes.  E.g. the planet is to the left of our path

        >>> ai.evade(other)
        >>> ship.left_thrust
        0
        >>> ship.right_thrust
        1

    and when it's to the right

        >>> ship.direction = 90
        >>> ai.evade(other)
        >>> ship.left_thrust
        1
        >>> ship.right_thrust
        0

    If we're further away from the planet, then we can follow the
    enemy instead of focusing 100% on the planet

        >>> ship.position = Vector(-100, -100)
        >>> ship.direction = 0
        >>> ship.left_thrust = 10
        >>> ship.right_thrust = 0
        >>> ai.evade(other)
        >>> ship.left_thrust
        10
        >>> ship.right_thrust
        1

        >>> ship.direction = 90
        >>> ship.left_thrust = 10
        >>> ship.right_thrust = 0
        >>> ai.evade(other)
        >>> ship.left_thrust
        11
        >>> ship.right_thrust
        0

    """


def doctest_AIController_get_closest_obstacle():
    """Tests for AIController.get_closest_obstacle.

        >>> from pyspacewar.ai import AIController
        >>> from pyspacewar.world import Ship, World, Missile, Planet, Vector
        >>> ship = Ship(position=Vector(30, 0))
        >>> missile = Missile(position=Vector(31, 0))
        >>> sun = Planet(position=Vector(35, 20), radius=5)
        >>> moon = Planet(position=Vector(0, -10), radius=2)
        >>> world = World()
        >>> world.add(ship)
        >>> world.add(missile)
        >>> world.add(sun)
        >>> world.add(moon)
        >>> ai = AIController(ship)

    In order not to crash into planets we need to pay attention

        >>> ai.get_closest_obstacle(ship) is sun
        True

    """


def doctest_AIController_maybe_fire():
    """Tests for AIController.maybe_fire.

        >>> from pyspacewar.ai import AIController
        >>> from pyspacewar.world import Ship, World
        >>> ship = Ship()
        >>> ship.launch_effect = effect('Foom!')
        >>> world = World()
        >>> world.add(ship)
        >>> ai = AIController(ship)

    The AI always fires at very close range

        >>> enemy = Ship()
        >>> ai.maybe_fire(enemy, 10)
        Foom!

    unless the enemy is already dead

        >>> enemy.dead = True
        >>> ai.maybe_fire(enemy, 10)

    """
