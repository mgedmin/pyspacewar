#!/usr/bin/env python


class TimeSourceStub(object):

    delta = 10

    def __init__(self):
        self.counter = 0

    def now(self):
        self.counter += 1
        return self.counter

    def wait(self, time_point):
        print("Waiting for %s" % time_point)
        on_schedule = time_point >= self.counter
        self.counter = max(self.counter, time_point)
        return on_schedule


class Ticker(object):
    """Fake world object."""

    mass = 0
    radius = 0

    def move(self, dt):
        print("Tick (%s)" % dt)


class Controller(object):
    """Fake controller."""

    def control(self):
        print("Controlling the world")


def doctest_PythonTimeSource():
    """Tests for PythonTimeSource

        >>> from pyspacewar.game import PythonTimeSource
        >>> ts = PythonTimeSource(40)
        >>> ts.ticks_per_second
        40
        >>> round(ts.delta * ts.ticks_per_second, 3)
        1.0

    You can get a current timestamp and wait for the future

        >>> back_then = ts.now()
        >>> future = back_then + ts.delta
        >>> ts.wait(future)
        True
        >>> now = ts.now()
        >>> eps = 0.01
        >>> now >= future - eps or 'error: %r < %r' % (now, future)
        True

    You can safely wait for the past

        >>> ts.wait(back_then)
        False

    """


def doctest_Game():
    """Tests for Game

        >>> from pyspacewar.game import Game
        >>> g = Game()
        >>> g.world.objects
        []
        >>> g.time_source.ticks_per_second == Game.TICKS_PER_SECOND
        True

    """


def doctest_Game_randomly_place_and_position():
    """Tests for Game.randomly_place

    Let us create a screaming brick for this test

        >>> from pyspacewar.world import Object
        >>> class Brick(Object):
        ...     def collision(self, other):
        ...         print("Aaaaargh!")

    The game is able to position objects randomly so that they never overlap

        >>> from pyspacewar.game import Game
        >>> g = Game()
        >>> for n in range(100):
        ...     g.randomly_place(Brick(radius=10), 200)
        >>> len(g.world.objects)
        100
        >>> g.world.update(1)

    If you do not want to add the object to the world, use randomly_position
    instead.

        >>> good_place = Brick()
        >>> g.randomly_position(good_place, 100)
        >>> len(g.world.objects)
        100

        >>> g.world.add(good_place)
        >>> g.world.update(1)

    """


def doctest_Game_respawn():
    """Tests for Game.respawn

        >>> from pyspacewar.game import Game
        >>> from pyspacewar.world import Ship, Vector
        >>> g = Game()
        >>> ship = Ship(velocity=Vector(3, 5))
        >>> ship.dead = True

    A dead ship can come back to life in a new randomly selected place

        >>> g.respawn(ship)
        >>> ship.velocity
        Vector(0, 0)
        >>> ship.direction % g.ROTATION_SPEED
        0.0
        >>> ship.position.length() <= g.respawn_radius
        True
        >>> ship.dead
        False
        >>> ship.health
        1.0

    """


def doctest_Game_auto_respawn():
    """Tests for Game.auto_respawn

        >>> from pyspacewar.game import Game
        >>> from pyspacewar.world import Ship
        >>> g = Game()
        >>> ship1 = Ship()
        >>> ship2 = Ship()
        >>> ship2.dead = True
        >>> g.ships = [ship1, ship2]

    The game keeps track of dead ships.

        >>> g.auto_respawn()
        >>> list(g.timers) == [ship2]
        True
        >>> g.timers[ship2] == g.respawn_time
        True

    The timer ticks and ticks

        >>> g.auto_respawn()
        >>> g.timers[ship2] == g.respawn_time - g.DELTA_TIME
        True

    and when it reaches zero, the ship comes back to life

        >>> g.timers[ship2] = g.DELTA_TIME
        >>> g.auto_respawn()
        >>> list(g.timers)
        []
        >>> ship2.dead
        False

    """


def doctest_Game_time_to_respawn():
    """Tests for Game.time_torespawn

        >>> from pyspacewar.game import Game
        >>> from pyspacewar.world import Ship
        >>> g = Game()
        >>> ship = Ship()

    The game keeps track of dead ships, and keeps a respawn timer for each
    of them.

        >>> g.timers[ship] = 17.5

    You can discover the value of the timer by calling time_to_respawn

        >>> g.time_to_respawn(ship)
        17.5

    If there is no timer for a particular ship ('cause it is not dead),
    you will get 0

        >>> del g.timers[ship]
        >>> g.time_to_respawn(ship)
        0

    """


def doctest_Game_skip_a_tick():
    """Tests for Game.skip_a_tick

        >>> from pyspacewar.game import Game
        >>> g = Game()
        >>> ts = g.time_source = TimeSourceStub()
        >>> g.world.add(Ticker())

    When the game is paused, you should inform it by calling the skip_for_tick
    method (so the game won't think the frame rate has dropped and won't start
    compensating).

        >>> g.skip_a_tick()
        >>> g.skip_a_tick()
        Waiting for 11
        >>> g.skip_a_tick()
        Waiting for 22

    The waiting time depends on outside delays

        >>> ts.counter += 5
        >>> g.skip_a_tick()
        Waiting for 33

    """


def doctest_Game_wait_for_tick():
    """Tests for Game.wait_for_tick

        >>> from pyspacewar.game import Game
        >>> g = Game()
        >>> ts = g.time_source = TimeSourceStub()
        >>> g.world.add(Ticker())
        >>> g.controllers.append(Controller())

    Initial call to g.wait_for_tick remembers the current time.  All other
    calls wait the necessary amount.  Each call also causes an update in the
    game world.

        >>> g.wait_for_tick()
        True
        >>> g.wait_for_tick()
        Tick (2.0)
        Controlling the world
        Waiting for 11
        True
        >>> g.wait_for_tick()
        Tick (2.0)
        Controlling the world
        Waiting for 21
        True
        >>> g.wait_for_tick()
        Tick (2.0)
        Controlling the world
        Waiting for 31
        True

    The waiting time is independent of outside delays

        >>> ts.counter += 5
        >>> g.wait_for_tick()
        Tick (2.0)
        Controlling the world
        Waiting for 41
        True
        >>> ts.counter += 105
        >>> g.wait_for_tick()
        Tick (2.0)
        Controlling the world
        Waiting for 51
        False

    After the game world is updated, wait_for_tick also takes care to
    look for dead ships.

        >>> from pyspacewar.world import Ship
        >>> ship = Ship()
        >>> ship.dead = True
        >>> g.ships.append(ship)

        >>> g.wait_for_tick()
        Tick (2.0)
        Controlling the world
        Waiting for 61
        False

        >>> list(g.timers) == [ship]
        True

    """


def doctest_Game_new():
    """Tests for Game.new

        >>> from pyspacewar.game import Game
        >>> g = Game.new(ships=2)
        >>> len(g.ships)
        2

    """
