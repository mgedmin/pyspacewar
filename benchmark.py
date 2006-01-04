"""
PySpaceWar benchmarks for optimisation work
"""

import sys
import time
import random
import optparse

from game import Game
from world import Ship
from ai import AIController
from ui import GameUI


class DummyAIController(object):

    def __init__(self, ship):
        self.ship = ship

    def control(self):
        if len(self.ship.world.objects) < 90:
            self.ship.launch()

class DummyTimeSource(object):

    delta = 0

    def now(self):
        return 0

    def wait(self, time):
        return True


class Stats(object):
    time = 0
    ticks = 0
    max_objects = 0
    min_objects = 1e1000
    total_objects = 0
    best_time = 1e1000
    worst_time = 0

    @property
    def avg_objects(self):
        if self.ticks == 0:
            return 0
        return self.total_objects / float(self.ticks)

    @property
    def ticks_per_second(self):
        if self.time == 0:
            return 0
        return self.ticks / float(self.time)

    @property
    def ms_per_tick(self):
        if self.ticks == 0:
            return 0
        return self.time * 1000.0 / self.ticks


def benchmark_logic(seed=None, how_long=100):
    game = Game.new(ships=2, rng=random.Random(seed))
    game.time_source = DummyTimeSource()
    ships = [obj for obj in game.world.objects if isinstance(obj, Ship)]
    game.controllers += map(DummyAIController, ships)
    game.wait_for_tick() # first one does nothing serious
    stats = Stats()
    start = now = time.time()
    while stats.ticks < how_long:
        prev = now
        game.wait_for_tick()
        now = time.time()
        stats.ticks += 1
        stats.max_objects = max(stats.max_objects, len(game.world.objects))
        stats.min_objects = min(stats.min_objects, len(game.world.objects))
        stats.total_objects += len(game.world.objects)
        stats.best_time = min(stats.best_time, now - prev)
        stats.worst_time = max(stats.worst_time, now - prev)
        for event in pygame.event.get():
            if event.type == QUIT:
                break
            elif event.type == KEYDOWN:
                if event.key in (K_ESCAPE, K_q):
                    break
    stats.time = now - start
    return stats


def benchmark_ui(seed=None, how_long=100):
    ui = GameUI()
    ui.rng = random.Random(seed)
    ui.init()
    for player_id, is_ai in enumerate(ui.ai_controlled):
        if not is_ai:
            ui.toggle_ai(player_id)
    game = ui.game
    game.time_source = DummyTimeSource()
    game.wait_for_tick() # first one does nothing serious
    stats = Stats()
    start = now = time.time()
    while stats.ticks < how_long:
        prev = now
        ui.wait_for_tick()
        ui.draw()
        now = time.time()
        stats.ticks += 1
        stats.max_objects = max(stats.max_objects, len(game.world.objects))
        stats.min_objects = min(stats.min_objects, len(game.world.objects))
        stats.total_objects += len(game.world.objects)
        stats.best_time = min(stats.best_time, now - prev)
        stats.worst_time = max(stats.worst_time, now - prev)
    stats.time = now - start
    return stats


def main():
    parser = optparse.OptionParser()
    parser.add_option('-s', '--seed', default=0, action='store', dest='seed')
    parser.add_option('-g', '--gui', default=benchmark_logic,
                      action='store_const', const=benchmark_ui,
                      dest='benchmark')
    parser.add_option('--psyco', default=False, action='store_true',
                      dest='psyco')
    opts, args = parser.parse_args()
    if opts.psyco:
        try:
            import psyco
            import world
            psyco.full()
        except:
            print 'psyco not available'
        else:
            print 'using psyco'
    print 'random seed: %r' % opts.seed
    stats = opts.benchmark(opts.seed)
    print 'ticks: %d' % stats.ticks
    print 'ticks per second: avg=%.3f' % stats.ticks_per_second
    print 'ms per tick: min=%.3f avg=%.3f max=%.3f' % (
                stats.best_time * 1000.0,
                stats.ms_per_tick,
                stats.worst_time * 1000.0)
    print 'objects: min=%d avg=%.1f max=%d' % (
                stats.min_objects,
                stats.avg_objects,
                stats.max_objects)

if __name__ == '__main__':
    main()
