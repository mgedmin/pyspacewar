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
        """Wait until now() becomes >= time_point."""
        time_to_sleep = time_point - self.now()
        if time_to_sleep > 0:
            time.sleep(time_to_sleep)


class Game(object):
    """A game.

    Example:

        g = Game.new(ships=2, planet_kinds=3)
        while True:
            g.wait_for_tick()
            # interact with game objects
            # draw the state of the game

    """

    TICKS_PER_SECOND = 20           # Number of game ticks per second
    DELTA_TIME = 0.2                # World time units per game tick

    def __init__(self, rng=None):
        if rng is None:
            rng = random.Random()
        self.rng = rng
        self.world = World()
        self.time_source = PythonTimeSource(self.TICKS_PER_SECOND)
        self._next_tick = None

    def randomly_place(self, obj):
        """Place ``obj`` in a randomly chosen location."""
        world_radius = 600
        while True:
            obj.position = Vector.from_polar(random.uniform(0, 360),
                                             random.uniform(0, world_radius))
            for other in self.world.objects:
                if self.world.collide(obj, other):
                    break
            else:
                break
            world_radius *= 1.1
        self.world.add(obj)

    def wait_for_tick(self):
        """Wait for the next game time tick."""
        if self._next_tick is None: # first time!
            self._next_tick = self.time_source.now() + self.time_source.delta
        else:
            self.world.update(self.DELTA_TIME)
            self.time_source.wait(self._next_tick)
            self._next_tick += self.time_source.delta

    def new(cls, ships=2, planet_kinds=1, rng=None):
        """Create a new random game."""
        game = Game(rng)
        rng = game.rng
        n_planets = rng.randrange(2, 20)
        for n in range(n_planets):
            appearance = rng.randrange(planet_kinds)
            radius = rng.uniform(5, 40)
            mass = radius ** 3 * rng.uniform(2, 6)
            game.randomly_place(Planet(appearance=appearance,
                                       radius=radius, mass=mass))
        for n in range(ships):
            game.randomly_place(Ship(appearance=n,
                                     direction=rng.randrange(360)))
        return game

    new = classmethod(new)
