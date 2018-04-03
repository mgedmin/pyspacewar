"""
Ship artificial intelligence.

Written by Ignas Mikalajunas.
"""

from .world import Ship


class AIController(object):
    """AI for a ship."""

    def __init__(self, ship):
        self.ship = ship
        self.rng = ship.world.rng
        self.last_l_r = 1
        self.enemy = None

    def choose_enemy(self):
        enemy = self.enemy
        if enemy is not None and enemy.dead:
            enemy = None
        if enemy is not None:
            dist_to_enemy = self.ship.distance_to(enemy)
        else:
            dist_to_enemy = 1e999
        threshold = 50
        for ship in self.ship.world.objects:
            if not isinstance(ship, Ship):
                continue
            if ship is self.ship or ship is self.enemy or ship.dead:
                continue  # pragma: nocover because peephole optimizer :/
            dist = self.ship.distance_to(ship)
            if enemy is None or dist < dist_to_enemy - threshold:
                enemy = ship
        return enemy

    def control(self):
        if self.ship.dead:
            return
        enemy = self.choose_enemy()
        self.enemy = enemy
        if enemy is not None:
            self.target(enemy)
        else:
            self.ship.brake()
        self.evade(enemy)

    def target(self, enemy):
        target_vector = enemy.position - self.ship.position
        moving_target_vector = (
            target_vector + enemy.velocity - self.ship.velocity)

        l_r = self.ship.direction_vector.cross_product(moving_target_vector)

        if target_vector.length() < 50:
            turn_const = 10
            thrust_const = 0
        else:
            turn_const = 2
            thrust_const = 1

        if l_r > 0:
            if self.last_l_r < 0:
                self.maybe_fire(enemy, target_vector.length())
            self.ship.left_thrust = self.rng.randrange(turn_const,
                                                       turn_const + 5)
            self.ship.right_thrust = 0
        else:
            if self.last_l_r > 0:
                self.maybe_fire(enemy, target_vector.length())
            self.ship.left_thrust = 0
            self.ship.right_thrust = self.rng.randrange(turn_const,
                                                        turn_const + 5)

        rel_velocity = (self.ship.velocity - enemy.velocity).length()
        if rel_velocity < 3:
            rel_velocity = 3
        limit_squared = self.rng.randrange(int(rel_velocity * 0.8),
                                           int(rel_velocity * 1.5) + 1)
        if self.ship.velocity.length() ** 2 < limit_squared + 1:
            self.ship.forward_thrust = 1 * thrust_const
            self.ship.rear_thrust = 0
        else:
            self.ship.brake()

        self.last_l_r = l_r

    def evade(self, enemy):
        if enemy is not None and not enemy.dead:
            do_not_evade = enemy
        else:
            do_not_evade = None
        planet = self.get_closest_obstacle(self.ship, ignore=do_not_evade)
        if not planet:
            return

        evade_vector = planet.position - self.ship.position
        moving_target_vector = evade_vector - self.ship.velocity

        l_r = self.ship.direction_vector.cross_product(moving_target_vector)

        evade_vector_length = evade_vector.length()
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

    def get_closest_obstacle(self, what, ignore=None):
        distance = 300  # cutoff
        closest = None
        for obj in self.ship.world.objects:
            if obj.radius == 0:
                continue
            if obj is self.ship:
                continue
            if obj is ignore:
                continue
            dst = what.distance_to(obj)
            if dst < distance:
                closest = obj
                distance = dst
        return closest

    def maybe_fire(self, enemy, distance):
        if not enemy.dead:
            if 0 == self.rng.randrange(0, int(distance / 30) + 1):
                self.ship.launch()
