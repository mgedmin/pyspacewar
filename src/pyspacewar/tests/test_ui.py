#!/usr/bin/env python

import unittest
import doctest
import sys
import os


class SurfaceStub(object):

    w = 800
    h = 600

    def get_size(self):
        return (self.w, self.h)


def doctest_Viewport():
    """Tests for Viewport

        >>> from world import Vector
        >>> from ui import Viewport
        >>> viewport = Viewport(SurfaceStub())
        >>> viewport.origin
        Vector(0, 0)
        >>> viewport.scale
        1.0

    To make things more interesting we will set a scale of 0.2 and shift
    the origin to (100, 200)

        >>> viewport.scale = 0.2
        >>> viewport.origin = Vector(100, 200)

    ``screen_len`` converts a length in world units to screen units

        >>> viewport.screen_len(50)
        10
        >>> viewport.screen_len(6)
        1

    ``screen_pos`` converts world coordinates to screen coordinates

        >>> viewport.screen_pos(Vector(100, 200))
        (400, 300)
        >>> viewport.screen_pos(Vector(150, 250))
        (410, 290)
        >>> viewport.screen_pos(Vector(106, 199))
        (401, 300)

    ``world_pos`` converts screen coordinates to world coordinates

        >>> viewport.world_pos((400, 300))
        (100.0, 200.0)
        >>> viewport.world_pos((410, 290))
        (150.0, 250.0)
        >>> viewport.world_pos((401, 300))
        (105.0, 200.0)

    """


def doctest_Viewport_screen_size_change():
    """Tests for Viewport

        >>> from world import Vector
        >>> from ui import Viewport
        >>> viewport = Viewport(SurfaceStub())

    ``screen_pos`` converts world coordinates to screen coordinates

        >>> viewport.screen_pos(Vector(0, 0))
        (400, 300)

    You can change the size of the surface

        >>> viewport.surface.w = 640
        >>> viewport.surface.h = 480
        >>> viewport.surface_size_changed()

        >>> viewport.screen_pos(Vector(0, 0))
        (320, 240)

    """


def doctest_Viewport_keep_visible():
    """Tests for Viewport.keep_visible.

        >>> from world import Vector
        >>> from ui import Viewport
        >>> viewport = Viewport(SurfaceStub())

    Points that are already visible change nothing

        >>> viewport.keep_visible([Vector(0, 0)], 10)
        >>> viewport.keep_visible([Vector(100, 100)], 10)
        >>> viewport.keep_visible([Vector(-200, -100)], 10)
        >>> print viewport.origin, viewport.scale
        (0.000, 0.000) 1.0

    We can see the range of points that are inside the view margin, for
    a given margin size

        >>> viewport.world_inner_bounds(0)
        (-400.0, -300.0, 400.0, 300.0)
        >>> viewport.world_inner_bounds(10)
        (-390.0, -290.0, 390.0, 290.0)

    Points that are off-screen cause scrolling

        >>> viewport.keep_visible([Vector(600, 200)], 10)
        >>> print viewport.origin, viewport.scale
        (210.000, 0.000) 1.0

        >>> viewport.keep_visible([Vector(300, 700)], 10)
        >>> print viewport.origin, viewport.scale
        (210.000, 410.000) 1.0

        >>> viewport.keep_visible([Vector(-300, -100)], 10)
        >>> print viewport.origin, viewport.scale
        (90.000, 190.000) 1.0

        >>> viewport.world_inner_bounds(10)
        (-300.0, -100.0, 480.0, 480.0)

    If you specify several widely-separated points, they may cause a scale
    change

        >>> viewport.keep_visible([Vector(-300, -100),
        ...                        Vector(500, 400)], 10)

        >>> print viewport.origin, round(viewport.scale, 3)
        (99.732, 190.000) 0.974

        >>> xmin, ymin, xmax, ymax = viewport.world_inner_bounds(10)
        >>> xmin <= -300 and 500 <= xmax
        True
        >>> ymin <= -100 and 400 <= ymax
        True

    """


def doctest_FrameRateCounter_frame():
    """Tests for FrameRateCounter.frame

        >>> from ui import FrameRateCounter
        >>> frc = FrameRateCounter()

        >>> frc.frame()
        >>> len(frc.frames)
        1
        >>> frc.frame()
        >>> len(frc.frames)
        2

        >>> frc.frames = range(frc.avg_last_n_frames - 1)
        >>> frc.frame()
        >>> len(frc.frames) == frc.avg_last_n_frames
        True
        >>> frc.frame()
        >>> len(frc.frames) == frc.avg_last_n_frames
        True
        >>> frc.frame()
        >>> len(frc.frames) == frc.avg_last_n_frames
        True

        >>> frc.frames[:3]
        [2, 3, 4]

    """


def doctest_FrameRateCounter_reset():
    """Tests for FrameRateCounter.reset

        >>> from ui import FrameRateCounter
        >>> frc = FrameRateCounter()
        >>> frc.frames = range(15)
        >>> frc.reset()
        >>> frc.frames
        []

    """


def doctest_FrameRateCounter_fps():
    """Tests for FrameRateCounter.fps

        >>> from ui import FrameRateCounter
        >>> frc = FrameRateCounter()
        >>> frc.frames = []
        >>> frc.fps()
        0

        >>> frc.frames = [1000]
        >>> frc.fps()
        0

        >>> frc.frames += [1005]

    5 ms per frame corresponds to 200 frames per second.

        >>> frc.fps()
        200.0

        >>> frc.frames += [1020]

    The first frame took 5 ms, the next one 15 ms.  Average is 10 ms per frame,
    and this corresponds to 100 frames per second.

        >>> frc.fps()
        100.0

    """


def setUp(test=None):
    import pygame
    pygame.init() # so that pygame.key.name() works
    # unfortunately, on linux, if $DISPLAY is unset, pygame.init doesn't
    # complain, but pygame.key.name() returns 'unknown key' for all keys


def test_suite():
    path = os.path.join(os.path.dirname(__file__), os.path.pardir)
    if path not in sys.path:
        sys.path.append(path)
    return unittest.TestSuite([
                        doctest.DocTestSuite('ui', setUp=setUp),
                        doctest.DocTestSuite()])


if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
