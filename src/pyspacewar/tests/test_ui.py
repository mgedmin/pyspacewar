#!/usr/bin/env python
from __future__ import print_function

import unittest
import doctest
import sys
import os

import pytest
import pygame
from pygame.locals import (
    Rect, KEYDOWN, MOUSEBUTTONDOWN, MOUSEBUTTONUP, MOUSEMOTION,
)


class SurfaceStub(object):

    def __init__(self, size=(800, 600)):
        self.w, self.h = size
        self.alpha = 255
        self.colorkey = None
        self._ops = []

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

    def set_alpha(self, alpha):
        self.alpha = alpha

    def set_colorkey(self, color):
        r, g, b = color
        self.colorkey = (r, g, b)

    def _fmt_color(self, color):
        if color == self.colorkey:
            return '<colorkey>'
        r, g, b = color
        return "#%02x%02x%02x" % (r, g, b)

    def set_at(self, pos, color):
        x, y = pos
        self._record("(%s, %s) <- %s" % (x, y, self._fmt_color(color)))

    def blit(self, what, pos, area=None):
        x, y = pos
        if area:
            ax, ay, aw, ah = area
            subset = "[(%s, %s)..(%s, %s)]" % (ax, ay, ax + aw - 1, ay + ah - 1)
        else:
            subset = ""
        if what.alpha != 255:
            subset += "[alpha=%s]" % what.alpha
        self._record("(%s, %s) <- %r%s" % (x, y, what, subset))
        if isinstance(what, SurfaceStub):
            for op in what._ops:
                self._record("  %s" % op)

    def fill(self, color, rect=None):
        x, y, w, h = rect or (0, 0, self.w, self.h)
        self._record("(%s, %s)..(%s, %s) <- fill(%s)" % (
            x, y, x + w - 1, y + h - 1, self._fmt_color(color)))

    def _rect(self, color, rect, line_width):
        x, y, w, h = rect
        self._record("(%s, %s)..(%s, %s) <- rect(%s, %s)" % (
            x, y, x + w - 1, y + h - 1, self._fmt_color(color), line_width))

    def _line(self, color, pt1, pt2):
        x1, y1 = pt1
        x2, y2 = pt2
        self._record("(%s, %s)..(%s, %s) <- line(%s)" % (
            x1, y1, x2, y2, self._fmt_color(color)))

    def _aaline(self, color, pt1, pt2):
        x1, y1 = pt1
        x2, y2 = pt2
        self._record("(%s, %s)..(%s, %s) <- aaline(%s)" % (
            x1, y1, x2, y2, self._fmt_color(color)))

    def _circle(self, color, center, radius, width=0):
        x, y = center
        extra = []
        if width:
            extra.append("width=%s" % width)
        self._record("(%s, %s) <- circle(%s, %s%s)" % (
            x, y, self._fmt_color(color), radius, ", ".join(extra)))

    def _record(self, op):
        self._ops.append(op)

    def __repr__(self):
        return '<Surface(%dx%d)>' % (self.w, self.h)


class PrintingSurfaceStub(SurfaceStub):

    def _record(self, op):
        print(op)


class TextSurfaceStub(SurfaceStub):

    def __init__(self, size, text="<text>"):
        super(TextSurfaceStub, self).__init__(size)
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
        return TextSurfaceStub((w, h), text)


class ImageStub(SurfaceStub):

    def __init__(self, size=(100, 80)):
        super(ImageStub, self).__init__(size)

    @classmethod
    def load(cls, filename):
        return ImageStub()

    def convert(self):
        return ImageStub()

    def __repr__(self):
        return '<Image(%dx%d)>' % (self.w, self.h)


class DrawStub(object):

    def rect(self, surface, color, rect, line_width):
        if isinstance(surface, SurfaceStub):
            surface._rect(color, rect, line_width)

    def line(self, surface, color, pt1, pt2):
        if isinstance(surface, SurfaceStub):
            surface._line(color, pt1, pt2)

    def aaline(self, surface, color, pt1, pt2):
        if isinstance(surface, SurfaceStub):
            surface._aaline(color, pt1, pt2)

    def circle(self, surface, color, center, radius, width=0):
        if isinstance(surface, SurfaceStub):
            surface._circle(color, center, radius, width)


def array_alpha_stub(surface):
    import numpy
    size = surface.get_size()
    array = numpy.empty(size, numpy.uint8)
    return array


def pixels_alpha_stub(surface):
    import numpy
    size = surface.get_size()
    array = numpy.empty(size, numpy.uint8)
    return array


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
        (30, 30) <- <Surface(740x540)>[alpha=242]
          (0, 0)..(739, 539) <- fill(#010208)
          (0, 0) <- <colorkey>
          (0, 539) <- <colorkey>
          (739, 0) <- <colorkey>
          (739, 539) <- <colorkey>
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
        (10, 10) <- <Surface(100x32)>[alpha=204.0]
          (0, 0)..(99, 31) <- fill(#080808)
          (0, 0) <- <colorkey>
          (0, 31) <- <colorkey>
          (99, 0) <- <colorkey>
          (99, 31) <- <colorkey>
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
        (10, 10) <- <Surface(120x76)>[alpha=204.0]
          (0, 0)..(119, 75) <- fill(#080808)
          (0, 0) <- <colorkey>
          (0, 75) <- <colorkey>
          (119, 0) <- <colorkey>
          (119, 75) <- <colorkey>
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
        (10, 490) <- <Surface(100x100)>[alpha=229]
          (0, 0)..(99, 99) <- fill(<colorkey>)
          (50, 50) <- circle(#001122, 50)
          (50, 50) <- #99aaff
          (51, 51) <- #aa7766
          (51, 49)..(52, 50) <- fill(#aa7766)
          (49, 49) <- circle(#aa7766, 2)
          (50, 50)..(95, 50) <- aaline(#445566)
          (50, 50)..(50, 50) <- aaline(#99aaff)

    """


def doctest_HUDTitle_FadingImage():
    """Test for HUDTitle

        >>> from pyspacewar.ui import HUDTitle, FadingImage
        >>> title = HUDTitle(ImageStub())
        >>> title.image = FadingImage(ImageStub())
        >>> title.draw(PrintingSurfaceStub())
        (350, 135) <- <Image(100x80)>

    Each frame also drops the alpha level

        >>> title.alpha
        242.25
        >>> title.draw(PrintingSurfaceStub())
        (350, 135) <- <Image(100x80)>[alpha=242.25]
        >>> title.alpha
        230.1375

    Eventually the image becomes invisible

        >>> title.alpha = 0.95
        >>> title.draw(PrintingSurfaceStub())

    """


def doctest_HUDTitle_NumPyFadingImage():
    """Test for HUDTitle

        >>> try:
        ...     import numpy  # noqa: F401
        ... except ImportError:
        ...     pytest.skip('needs numpy')
        >>> from pyspacewar.ui import HUDTitle, NumPyFadingImage
        >>> title = HUDTitle(ImageStub())
        >>> title.image = NumPyFadingImage(ImageStub())
        >>> title.draw(PrintingSurfaceStub())
        (350, 135) <- <Image(100x80)>

    Each frame also drops the alpha level, which is reflected directly
    in the image alpha channel via numpy array operations that we cannot
    easily see in this doctest

        >>> title.alpha
        242.25
        >>> title.draw(PrintingSurfaceStub())
        (350, 135) <- <Image(100x80)>
        >>> title.alpha
        230.1375

    Eventually the image becomes invisible

        >>> title.alpha = 0.95
        >>> title.draw(PrintingSurfaceStub())

    """


def doctest_HUDMenu():
    r"""Test for HUDMenu

        >>> from pyspacewar.ui import HUDMenu
        >>> font = FontStub()
        >>> menu = HUDMenu(font, [
        ...     'Say',
        ...     'Hello',
        ...     'etc.\t!',
        ... ])
        >>> surface = PrintingSurfaceStub()
        >>> menu.draw(surface)
        (306, 236) <- <Surface(188x128)>[(0, 0)..(187, 127)][alpha=229.5]
          (0, 0)..(187, 127) <- fill(<colorkey>)
          (0, 0)..(187, 31) <- fill(#d23030)
          (79, 8) <- 'Say'
          (0, 0) <- <colorkey>
          (0, 31) <- <colorkey>
          (187, 0) <- <colorkey>
          (187, 31) <- <colorkey>
          (0, 48)..(187, 79) <- fill(#781818)
          (69, 56) <- 'Hello'
          (0, 48) <- <colorkey>
          (0, 79) <- <colorkey>
          (187, 48) <- <colorkey>
          (187, 79) <- <colorkey>
          (0, 96)..(187, 127) <- fill(#781818)
          (32, 104) <- 'etc.'
          (146, 104) <- '!'
          (0, 96) <- <colorkey>
          (0, 127) <- <colorkey>
          (187, 96) <- <colorkey>
          (187, 127) <- <colorkey>

        >>> menu.find(surface, (310, 244))
        0
        >>> menu.find(surface, (310, 356))
        2
        >>> menu.find(surface, (310, 100))
        -1

    """


def doctest_HUDControlsMenu():
    r"""Test for HUDControlsMenu

        >>> from pyspacewar.ui import HUDControlsMenu
        >>> font = FontStub()
        >>> menu = HUDControlsMenu(font, [
        ...     'Help\tF1',
        ...     'Quit\tX',
        ... ])
        >>> surface = PrintingSurfaceStub()
        >>> menu.draw(surface)
        (28, 275) <- <Surface(744x50)>[(0, 0)..(743, 49)][alpha=229.5]
          (0, 0)..(743, 49) <- fill(<colorkey>)
          (0, 0)..(743, 23) <- fill(#d23030)
          (8, 4) <- 'Help'
          (716, 4) <- 'F1'
          (0, 0) <- <colorkey>
          (0, 23) <- <colorkey>
          (743, 0) <- <colorkey>
          (743, 23) <- <colorkey>
          (0, 26)..(743, 49) <- fill(#781818)
          (8, 30) <- 'Quit'
          (726, 30) <- 'X'
          (0, 26) <- <colorkey>
          (0, 49) <- <colorkey>
          (743, 26) <- <colorkey>
          (743, 49) <- <colorkey>

    """


def doctest_HUDInput():
    """Test for HUDInput

        >>> from pyspacewar.ui import HUDInput
        >>> font = FontStub()
        >>> input = HUDInput(font, "How much?", text='0')

        >>> input.draw(PrintingSurfaceStub())
        (20, 448) <- <Surface(760x32)>[alpha=204]
          (0, 0)..(759, 31) <- fill(#010208)
          (8, 8) <- 'How much?'
          (98, 8) <- '0'
          (0, 0) <- <colorkey>
          (0, 31) <- <colorkey>
          (759, 0) <- <colorkey>
          (759, 31) <- <colorkey>

    """


def doctest_HUDMessage():
    """Test for HUDMessage

        >>> from pyspacewar.ui import HUDMessage
        >>> font = FontStub()
        >>> message = HUDMessage(font, "Press f to pay respects")

        >>> message.draw(PrintingSurfaceStub())
        (269, 276) <- <Surface(262x48)>[alpha=229]
          (0, 0)..(261, 47) <- fill(#18780e)
          (16, 16) <- 'Press f to pay respects'
          (0, 0) <- <colorkey>
          (261, 0) <- <colorkey>
          (0, 47) <- <colorkey>
          (261, 47) <- <colorkey>
          (1, 0) <- <colorkey>
          (260, 0) <- <colorkey>
          (1, 47) <- <colorkey>
          (260, 47) <- <colorkey>
          (0, 1) <- <colorkey>
          (261, 1) <- <colorkey>
          (0, 46) <- <colorkey>
          (261, 46) <- <colorkey>

    """


class UIStub(object):

    menu_font = FontStub()
    hud_font = FontStub()
    ui_mode = None
    version_text = 'version 0.42.frog-knows'

    def __init__(self):
        from pyspacewar.ui import Viewport
        self.controls = {}
        self.rev_controls = {}
        self.viewport = Viewport(SurfaceStub())

    def pause(self):
        print('Paused!')

    def watch_demo(self):
        print('Switch to demo mode!')

    def toggle_fullscreen(self):
        print('Toggle fullscreen!')

    def toggle_missile_orbits(self):
        print('Toggle missile orbits!')

    def play_music(self, music):
        print('Play %s music!' % music)

    def main_menu(self):
        print('Enter main menu!')

    def zoom_in(self):
        self.viewport.scale *= 1.25

    def zoom_out(self):
        self.viewport.scale /= 1.25


class GameModeStub(object):

    def draw(self, surface):
        surface._record('<draw the game>')

    def __repr__(self):
        return '<GameModeStub>'


class KeyEventStub(object):

    def __init__(self, key, unicode=u"", mod=0, type=KEYDOWN):
        self.type = type
        self.key = key
        self.mod = mod
        if type == KEYDOWN:
            self.unicode = unicode


class PressedKeysStub(dict):

    def __init__(self, *pressed):
        self.pressed = pressed

    def __missing__(self, key):
        return key in self.pressed


class MouseEventStub(object):

    def __init__(self, button=1, pos=(400, 300), rel=(0, 0),
                 buttons=(), type=MOUSEBUTTONDOWN):
        self.type = type
        self.pos = pos
        if type == MOUSEMOTION:
            self.buttons = [False] * 3
            for btn in buttons:
                self.buttons[btn] = True
            self.rel = rel
        else:
            self.button = button


def doctest_UIMode():
    """Test for UIMode

        >>> from pyspacewar.ui import UIMode
        >>> ui = UIStub()
        >>> mode = UIMode(ui)

    This is an abstract base class that doesn't do much

        >>> mode.enter(prev_mode=None)
        >>> mode.draw(PrintingSurfaceStub())

    There's some default event handling, e.g. you can drag the screen
    while holding down the right or middle mouse button to pan around

        >>> event = MouseEventStub(buttons=[1], rel=(7, 2), type=MOUSEMOTION)
        >>> mode.handle_mouse_motion(event)
        >>> ui.viewport.origin
        Vector(7.0, -2.0)

    and you can zoom with the mouse wheel

        >>> event = MouseEventStub(button=4)
        >>> mode.handle_mouse_press(event)
        >>> ui.viewport.scale
        1.25

        >>> event = MouseEventStub(button=5)
        >>> mode.handle_mouse_press(event)
        >>> ui.viewport.scale
        1.0

    And that's pretty much it.

        >>> mode.leave()

    """


def doctest_PauseMode():
    """Test for PauseMode

        >>> from pyspacewar.ui import PauseMode
        >>> ui = UIStub()
        >>> mode = PauseMode(ui)

    The world is frozen during pause mode

        >>> mode.paused
        True

    There's some fancy animation that starts one second after you
    enter the mode

        >>> mode.enter(prev_mode=GameModeStub())
        >>> mode.draw(PrintingSurfaceStub())
        <draw the game>

    Instead of advancing the system clock by 1 second let's push
    the mode enter time backwards by 1 second

        >>> mode.pause_entered -= 1.0
        >>> mode.draw(PrintingSurfaceStub())
        <draw the game>
        (354, 276) <- <Surface(92x48)>[alpha=0]
          (0, 0)..(91, 47) <- fill(#18780e)
          (16, 16) <- 'Paused'
          (0, 0) <- <colorkey>
          (91, 0) <- <colorkey>
          (0, 47) <- <colorkey>
          (91, 47) <- <colorkey>
          (1, 0) <- <colorkey>
          (90, 0) <- <colorkey>
          (1, 47) <- <colorkey>
          (90, 47) <- <colorkey>
          (0, 1) <- <colorkey>
          (91, 1) <- <colorkey>
          (0, 46) <- <colorkey>
          (91, 46) <- <colorkey>

    The message fades in slowly over 5 seconds

        >>> mode.pause_entered -= 2.5
        >>> mode.draw(PrintingSurfaceStub())
        <draw the game>
        (354, 276) <- <Surface(92x48)>[alpha=114]
          (0, 0)..(91, 47) <- fill(#18780e)
          (16, 16) <- 'Paused'
          (0, 0) <- <colorkey>
          (91, 0) <- <colorkey>
          (0, 47) <- <colorkey>
          (91, 47) <- <colorkey>
          (1, 0) <- <colorkey>
          (90, 0) <- <colorkey>
          (1, 47) <- <colorkey>
          (90, 47) <- <colorkey>
          (0, 1) <- <colorkey>
          (91, 1) <- <colorkey>
          (0, 46) <- <colorkey>
          (91, 46) <- <colorkey>

        >>> mode.pause_entered -= 3.0
        >>> mode.draw(PrintingSurfaceStub())
        <draw the game>
        (354, 276) <- <Surface(92x48)>[alpha=229]
          (0, 0)..(91, 47) <- fill(#18780e)
          (16, 16) <- 'Paused'
          (0, 0) <- <colorkey>
          (91, 0) <- <colorkey>
          (0, 47) <- <colorkey>
          (91, 47) <- <colorkey>
          (1, 0) <- <colorkey>
          (90, 0) <- <colorkey>
          (1, 47) <- <colorkey>
          (90, 47) <- <colorkey>
          (0, 1) <- <colorkey>
          (91, 1) <- <colorkey>
          (0, 46) <- <colorkey>
          (91, 46) <- <colorkey>

    Pause mode ends when the user presses any non-modifier key
    or a mouse button

        >>> from pygame.locals import K_SPACE, K_LSHIFT
        >>> mode.handle_key_press(KeyEventStub(K_SPACE))
        >>> ui.ui_mode
        <GameModeStub>

        >>> ui.ui_mode = None
        >>> mode.handle_mouse_release(MouseEventStub(type=MOUSEBUTTONUP))
        >>> ui.ui_mode
        <GameModeStub>

    Modifier keypresses are ignored

        >>> ui.ui_mode = None
        >>> mode.handle_key_press(KeyEventStub(K_LSHIFT))
        >>> ui.ui_mode

    """


def doctest_DemoMode():
    """Test for DemoMode

        >>> from pyspacewar.ui import DemoMode
        >>> ui = UIStub()
        >>> mode = DemoMode(ui)

        >>> mode.enter(prev_mode=GameModeStub())
        Play demo music!

    You leave demo mode by pressing any non-modifier key or the left mouse
    button

        >>> from pygame.locals import K_LSHIFT, K_SPACE

        >>> mode.handle_key_press(KeyEventStub(K_LSHIFT))

        >>> mode.handle_key_press(KeyEventStub(K_SPACE))
        Enter main menu!

        >>> mode.handle_mouse_release(MouseEventStub(button=1))
        Enter main menu!

        >>> mode.handle_mouse_release(MouseEventStub(button=2))

    You can also pause, toggle fullscreen, toggle missile orbits, or zoom

        >>> from pygame.locals import K_PAUSE, K_o, K_f, K_EQUALS, K_MINUS

        >>> mode.handle_key_press(KeyEventStub(K_PAUSE))
        Paused!

        >>> mode.handle_key_press(KeyEventStub(K_o))
        Toggle missile orbits!

        >>> mode.handle_key_press(KeyEventStub(K_f))
        Toggle fullscreen!

        >>> mode.handle_held_keys(PressedKeysStub(K_EQUALS))
        >>> ui.viewport.scale
        1.25

        >>> mode.handle_held_keys(PressedKeysStub(K_MINUS))
        >>> ui.viewport.scale
        1.0

    """


def doctest_TitleMode():
    """Test for TitleMode

        >>> from pyspacewar.ui import TitleMode, HUDTitle, FadingImage
        >>> ui = UIStub()
        >>> mode = TitleMode(ui)
        >>> mode.title = HUDTitle(ImageStub())
        >>> mode.title.image = FadingImage(ImageStub())

    Title mode is like demo mode, except it also shows a title image

        >>> ui.ui_mode = mode
        >>> mode.enter(prev_mode=None)
        Play demo music!

        >>> mode.draw(PrintingSurfaceStub())
        (285, 574) <- 'version 0.42.frog-knows'
        (350, 135) <- <Image(100x80)>

    When enough time passes that the title disappears, we switch to the regular
    demo mode

        >>> mode.title.alpha = 0.95
        >>> mode.draw(PrintingSurfaceStub())
        (285, 574) <- 'version 0.42.frog-knows'
        Switch to demo mode!

    """


@pytest.fixture(scope='module', autouse=True)
def setUp(test=None):
    os.environ['SDL_VIDEODRIVER'] = 'dummy'
    os.environ['SDL_AUDIODRIVER'] = 'dummy'
    pygame.init()  # so that pygame.key.name() works
    pygame.draw = DrawStub()
    pygame.image.load = ImageStub.load
    pygame.Surface = SurfaceStub
    pygame.surfarray.array_alpha = array_alpha_stub
    pygame.surfarray.pixels_alpha = pixels_alpha_stub


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
