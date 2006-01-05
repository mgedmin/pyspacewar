#!/usr/bin/env python
"""
PySpaceWar benchmarks for optimisation work
"""

import sys
import time
import random
import optparse

import pygame
from pygame.locals import *

from game import Game
from world import Ship
from ai import AIController
from ui import GameUI


class DummyAIController(object):

    def __init__(self, ship):
        self.ship = ship

    def control(self):
        if self.ship.appearance % 2:
            self.ship.turn_left()
        else:
            self.ship.turn_right()
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
    min_objects = sys.maxint
    total_objects = 0
    best_time = sys.maxint
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


def benchmark_logic(seed=None, how_long=100, ai_controller=DummyAIController,
                    warmup=0):
    game = Game.new(ships=2, rng=random.Random(seed))
    game.time_source = DummyTimeSource()
    ships = [obj for obj in game.world.objects if isinstance(obj, Ship)]
    game.controllers += map(ai_controller, ships)
    game.wait_for_tick() # first one does nothing serious
    for n in range(warmup):
        game.wait_for_tick()
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
    stats.time = now - start
    return stats


def benchmark_ui(seed=None, how_long=100, ai_controller=DummyAIController,
                 warmup=0):
    ui = GameUI()
    ui.rng = random.Random(seed)
    ui.init()
    for player_id, is_ai in enumerate(ui.ai_controlled):
        if is_ai:
            ui.toggle_ai(player_id)
    game = ui.game
    game.time_source = DummyTimeSource()
    game.controllers += map(ai_controller, ui.ships)
    game.wait_for_tick() # first one does nothing serious
    for n in range(warmup):
        ui.wait_for_tick()
        ui.draw()
        event = pygame.event.poll()
        if (event.type == QUIT or
            (event.type == KEYDOWN and event.key in (K_ESCAPE, K_q))):
            how_long = 0
            break
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
        event = pygame.event.poll()
        if (event.type == QUIT or
            (event.type == KEYDOWN and event.key in (K_ESCAPE, K_q))):
            break
    stats.time = now - start
    return stats


def main():
    parser = optparse.OptionParser()
    parser.add_option('-s', '--seed', default=0,
                      help='specify random seed [default: %default]',
                      action='store', dest='seed', type='int')
    parser.add_option('-t', '--ticks', default=100,
                      help='specify number of game ticks [default: %default]',
                      action='store', dest='ticks', type='int')
    parser.add_option('-w', '--warmup', default=0,
                      help='warm up for a number of ticks [default: %default]',
                      action='store', dest='warmup', type='int')
    parser.add_option('-a', '--ai', default=DummyAIController,
                      help='use real AI logic [default: dumb logic]',
                      action='store_const', const=AIController,
                      dest='ai_controller')
    parser.add_option('-g', '--gui', default=benchmark_logic,
                      help='benchmark drawing and logic [default: just logic]',
                      action='store_const', const=benchmark_ui,
                      dest='benchmark')
    parser.add_option('-p', '--profile', default=False,
                      help='enable profiling [default: %default]',
                      action='store_true', dest='profile')
    parser.add_option('--psyco', default=False,
                      help='use Psyco [default: %default]',
                      action='store_true', dest='psyco')
    opts, args = parser.parse_args()
    print "=== Parameters ==="
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
    print 'warmup: %d' % opts.warmup
    print 'ai: %s' % opts.ai_controller.__name__
    print 'benchmark: %s' % opts.benchmark.__name__
    if opts.profile:
        from profile import Profile
        profiler = Profile()
        stats = profiler.runcall(opts.benchmark, opts.seed, opts.ticks,
                                 opts.ai_controller, opts.warmup)
    else:
        profiler = None
        stats = opts.benchmark(opts.seed, opts.ticks, opts.ai_controller,
                               opts.warmup)
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

    if profiler is not None:
        from pstats import Stats
        stats = Stats(profiler)
        stats.strip_dirs()
        print
        print "== Stats by internal time ==="
        print
        stats.sort_stats('time', 'calls')
        stats.print_stats(40)
        print
        print "== Stats by cumulative time ==="
        print
        stats.sort_stats('cumulative', 'calls')
        stats.print_callees(25)

if __name__ == '__main__':
    main()
