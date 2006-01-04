"""
PySpaceWar game logic
"""

import time
import random

from world import World, Vector, Ship, Planet


class PythonTimeSource(object):
    """A ticking clock based on time.time."""

    def __init__(self, ticks_per_second):
        self.ticks_per_second = ticks_per_second
        self.delta = 1.0 / ticks_per_second

    def now(self):
        """Return the current time."""
        return time.time()

    def wait(self, time_point):
        """Wait until now() becomes >= time_point.

        Returns True if we're on schedule; False if time_point was already
        past when ``wait`` was called.
        """
        time_to_sleep = time_point - self.now()
        if time_to_sleep > 0:
            time.sleep(time_to_sleep)
        return time_to_sleep >= 0


class Game(object):
    """A game.

    Example:

        g = Game.new(ships=2, planet_kinds=3)
        while True:
            g.wait_for_tick()
            # interact with game objects
            # draw the state of the game

    """

    TICKS_PER_SECOND = 20               # Number of game ticks per second
    DELTA_TIME = 2.0                    # World time units per game tick
    ROTATION_SPEED = 10 / DELTA_TIME    # Rotation angle per time unit
    FRONT_THRUST = 0.2 / DELTA_TIME     # Forward acceleration
    REAR_THRUST = 0.1 / DELTA_TIME      # Backward acceleration

    respawn_radius = 600                # Locale for respawning ships
    respawn_time = 100                  # Time before a dead ship respawns

    def __init__(self, rng=None):
        if rng is None:
            rng = random.Random()
        self.rng = rng
        self.world = World(rng)
        self.ships = []
        self.timers = {}
        self.time_source = PythonTimeSource(self.TICKS_PER_SECOND)
        self._next_tick = None
        self.controllers = []

    def randomly_position(self, obj, world_radius):
        """Pick a random location for ``obj``."""
        while True:
            obj.position = Vector.from_polar(self.rng.uniform(0, 360),
                                             self.rng.uniform(0, world_radius))
            for other in self.world.objects:
                if other is not obj and self.world.collide(obj, other):
                    break
            else:
                break
            world_radius *= 1.1

    def randomly_place(self, obj, world_radius):
        """Place ``obj`` in a randomly chosen location."""
        self.randomly_position(obj, world_radius)
        self.world.add(obj)
        if isinstance(obj, Ship):
            self.ships.append(obj)

    def respawn(self, ship):
        """Respawn a ship."""
        self.randomly_position(ship, self.respawn_radius)
        ship.velocity = Vector(0, 0)
        granularity = self.ROTATION_SPEED
        ship.direction = self.rng.randrange(360 / granularity) * granularity
        ship.respawn()

    def auto_respawn(self):
        """Respawn dead ships after a timeout."""
        for ship in self.ships:
            if ship.dead:
                if ship not in self.timers:
                    self.timers[ship] = self.respawn_time
                else:
                    self.timers[ship] -= self.DELTA_TIME
                    if self.timers[ship] <= 0:
                        del self.timers[ship]
                        self.respawn(ship)

    def time_to_respawn(self, ship):
        """Return the time left before a dead ship will respawn.

        Returns 0 if the ship is not dead.
        """
        return self.timers.get(ship, 0)

    def wait_for_tick(self):
        """Wait for the next game time tick."""
        if self._next_tick is None: # first time!
            self._next_tick = self.time_source.now() + self.time_source.delta
            on_schedule = True
        else:
            self.world.update(self.DELTA_TIME)
            self.auto_respawn()
            for controller in self.controllers:
                controller.control()
            on_schedule = self.time_source.wait(self._next_tick)
            self._next_tick += self.time_source.delta
        return on_schedule

    def new(cls, ships=2, planet_kinds=1, world_radius=1200,
            ship_start_radius=600, rng=None):
        """Create a new random game."""
        game = cls(rng)
        game.respawn_radius = ship_start_radius
        rng = game.rng
        n_planets = rng.randrange(2, 20)
        for n in range(n_planets):
            appearance = rng.randrange(planet_kinds)
            radius = rng.uniform(5, 40)
            mass = radius ** 3 * rng.uniform(2, 6)
            planet = Planet(appearance=appearance, radius=radius, mass=mass)
            game.randomly_place(planet, world_radius)
        for n in range(ships):
            granularity = cls.ROTATION_SPEED
            direction = rng.randrange(360 / granularity) * granularity
            ship = Ship(appearance=n, direction=direction)
            # Install a standard engine
            ship.rotation_speed = cls.ROTATION_SPEED
            ship.forward_power = cls.FRONT_THRUST
            ship.backward_power = cls.REAR_THRUST
            game.randomly_place(ship, ship_start_radius)
        return game

    new = classmethod(new)
