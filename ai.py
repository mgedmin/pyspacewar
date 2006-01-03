"""
Ship artificial intelligence.

TODO: write unit tests and refactor this module.
      (I tried refactoring without tests, and broke the code horribly.)
"""

import random

from world import Ship


def length(vector):
    # temporary compatibility function
    return vector.length()

def length_sq(vector):
    # temporary compatibility function
    return vector.length() ** 2


class AIController(object):
    """AI for a ship."""

    def __init__(self, ship):
        self.ship = ship
        self.last_l_r = 1
        self.enemy = None

    def chooseEnemy(self):
        enemy = self.enemy
        if enemy is not None and enemy.dead:
            enemy = None
        if enemy is not None:
            dist_to_enemy = length_sq(enemy.position - self.ship.position)
        else:
            dist_to_enemy = 0
        threshold = 50 ** 2
        for ship in self.ship.world.objects:
            if not isinstance(ship, Ship):
                continue
            if ship is self.ship or ship is self.enemy or ship.dead:
                continue
            dist = length_sq(ship.position - self.ship.position)
            if enemy is None or dist < dist_to_enemy - threshold:
                enemy = ship
        return enemy

    def control(self):
        if self.ship.dead:
            return
        enemy = self.chooseEnemy()
        self.enemy = enemy
        if enemy is not None:
            self.target(enemy)
        else:
            self.ship.velocity *= 0.95
        self.evade(enemy)

    def target(self, enemy):
        target_vector = enemy.position - self.ship.position
        moving_target_vector = target_vector + enemy.velocity - self.ship.velocity

        l_r = (self.ship.direction_vector[0]*moving_target_vector[1] -
               self.ship.direction_vector[1]*moving_target_vector[0])

        if length_sq(target_vector) < 2500:
            turn_const = 10
            thrust_const = 0
        else:
            turn_const = 2
            thrust_const = 1

        if l_r > 0:
            if self.last_l_r < 0:
                self.maybe_fire(enemy, length(target_vector))
            self.ship.left_thrust = random.randrange(turn_const, turn_const + 5)
            self.ship.right_thrust = 0
        else:
            if self.last_l_r > 0:
                self.maybe_fire(enemy, length(target_vector))
            self.ship.left_thrust = 0
            self.ship.right_thrust = random.randrange(turn_const, turn_const + 5)

        rel_velocity = length(self.ship.velocity - enemy.velocity)
        if rel_velocity < 3:
            rel_velocity = 3
        if length_sq(self.ship.velocity) < random.randrange(int(rel_velocity * 0.8), int(rel_velocity * 1.5) + 1) + 1:
            self.ship.forward_thrust = 1 * thrust_const
            self.ship.rear_thrust = 0
        else:
            self.ship.velocity *= 0.95

        self.last_l_r = l_r

    def evade(self, enemy):
        if enemy is not None and not enemy.dead:
            do_not_evade = enemy
        else:
            do_not_evade = None
        planet = self.getClosestToObject(self.ship, ignore=do_not_evade)
        if not planet:
            return

        evade_vector = planet.position - self.ship.position
        moving_target_vector = evade_vector - self.ship.velocity

        l_r = (self.ship.direction_vector[0]*moving_target_vector[1] -
               self.ship.direction_vector[1]*moving_target_vector[0])

        evade_vector_length = length(evade_vector)
        evade_factor = 1

        if evade_vector_length < 100:
            if l_r < 0:
                self.ship.left_thrust = evade_factor
                self.ship.right_thrust = 0
            else:
                self.ship.right_thrust = evade_factor
                self.ship.left_thrust = 0
        else:
            if l_r < 0:
                self.ship.left_thrust += evade_factor
            else:
                self.ship.right_thrust += evade_factor

    def getClosestToObject(self, what, ignore=None):
        distance = 90000 # cutoff, 300 ** 2
        closest = None
        for obj in self.ship.world.objects:
            if obj.radius == 0:
                continue
            if obj is self.ship:
                continue
            if obj is ignore:
                continue
            dst = length_sq(what.position - obj.position)
            if dst < distance:
                closest = obj
                distance = dst
        return closest

    def maybe_fire(self, enemy, distance):
        if not enemy.dead:
            if 0 == random.randrange(0, int(distance / 30) + 1):
                self.ship.launch()
