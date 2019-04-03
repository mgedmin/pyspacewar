#!/usr/bin/env python
from __future__ import print_function

import unittest
import doctest
import sys
import os

import pygame
from pygame.locals import Rect


class SurfaceStub(object):

    w = 800
    h = 600

    def get_width(self):
        return self.w

    def get_height(self):
        return self.h

    def get_size(self):
        return (self.w, self.h)

    def get_rect(self):
        return Rect(0, 0, self.w, self.h)

    def get_bitsize(self):
        return 32


class PrintingSurfaceStub(SurfaceStub):

    def set_at(self, pos, color):
        x, y = pos
        r, g, b = color
        print("(%s, %s) <- #%02x%02x%02x" % (x, y, r, g, b))

    def blit(self, what, pos):
        x, y = pos
        print("(%s, %s) <- %r" % (x, y, what))

    def fill(self, color, rect):
        x, y, w, h = rect
        r, g, b = color
        print("(%s, %s)..(%s, %s) <- fill(#%02x%02x%02x)" % (
            x, y, x + w - 1, y + h - 1, r, g, b))

    def _rect(self, color, rect, line_width):
        x, y, w, h = rect
        r, g, b = color
        print("(%s, %s)..(%s, %s) <- rect(#%02x%02x%02x, %s)" % (
            x, y, x + w - 1, y + h - 1, r, g, b, line_width))

    def _line(self, color, pt1, pt2):
        x1, y1 = pt1
        x2, y2 = pt2
        r, g, b = color
        print("(%s, %s)..(%s, %s) <- line(#%02x%02x%02x)" % (
            x1, y1, x2, y2, r, g, b))

    def _aaline(self, color, pt1, pt2):
        x1, y1 = pt1
        x2, y2 = pt2
        r, g, b = color
        print("(%s, %s)..(%s, %s) <- aaline(#%02x%02x%02x)" % (
            x1, y1, x2, y2, r, g, b))

    def _circle(self, color, center, radius):
        x, y = center
        r, g, b = color
        print("(%s, %s) <- circle(#%02x%02x%02x, %s)" % (
            x, y, r, g, b, radius))


class TextSurfaceStub(SurfaceStub):

    def __init__(self, w, h, text="<text>"):
        self.w = w
        self.h = h
        self.text = text

    def __repr__(self):
        return repr(str(self.text))


class FontStub(object):

    def size(self, text):
        w = len(text) * 10
        h = 16
        return (w, h)

    def get_linesize(self):
        return 16

    def render(self, text, antialias, color, background=None):
        w, h = self.size(text)
        return TextSurfaceStub(w, h, text)


class ImageStub(object):

    w = 100
    h = 80
    colorkey = None
    alpha = 255

    def get_width(self):
        return self.w

    def get_height(self):
        return self.h

    def set_colorkey(self, color):
        r, g, b = color
        self.colorkey = (r, g, b)

    def set_alpha(self, alpha):
        self.alpha = alpha

    def convert(self):
        return ImageStub()

    def __repr__(self):
        args = []
        if self.alpha != 255:
            args.append('alpha=%s' % self.alpha)
        return 'image(%s)' % ', '.join(args)


class DrawStub(object):

    def rect(self, surface, color, rect, line_width):
        if isinstance(surface, PrintingSurfaceStub):
            surface._rect(color, rect, line_width)

    def line(self, surface, color, pt1, pt2):
        if isinstance(surface, PrintingSurfaceStub):
            surface._line(color, pt1, pt2)

    def aaline(self, surface, color, pt1, pt2):
        if isinstance(surface, PrintingSurfaceStub):
            surface._aaline(color, pt1, pt2)

    def circle(self, surface, color, center, radius):
        if isinstance(surface, PrintingSurfaceStub):
            surface._circle(color, center, radius)


def doctest_is_modifier_key():
    """Test for is_modifier_key

        >>> from pyspacewar.ui import is_modifier_key
        >>> from pygame.locals import K_LSHIFT, K_a

    Sometimes we want to distinguish modifier keys like Shift from
    real keys like A.

        >>> is_modifier_key(K_LSHIFT)
        True
        >>> is_modifier_key(K_a)
        False

    """


def doctest_find():
    """Test for find

        >>> from pyspacewar.ui import find

    This is a helper that can compute pathnames to data files

        >>> os.path.exists(find('images', 'background.jpg'))
        True

    """


def doctest_Viewport():
    """Tests for Viewport

        >>> from pyspacewar.world import Vector
        >>> from pyspacewar.ui import Viewport
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

    ``in_screen`` tests if world coordinates are visible on screen

        >>> viewport.in_screen(Vector(100, 200))
        True
        >>> viewport.in_screen(Vector(2101, 200))
        False

    ```shift_by_pixels`` adjusts the viewport position by a given
    number of screen pixels

        >>> viewport.shift_by_pixels((20, -10))
        >>> viewport.screen_pos(Vector(100, 200))
        (380, 310)

    """


def doctest_Viewport_screen_size_change():
    """Tests for Viewport

        >>> from pyspacewar.world import Vector
        >>> from pyspacewar.ui import Viewport
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

        >>> from pyspacewar.world import Vector
        >>> from pyspacewar.ui import Viewport
        >>> viewport = Viewport(SurfaceStub())

    Points that are already visible change nothing

        >>> viewport.keep_visible([Vector(0, 0)], 10)
        >>> viewport.keep_visible([Vector(100, 100)], 10)
        >>> viewport.keep_visible([Vector(-200, -100)], 10)
        >>> print(viewport.origin, viewport.scale)
        (0.000, 0.000) 1.0

    We can see the range of points that are inside the view margin, for
    a given margin size

        >>> viewport.world_inner_bounds(0)
        (-400.0, -300.0, 400.0, 300.0)
        >>> viewport.world_inner_bounds(10)
        (-390.0, -290.0, 390.0, 290.0)

    Points that are off-screen cause scrolling

        >>> viewport.keep_visible([Vector(600, 200)], 10)
        >>> print(viewport.origin, viewport.scale)
        (210.000, 0.000) 1.0

        >>> viewport.keep_visible([Vector(300, 700)], 10)
        >>> print(viewport.origin, viewport.scale)
        (210.000, 410.000) 1.0

        >>> viewport.keep_visible([Vector(-300, -100)], 10)
        >>> print(viewport.origin, viewport.scale)
        (90.000, 190.000) 1.0

        >>> viewport.world_inner_bounds(10)
        (-300.0, -100.0, 480.0, 480.0)

    If you specify several widely-separated points, they may cause a scale
    change

        >>> viewport.keep_visible([Vector(-300, -100),
        ...                        Vector(500, 400)], 10)

        >>> print(viewport.origin, round(viewport.scale, 3))
        (99.732, 190.000) 0.974

        >>> xmin, ymin, xmax, ymax = viewport.world_inner_bounds(10)
        >>> xmin <= -300 and 500 <= xmax
        True
        >>> ymin <= -100 and 400 <= ymax
        True

    """


def doctest_Viewport_draw_trail():
    """Tests for Viewport.draw_trail

        >>> from pyspacewar.world import Vector
        >>> from pyspacewar.ui import Viewport
        >>> viewport = Viewport(SurfaceStub())
        >>> viewport.scale = 2.0

        >>> viewport.draw_trail([
        ...     Vector(120, 50),
        ...     Vector(130, 55),
        ...     Vector(140, 60),
        ... ], [
        ...     (250, 250, 250),
        ...     (200, 200, 200),
        ...     (150, 150, 150),
        ... ], PrintingSurfaceStub().set_at)
        (640, 200) <- #fafafa
        (660, 190) <- #c8c8c8
        (680, 180) <- #969696

    """


def doctest_FrameRateCounter_frame():
    """Tests for FrameRateCounter.frame

        >>> from pyspacewar.ui import FrameRateCounter
        >>> frc = FrameRateCounter()

        >>> frc.frame()
        >>> len(frc.frames)
        1
        >>> frc.frame()
        >>> len(frc.frames)
        2

        >>> frc.frames = list(range(frc.avg_last_n_frames - 1))
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

        >>> from pyspacewar.ui import FrameRateCounter
        >>> frc = FrameRateCounter()
        >>> frc.frames = list(range(15))
        >>> frc.reset()
        >>> frc.frames
        []

    """


def doctest_FrameRateCounter_fps():
    """Tests for FrameRateCounter.fps

        >>> from pyspacewar.ui import FrameRateCounter
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


def doctest_FrameRateCounter_notional_fps():
    """Tests for FrameRateCounter.notional_fps

        >>> from pyspacewar.ui import FrameRateCounter
        >>> frc = FrameRateCounter()
        >>> frc.frames = []
        >>> frc.notional_fps()
        0.0

    20 ms per frame corresponds to 50 fps

        >>> frc.get_ticks = lambda: 1020
        >>> frc.frames = [1000]
        >>> frc.notional_fps()
        50.0

    """


def doctest_HUDCollection():
    """Tests for HUDCollection

        >>> from pyspacewar.ui import HUDCollection
        >>> from pyspacewar.ui import HUDElement

    This is a very boring class that holds a bunch of elements
    and can ask all of them to draw.

        >>> hc = HUDCollection([
        ...     HUDElement(180, 60, 1.0, 0.0),
        ... ])
        >>> hc.draw(SurfaceStub())

    """


def doctest_HUDElement():
    """Tests for HUDElement

        >>> from pyspacewar.ui import HUDElement
        >>> e = HUDElement(180, 60, 0, 0)

    A HUD element can compute its on-screen position

        >>> e.position(SurfaceStub(), margin=10)
        (10, 10)

    Alignment goes from 0.0 (left/top) to 1.0 (right/bottom)

        >>> e.xalign = 0.5
        >>> e.yalign = 1.0
        >>> e.position(SurfaceStub(), margin=10)
        (310, 530)

    The default draw method is a no-op; you're supposed to override
    it in subclasses

        >>> e.draw(SurfaceStub())

    """


def doctest_HUDLabel():
    """Test for HUDLabel

        >>> from pyspacewar.ui import HUDLabel
        >>> font = FontStub()
        >>> label = HUDLabel(font, "Hello", xalign=1.0)
        >>> label.draw(PrintingSurfaceStub())
        (740, 10) <- 'Hello'

    """


def doctest_HUDFormattedText():
    r"""Tests for HUDFormattedText

        >>> from pyspacewar.ui import HUDFormattedText
        >>> font = FontStub()
        >>> bold_font = FontStub()
        >>> text = u'''
        ... = Hello =
        ...
        ... This is nice?
        ...
        ...   it is \u2014 really nice???
        ...
        ... It even supports justified text if the text is long
        ... enough not to fit on a single line blah blah blah
        ... is this thing on?
        ... '''.lstrip()
        >>> help_text = HUDFormattedText(font, bold_font, text)

        >>> help_text.position(SurfaceStub())
        (30, 30)
        >>> (help_text.width, help_text.height)
        (740, 540)

        >>> help_text.draw(PrintingSurfaceStub())
        (30, 30) <- <Surface(740x540x8 SW)>
        (70, 70) <- 'Hello'
        (70, 102) <- 'This'
        (120, 102) <- 'is'
        (150, 102) <- 'nice?'
        (90, 134) <- 'it is'
        (230, 134) <- 'really'
        (300, 134) <- 'nice???'
        (70, 166) <- 'It'
        (100, 166) <- 'even'
        (151, 166) <- 'supports'
        (242, 166) <- 'justified'
        (343, 166) <- 'text'
        (394, 166) <- 'if'
        (424, 166) <- 'the'
        (465, 166) <- 'text'
        (516, 166) <- 'is'
        (547, 166) <- 'long'
        (598, 166) <- 'enough'
        (669, 166) <- 'not'
        (710, 166) <- 'to'
        (70, 182) <- 'fit'
        (110, 182) <- 'on'
        (140, 182) <- 'a'
        (160, 182) <- 'single'
        (230, 182) <- 'line'
        (280, 182) <- 'blah'
        (330, 182) <- 'blah'
        (380, 182) <- 'blah'
        (430, 182) <- 'is'
        (460, 182) <- 'this'
        (510, 182) <- 'thing'
        (570, 182) <- 'on?'
        (620, 514) <- 'Page 1 of 1'

    """


def doctest_HUDInfoPanel():
    """Tests for HUDInfoPanel

        >>> from pyspacewar.ui import HUDInfoPanel
        >>> font = FontStub()
        >>> panel = HUDInfoPanel(font, ncols=10, content=[
        ...     ['Lat', 42],
        ...     ['Lon', lambda: -55],
        ... ])

        >>> panel.draw(PrintingSurfaceStub())
        (10, 10) <- <Surface(100x32x8 SW)>
        (11, 11) <- 'Lat'
        (89, 11) <- '42'
        (11, 27) <- 'Lon'
        (79, 27) <- '-55'

    """


def doctest_HUDShipInfo():
    """Test for HUDShipInfo

        >>> from pyspacewar.ui import HUDShipInfo
        >>> from pyspacewar.world import Ship
        >>> ship = Ship()
        >>> font = FontStub()
        >>> panel = HUDShipInfo(ship, font)

        >>> panel.draw(PrintingSurfaceStub())
        (10, 10) <- <Surface(120x76x8 SW)>
        (11, 11) <- 'direction'
        (119, 11) <- '0'
        (11, 27) <- 'heading'
        (119, 27) <- '0'
        (11, 43) <- 'speed'
        (99, 43) <- '0.0'
        (11, 59) <- 'frags'
        (119, 59) <- '0'
        (11, 81)..(128, 84) <- rect(#ccffff, 1)
        (12, 82)..(127, 83) <- fill(#ffffff)

    """


def doctest_HUDCompass():
    """Test for HUDCompass

        >>> from pyspacewar.ui import HUDCompass, Viewport
        >>> from pyspacewar.world import World, Ship, Planet, Missile, Vector
        >>> world = World()
        >>> world.add(Planet(Vector(20, -30), mass=20, radius=1))
        >>> world.add(Planet(Vector(20, 30), mass=20, radius=30))
        >>> world.add(Planet(Vector(-20, 30), mass=20, radius=50))
        >>> world.add(Planet(Vector(2000, -300), mass=10))
        >>> world.add(Missile(Vector(15, 0)))
        >>> ship = Ship()
        >>> viewport = Viewport(SurfaceStub())
        >>> compass = HUDCompass(world, ship, viewport)

        >>> compass.draw(PrintingSurfaceStub())
        (10, 490) <- <Surface(100x100x8 SW)>

    """


def doctest_HUDTitle():
    """Test for HUDTitle

        >>> from pyspacewar.ui import HUDTitle
        >>> title = HUDTitle(ImageStub())
        >>> title.draw(PrintingSurfaceStub())
        (350, 135) <- image()

    Each frame also drops the alpha level

        >>> title.alpha
        242.25
        >>> title.draw(PrintingSurfaceStub())
        (350, 135) <- image(alpha=242.25)
        >>> title.alpha
        230.1375

    Eventually the image becomes invisible

        >>> title.alpha = 0.95
        >>> title.draw(PrintingSurfaceStub())

    """


def setUp(test=None):
    os.environ['SDL_VIDEODRIVER'] = 'dummy'
    os.environ['SDL_AUDIODRIVER'] = 'dummy'
    pygame.init()  # so that pygame.key.name() works
    pygame.draw = DrawStub()


def test_suite():
    path = os.path.normpath(
        os.path.join(os.path.dirname(__file__), '..', '..'))
    if path not in sys.path:
        sys.path.append(path)
    optionflags = (
        doctest.REPORT_ONLY_FIRST_FAILURE
        | doctest.REPORT_NDIFF
    )
    return unittest.TestSuite([
        doctest.DocTestSuite('pyspacewar.ui', optionflags=optionflags,
                             setUp=setUp),
        doctest.DocTestSuite(optionflags=optionflags),
    ])


if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
