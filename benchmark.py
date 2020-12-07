#!/usr/bin/env python
"""
PySpaceWar benchmarks for optimisation work
"""
from __future__ import print_function

import optparse
import os
import random
import sys
import time

import pygame
from pygame.locals import *


def setup_path():
    """Set up python path if running from a source tree."""
    pkgdir = os.path.join(os.path.dirname(__file__), 'src')
    print(pkgdir)
    if os.path.isdir(pkgdir):
        sys.path.insert(0, pkgdir)

setup_path()


from pyspacewar.ai import AIController
from pyspacewar.game import Game
from pyspacewar.ui import GameUI
from pyspacewar.world import Ship


def get_cpu_speed():
    try:
        with open('/proc/cpuinfo') as f:
            rows = [row for row in f if row.startswith('cpu MHz')]
    except IOError:
        return 0
    try:
        return float(rows[0].split(':')[1])
    except IndexError:
        return 0


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
    min_objects = 1e999
    total_objects = 0
    best_time = 1e999
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


class Benchmark(object):

    def __init__(self, seed=None, how_long=100,
                 ai_controller=DummyAIController, warmup_ticks=0,
                 profile=False, debug=False):
        self.seed = seed
        self.how_long = how_long
        self.ai_controller = ai_controller
        self.warmup_ticks = warmup_ticks
        self.profile = profile
        self.debug = debug

    def run(self):
        self.stats = Stats()
        self.init()
        self.stats.cpu_speed_before_warmup = get_cpu_speed()
        self.warmup()
        self.stats.cpu_speed_after_warmup = get_cpu_speed()
        if self.profile:
            from profile import Profile
            profiler = Profile()
            profiler.runcall(self.benchmark)
        else:
            self.benchmark()
        self.stats.cpu_speed_after_benchmark = get_cpu_speed()
        if self.profile:
            import pstats
            self.stats.profile_stats = pstats.Stats(profiler)
        return self.stats

    def warmup(self):
        tick = 0
        while tick < self.warmup_ticks:
            self.cycle()
            tick += 1

    def benchmark(self):
        game = self.game
        stats = self.stats
        start = now = time.time()
        while stats.ticks < self.how_long:
            prev = now
            self.cycle()
            now = time.time()
            stats.ticks += 1
            stats.max_objects = max(stats.max_objects, len(game.world.objects))
            stats.min_objects = min(stats.min_objects, len(game.world.objects))
            stats.total_objects += len(game.world.objects)
            stats.best_time = min(stats.best_time, now - prev)
            stats.worst_time = max(stats.worst_time, now - prev)
            stats.time = now - start


class LogicBenchmark(Benchmark):

    def init(self):
        game = Game.new(ships=2, rng=random.Random(self.seed))
        game.time_source = DummyTimeSource()
        ships = [obj for obj in game.world.objects if isinstance(obj, Ship)]
        game.controllers += map(self.ai_controller, ships)
        game.wait_for_tick() # first one does nothing serious
        self.game = game
        self.cycle = game.wait_for_tick


class GameBenchmark(Benchmark):

    def init(self):
        ui = GameUI()
        ui.rng = random.Random(self.seed)
        ui.show_debug_info = self.debug
        ui.init()
        for player_id, is_ai in enumerate(ui.ai_controlled):
            if is_ai:
                ui.toggle_ai(player_id)
        game = ui.game
        game.time_source = DummyTimeSource()
        game.controllers += map(self.ai_controller, ui.ships)
        game.wait_for_tick() # first one does nothing serious
        self.ui = ui
        self.game = game

    def cycle(self):
        self.ui.wait_for_tick()
        self.ui.draw()
        event = pygame.event.poll()
        if (event.type == QUIT or
            (event.type == KEYDOWN and event.key in (K_ESCAPE, K_q))):
            self.how_long = 0
            self.warmup_ticks = 0


def main():
    parser = optparse.OptionParser()
    parser.add_option('-s', '--seed', default=0,
                      help='specify random seed [default: %default]',
                      action='store', dest='seed', type='int')
    parser.add_option('-t', '--ticks', default=100,
                      help='specify number of game ticks [default: %default]',
                      action='store', dest='ticks', type='int')
    parser.add_option('-w', '--warmup', default=100,
                      help='warm up for a number of ticks [default: %default]',
                      action='store', dest='warmup', type='int')
    parser.add_option('-a', '--ai', default=DummyAIController,
                      help='use real AI logic [default: dumb logic]',
                      action='store_const', const=AIController,
                      dest='ai_controller')
    parser.add_option('-g', '--gui', default=LogicBenchmark,
                      help='benchmark drawing and logic [default: just logic]',
                      action='store_const', const=GameBenchmark,
                      dest='benchmark')
    parser.add_option('-d', '--debug', default=False,
                      help='show debug info during benchmark [default: %default]',
                      action='store_true', dest='debug')
    parser.add_option('-p', '--profile', default=False,
                      help='enable profiling [default: %default]',
                      action='store_true', dest='profile')
    parser.add_option('--psyco', default=False,
                      help='use Psyco [default: %default]',
                      action='store_true', dest='psyco')
    opts, args = parser.parse_args()
    print("=== Parameters ===")
    print()
    if opts.psyco:
        try:
            import psyco
            psyco.full()
        except:
            print('psyco not available')
        else:
            print('using psyco')
    print('random seed: %r' % opts.seed)
    print('warmup: %d' % opts.warmup)
    print('ticks: %d' % opts.ticks)
    print('ai: %s' % opts.ai_controller.__name__)
    print('benchmark: %s' % opts.benchmark.__name__)
    print('debug: %s' % opts.debug)
    benchmark = opts.benchmark(opts.seed, opts.ticks, opts.ai_controller,
                               opts.warmup, opts.profile, opts.debug)
    start_time = time.time()
    stats = benchmark.run()
    total_time = time.time() - start_time
    print()
    print("=== CPU ===")
    print()
    print('CPU speed before warmup: %.0f MHz' % stats.cpu_speed_before_warmup)
    print('CPU speed after warmup: %.0f MHz' % stats.cpu_speed_after_warmup)
    print('CPU speed after benchmark: %.0f MHz' % stats.cpu_speed_after_benchmark)
    print()
    print("=== Results ===")
    print()
    print('total time: %.3f seconds' % total_time)
    print('ticks: %d' % stats.ticks)
    print('objects: min=%d avg=%.1f max=%d' % (
                stats.min_objects,
                stats.avg_objects,
                stats.max_objects))
    print('ticks per second: avg=%.3f' % stats.ticks_per_second)
    print('ms per tick: min=%.3f avg=%.3f max=%.3f' % (
                stats.best_time * 1000.0,
                stats.ms_per_tick,
                stats.worst_time * 1000.0))

    if opts.profile:
        stats = stats.profile_stats
        stats.strip_dirs()
        print()
        print("== Stats by internal time ===")
        print()
        stats.sort_stats('time', 'calls')
        stats.print(_stats(40))
        print()
        print("== Stats by number of calls, with callers ===")
        print()
        stats.sort_stats('calls', 'time')
        stats.print_callers(20)
        print()
        print("== Stats by cumulative time, with calees ===")
        print()
        stats.sort_stats('cumulative', 'calls')
        stats.print_callees(20)

if __name__ == '__main__':
    main()
