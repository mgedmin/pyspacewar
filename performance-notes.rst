Notes on performance
====================

The game runs reasonably fast (although not as fast as I'd like) on my 1.6 GHz
Pentium M laptop.

There's a benchmark that helps measure progress if you're doing optimisation
work.  You can either benchmark game logic only (default if you run
benchmark.py with no parameters), or logic + gui (run benchmark.py -g).

The benchmark can run the profiler for you to help identify hot spots
(benchmark.py -p).  The benchmark can also show some timings it collects
manually (benchmark -d).


Current status
--------------

The benchmark performs at about 18 fps on average on my laptop.  The worst
frame rendering time is 64 ms which translates to 15 fps.  Actual gameplay
nearly always slows down to 10 fps when there are many missiles floating
around.


Goal
----

I would very much like the game to perform at 20 fps constantly, even when
there are 20 planets and 100 missiles, each with a trail 100 positions long.


Current profile data
--------------------

This section may become obsolete without further notice; look at the profile
results for most recent data.

According to the profile data produced by the benchmark, 62% of running time is
spent updating the game world, and 38% drawing things on screen.

Most of the update time is spent calculating gravitational forces (28% total
time or 45% update time) and performing collision detection (15% total time or
25% update time).

70% of draw time (26% total time) is spent drawing missile trails.

Overview::

  Total time                                        100%  ====================
    Update time (GameUI.wait_for_tick)               62%  ============
      Gravitation (Object.gravitate)                 28%  ======
      Collision detection (World.colllide)           15%  ===
      Other                                          19%  ====
    Draw time (GameUI.draw)                          38%  ========
      Missile trails (GameUI.draw_missile_trail)     26%  =====
      Other                                          12%  ==

The biggest hotspots (largest internal time) are::

  Object.gravitate                        16% total time  ================
  UI.draw_missile_trail                   12% total time  ============
  World.update                             9% total time  =========
  Vector.__new__                           7% total time  =======
  Viewport.screen_pos                      7% total time  =======
  World.collide                            7% total time  =======
  pygame.Surface.set_at                    7% total time  =======
  math.hypot                               6% total time  ======
  World.distance_to                        6% total time  ======
  tuple.__new__                            4% total time  ====

The most often called functions are::

  math.hypot                                258130 calls  ====================
  Viewport.screen_pos                       174147 calls  =============
  pygame.Surface.set_at                     173247 calls  =============
  Vector.__new__                            149736 calls  ===========
  tuple.__new__                             149736 calls  ===========
  World.collide                             141018 calls  ==========
  Object.distance_to                        141018 calls  ==========
  Object.gravitate                          110874 calls  ========
  Vector.x property                          50504 calls  ===
  Vector.y property                          50504 calls  ===

Note that timings shown by the benchmark show a slightly different result --
according to them, update takes 17--20 ms, while draw takes 30--40 ms (and
draw_missile_trails 20--30 ms).  I think many thousands of function calls
inside World.update skew the profiler results.


Optimizing missile trails
-------------------------

Some back-of-the-napkin calculations: when the benchmark reaches 6000 trail
points, draw_trail time reaches 25 ms.  That's about 4.1 µs per pixel.
Python's timeit claims that Viewport.screen_pos takes 3.1 µs, and that
pygame.Surface.set_at takes 0.95 µs.

If instead of calling screen_pos in a loop I introduce a list_of_screen_pos
method, which takes a list of 80 points and returns 80 pairs of coordinates,
the timing decreases to 2.2 µs per point.

If I remove trail gradients and instead draw all trail pixels in one color, I
can reduce draw_trail time for those 6000 pixels down to 20 ms (a 5 ms win).

Hey, if I psyco.bind(Viewport.draw_trail) then trail drawing time goes from 25
ms to 17 ms!


Ideas
-----

Rewrite the Vector class in a C extension module (maybe use Pyrex).

Implement Viewport.screen_pos in a C extension module.

Implement World.collide/Object.distance_to/Object.gravitate in C code.

Use a mutable Vector class instead of creating thousands of new objects.

Implement a better collision detection algorithm.


Dead ends
---------

Using pygame.surfarray to plot pixels manually (instead of set_at) slowed
things down.

Generating a list of massive objects instead of checking the mass every time in
World.update failed to produce any noticeable difference.

Rewriting all vector operations to use [0] and [1] instead of .x and .y (to
avoid calling lambdas thousands of times) failed to produce any noticeable
difference.

Checking whether a missile trail point was visible with Viewport.in_screen (to
avoid calling Viewport.screen_pos and Surface.set_at) slowed things down for
the benchmark.  Granted, in the benchmark, most of the missiles are always
on-screen.


Successful optimisations
------------------------

  Somewhere during the last changes (missile recoil?  menus?  detailed
  timings?) I lost 2 fps, so the average now is 18, not 20.

Manually inlining method calls in Object.distance_to (18.4 -> 20.5 average fps).

Manually inlining method calls in Object.gravitate (14.7 -> 18.4 average fps).

Getting rid of in_screen inside draw_missile_trail (13.8 -> 14.7 average fps).

Binding object attributes to local variables inside draw_missile_trail (13.0 ->
13.8 average fps).

Using vector[0/1] instead of vector.x/y in screen_pos and in_screen (11 fps ->
13 fps).

Collision detection: consider only those pairs of objects (a, b) where a.radius
> 0 or b.radius > 0 (35% improvement in update time).

Avoiding special cases in Vector.__new__, and using vector[0/1] instead of
vector.x/y in Vector.__sub__ (25% improvement in worst-case update time).

