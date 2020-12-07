"""
Graphical user interface for PySpaceWar
"""

import glob
import itertools
import math
import os
import random
import sys
import time


try:
    from ConfigParser import RawConfigParser as ConfigParser
except ImportError:
    from configparser import ConfigParser

try:
    unicode
except NameError:
    unicode = str

import pygame
from pygame.locals import (
    FULLSCREEN,
    K_1,
    K_2,
    K_BACKSPACE,
    K_CAPSLOCK,
    K_DELETE,
    K_DOWN,
    K_EQUALS,
    K_ESCAPE,
    K_F1,
    K_F12,
    K_KP_ENTER,
    K_KP_PERIOD,
    K_LALT,
    K_LCTRL,
    K_LEFT,
    K_LMETA,
    K_LSHIFT,
    K_LSUPER,
    K_MINUS,
    K_MODE,
    K_NUMLOCK,
    K_PAGEDOWN,
    K_PAGEUP,
    K_PAUSE,
    K_RALT,
    K_RCTRL,
    K_RETURN,
    K_RIGHT,
    K_RMETA,
    K_RSHIFT,
    K_RSUPER,
    K_SCROLLOCK,
    K_SPACE,
    K_UP,
    KEYDOWN,
    KMOD_ALT,
    MOUSEBUTTONDOWN,
    MOUSEBUTTONUP,
    MOUSEMOTION,
    QUIT,
    RESIZABLE,
    VIDEORESIZE,
    K_a,
    K_d,
    K_f,
    K_h,
    K_o,
    K_q,
    K_s,
    K_w,
    Rect,
)

from .ai import AIController
from .game import Game
from .version import version
from .world import Missile, Vector


MODIFIER_KEYS = {
    K_NUMLOCK, K_CAPSLOCK, K_SCROLLOCK,
    K_RSHIFT, K_LSHIFT, K_RCTRL, K_LCTRL, K_RALT, K_LALT,
    K_RMETA, K_LMETA, K_LSUPER, K_RSUPER, K_MODE,
}


DEFAULT_CONTROLS = {
    # Player 1
    'P1_TOGGLE_AI': K_1,
    'P1_LEFT': K_LEFT,
    'P1_RIGHT': K_RIGHT,
    'P1_FORWARD': K_UP,
    'P1_BACKWARD': K_DOWN,
    'P1_BRAKE': K_RALT,
    'P1_FIRE': K_RCTRL,
    # Player 2
    'P2_TOGGLE_AI': K_2,
    'P2_LEFT': K_a,
    'P2_RIGHT': K_d,
    'P2_FORWARD': K_w,
    'P2_BACKWARD': K_s,
    'P2_BRAKE': K_LALT,
    'P2_FIRE': K_LCTRL,
}


HELP_TEXT = u"""\
=PySpaceWar=

Two ships duel in a gravity field.   Gravity doesn't affect the ships
themselves (which have spanking new anti-gravity devices), but it affects
missiles launced by the ships.  The law of inertia applies to the ships \u2014
if you accelerate in one direction, you will continue to move in that direction
until you accelerate in another direction.

The two player mode is good for target practice, and to get the feel of your
ship.

=Player 1 Controls=

  P1_LEFT, P1_RIGHT \u2014 rotate
  P1_FORWARD      \u2014 accelerate in the direction you're facing
  P1_BACKWARD     \u2014 accelerate in the opposite direction
  P1_FIRE         \u2014 launch a missile
  P1_BRAKE        \u2014 brake (lose 5% speed)
  P1_TOGGLE_AI    \u2014 enable/disable computer control

=Player 2 Controls=

  P2_LEFT, P2_RIGHT \u2014 rotate
  P2_FORWARD      \u2014 accelerate in the direction you're facing
  P2_BACKWARD     \u2014 accelerate in the opposite direction
  P2_FIRE         \u2014 launch a missile
  P2_BRAKE        \u2014 brake (lose 5% speed)
  P2_TOGGLE_AI    \u2014 enable/disable computer control

=Other Controls=

  F1              \u2014 help
  ESC             \u2014 game menu
  PAUSE           \u2014 pause the game
  O               \u2014 hide/show missile orbits
  F, ALT+ENTER    \u2014 toggle full-screen mode
  +, -            \u2014 zoom in/out
  mouse wheel     \u2014 zoom in/out
  left click      \u2014 game menu
  right drag      \u2014 drag the viewport around

=Credits=

  Developer       \u2014 Marius Gedminas
  AI              \u2014 Ignas Mikalaj\u016bnas
  Graphics        \u2014 IGE - Outer Space (planet images)
                  \u2014 Hubble Space Telescope (background)
                  \u2014 Marius Gedminas (everything else)

PySpaceWar is powered by PyGame, Python and SDL.

This program is free software; you can redistribute it and/or modify it under
the terms of the GNU General Public License as published by the Free Software
Foundation; either version 2 of the License, or (at your option) any later
version.
"""


def key_name(key):
    """Return the name of the key.

        >>> key_name(K_RCTRL)
        'RIGHT CTRL'
        >>> key_name(None)
        '(unset)'

    """
    if not key:
        return '(unset)'
    return pygame.key.name(key).upper()


def fixup_keys_in_text(text, controls):
    """Replace action names with key names in help text.

        >>> fixup_keys_in_text('Press FIRE to start', {'FIRE': [K_RCTRL]})
        'Press RIGHT CTRL to start'

    """
    for action, keys in controls.items():
        text = text.replace(action, key_name(keys[0]))
    return text


def is_modifier_key(key):
    """Is this key a modifier?"""
    return key in MODIFIER_KEYS


def find(*filespec):
    """Construct a pathname relative to the location of this module."""
    basedir = os.path.dirname(__file__)
    return os.path.join(basedir, *filespec)


def colorblend(col1, col2, alpha=0.5):
    """Blend two colors.

    For example, let's blend 25% black and 75% white

        >>> colorblend((0, 0, 0), (255, 255, 255), 0.25)
        (191, 191, 191)

    """
    r1, g1, b1 = col1
    r2, g2, b2 = col2
    beta = 1-alpha
    return (
        int(alpha*r1+beta*r2),
        int(alpha*g1+beta*g2),
        int(alpha*b1+beta*b2),
    )


def linear(x, xmax, y1, y2):
    """Calculate a linear transition from y1 to y2 as x moves from 0 to xmax.

        >>> for x in range(10):
        ...     print('*' * int(linear(x, 9, 1, 10)))
        *
        **
        ***
        ****
        *****
        ******
        *******
        ********
        *********
        **********

    """
    return y1 + (y2 - y1) * float(x) / xmax


def smooth(x, xmax, y1, y2):
    """Calculate a smooth transition from y1 to y2 as x moves from 0 to xmax.

        >>> for x in range(10):
        ...     print('*' * int(smooth(x, 9, 1, 10)))
        *
        *
        *
        **
        ****
        ******
        ********
        *********
        *********
        *********

    """
    t = -5 + 10 * (float(x) / xmax)
    value = 1 / (1 + math.exp(-t))
    return y1 + (y2 - y1) * value


class Viewport(object):
    """A viewport to the universe.

    The responsibility of this class is to provide a mapping from screen
    coordinates to world coordinates and back.

    Attributes and properties:

        ``origin`` -- point in the universe corresponding to the center of
        the screen.

        ``scale`` -- ratio of pixels to world coordinate units.

    """

    AUTOSCALE_FACTOR = 1.001

    def __init__(self, surface):
        self.surface = surface
        self._origin = Vector(0, 0)
        self._scale = 1.0
        self._recalc()

    def _set_origin(self, new_origin):
        self._origin = new_origin
        self._recalc()

    origin = property(lambda self: self._origin, _set_origin)

    def _set_scale(self, new_scale):
        self._scale = new_scale
        self._recalc()

    scale = property(lambda self: self._scale, _set_scale)

    def _recalc(self):
        """Recalculate everything when origin/scale/screen size changes."""
        surface_w, surface_h = self.surface.get_size()
        # We want self.screen_pos(self.origin) == (surface_w/2, surface_h/2)
        self._screen_x = surface_w * 0.5 - self.origin.x * self.scale
        self._screen_y = surface_h * 0.5 + self.origin.y * self.scale
        # Let's cache world_bounds
        x1, y1 = self.world_pos((0, 0))
        x2, y2 = self.world_pos((surface_w, surface_h))
        self.world_bounds = min(x1, x2), min(y1, y2), max(x1, x2), max(y1, y2)

    def surface_size_changed(self):
        """Notify that surface size has changed."""
        self._recalc()

    def screen_len(self, world_len):
        """Convert a length in world coordinate units to pixels."""
        return int(world_len * self.scale)

    def screen_pos(self, world_pos):
        """Convert world coordinates to screen coordinates."""
        return (int(self._screen_x + world_pos[0] * self._scale),
                int(self._screen_y - world_pos[1] * self._scale))

    def draw_trail(self, list_of_world_pos, gradient, set_at):
        """Draw a trail.

        Optimization to avoid function calls and construction of lists.
        """
        sx = self._screen_x
        sy = self._screen_y
        scale = self._scale
        for (x, y), color in zip(list_of_world_pos, gradient):
            set_at((int(sx + x * scale), int(sy - y * scale)), color)

    def world_pos(self, screen_pos):
        """Convert screen coordinates into world coordinates."""
        x = (screen_pos[0] - self._screen_x) / self._scale
        y = -(screen_pos[1] - self._screen_y) / self._scale
        return (x, y)

    def in_screen(self, world_pos):
        """Is a position visible on screen?"""
        xmin, ymin, xmax, ymax = self.world_bounds
        return xmin <= world_pos[0] <= xmax and ymin <= world_pos[1] <= ymax

    def shift_by_pixels(self, delta):
        """Shift the origin by a given number of screen pixels."""
        delta_x, delta_y = delta
        self.origin += Vector(delta_x / self.scale, -delta_y / self.scale)

    def keep_visible(self, points, margin):
        """Adjust origin and scale to keep all specified points visible.

        Postcondition:

            margin <= x <= screen_w - margin

              and

            margin <= y <= screen_h - margin

              for x, y in [self.screen_pos(pt) for pt in points]

        """
        if len(points) > 1:
            xs = [pt.x for pt in points]
            ys = [pt.y for pt in points]
            w = max(xs) - min(xs)
            h = max(ys) - min(ys)
            xmin, ymin, xmax, ymax = self.world_inner_bounds(margin)
            seen_w = xmax - xmin
            seen_h = ymax - ymin
            factor = 1.0
            while seen_w < w or seen_h < h:
                factor *= self.AUTOSCALE_FACTOR
                seen_w *= self.AUTOSCALE_FACTOR
                seen_h *= self.AUTOSCALE_FACTOR
            if factor != 1.0:
                self.scale /= factor

        for pt in points:
            xmin, ymin, xmax, ymax = self.world_inner_bounds(margin)
            if pt.x < xmin:
                self.origin -= Vector(xmin - pt.x, 0)
            elif pt.x > xmax:
                self.origin -= Vector(xmax - pt.x, 0)
            if pt.y < ymin:
                self.origin -= Vector(0, ymin - pt.y)
            elif pt.y > ymax:
                self.origin -= Vector(0, ymax - pt.y)

    def world_inner_bounds(self, margin):
        """Calculate the rectange in world coordinates that fits inside a
        given margin in the screen.

        Returns (xmin, ymin, xmax, ymax).

        For all points (x, y) where (xmin <= x <= xmax and ymin <= y <= ymax)
        it is true, that margin <= sx <= screen_w - margin and
        margin <= sy <= screen_h - margin; here sx, sy == screen_pos(x, y)
        """
        surface_w, surface_h = self.surface.get_size()
        x1, y1 = self.world_pos((margin, margin))
        x2, y2 = self.world_pos((surface_w - margin, surface_h - margin))
        return min(x1, x2), min(y1, y2), max(x1, x2), max(y1, y2)


class FrameRateCounter(object):
    """Frame rate counter."""

    avg_last_n_frames = 10  # calculate average FPS for 10 frames

    get_ticks = staticmethod(pygame.time.get_ticks)

    def __init__(self):
        self.frames = []

    def frame(self):
        """Tell the counter that a new frame has just been drawn."""
        self.frames.append(self.get_ticks())
        if len(self.frames) > self.avg_last_n_frames:
            del self.frames[0]

    def reset(self):
        """Tell the counter that we stopped drawing frames for a while.

        Call this method if you pause the game for a time.
        """
        self.frames = []

    def fps(self):
        """Calculate the frame rate.

        Returns 0 if not enough frames have been drawn yet.
        """
        if len(self.frames) < 2:
            return 0
        ms = self.frames[-1] - self.frames[0]
        if ms == 0:
            return 0
        frames = len(self.frames) - 1
        return frames * 1000.0 / ms

    def notional_fps(self):
        """Calculate the frame rate assuming that I'm about to draw a frame.

        Returns 0 if not enough frames have been drawn yet.
        """
        if len(self.frames) < 1:
            return 0.0
        ms = self.get_ticks() - self.frames[0]
        frames = len(self.frames)
        return frames * 1000.0 / ms


class HUDCollection(object):
    """A collection of heads up display widgets."""

    def __init__(self, widgets=()):
        self.widgets = list(widgets)

    def draw(self, surface):
        """Draw all the elements."""
        for w in self.widgets:
            w.draw(surface)


class HUDElement(object):
    """Heads-up status display widget."""

    def __init__(self, width, height, xalign, yalign):
        self.width = width
        self.height = height
        self.xalign = xalign
        self.yalign = yalign

    def position(self, surface, margin=10):
        """Calculate screen position for the widget."""
        surface_w, surface_h = surface.get_size()
        x = margin + self.xalign * (surface_w - self.width - 2 * margin)
        y = margin + self.yalign * (surface_h - self.height - 2 * margin)
        return int(x), int(y)

    def draw(self, surface):
        """Draw the element."""
        pass


class HUDLabel(HUDElement):
    """A static text label."""

    DEFAULT_COLOR = (250, 250, 255)

    def __init__(self, font, text, xalign=0, yalign=0, color=DEFAULT_COLOR):
        self.font = font
        self.width, self.height = self.font.size(text)
        self.xalign = xalign
        self.yalign = yalign
        self.color = color
        self.rendered_text = font.render(text, True, self.color)

    def draw(self, surface):
        """Draw the element."""
        x, y = self.position(surface)
        surface.blit(self.rendered_text, (x, y))


class HUDFormattedText(HUDElement):
    """A static text screen."""

    bgcolor = (0x01, 0x02, 0x08)
    color = (0xff, 0xff, 0xff)
    page_number_color = (0x80, 0xcc, 0xff)
    alpha = int(0.95 * 255)

    xpadding = 40
    ypadding = 40

    indent = 20
    tabstop = 140

    def __init__(self, font, bold_font, text, xalign=0.5, yalign=0.5,
                 xsize=1.0, ysize=1.0, small_font=None):
        self.font = font
        self.bold_font = bold_font
        self.small_font = small_font or font
        self.text = text
        self.xsize = xsize
        self.ysize = ysize
        self.xalign = xalign
        self.yalign = yalign
        self.page = 0
        self.n_pages = -1

    def position(self, surface, margin=30):
        """Calculate screen position for the widget."""
        self.width = int((surface.get_width() - 2 * margin) * self.xsize)
        self.height = int((surface.get_height() - 2 * margin) * self.ysize)
        return HUDElement.position(self, surface, margin)

    def draw(self, surface):
        """Draw the element."""
        x, y = self.position(surface)  # calculates self.width/height as well
        rect = Rect(x, y, self.width, self.height)
        buffer = pygame.Surface(rect.size)
        buffer.set_alpha(self.alpha)
        buffer.set_colorkey((1, 1, 1))
        buffer.fill(self.bgcolor)
        for ax in (0, rect.width-1):
            for ay in (0, rect.height-1):
                buffer.set_at((ax, ay), (1, 1, 1))
        surface.blit(buffer, rect.topleft)
        rect.inflate_ip(-self.xpadding*2, -self.ypadding*2)
        self.render_text(surface, rect)

    def split_to_paragraphs(self, text):
        """Split text into paragraphs."""
        paragraphs = []
        for paragraph in self.text.split('\n\n'):
            if not paragraph.startswith(' '):
                # Intented blocks preserve line breaks, all others are joined
                paragraph = paragraph.replace('\n', ' ')
            paragraphs.append(paragraph)
        return paragraphs

    def split_items_into_groups(self, items, size, spacing):
        """Split a list of tuples (item_size, item) into groups such that
        the sum of sizes + spacing * (group size - 1) in each group is <= size.

        Think "word wrapping".
        """
        groups = []
        cur_group_size = size + 1
        for item_size, item in items:
            if cur_group_size > 0 and cur_group_size + item_size > size:
                cur_group = []
                cur_group_size = 0
                groups.append(cur_group)
            cur_group_size += item_size + spacing
            cur_group.append((item_size, item))
        return groups

    def layout_paragraph(self, paragraph, width):
        """Render and lay out a single paragraph.

        Returns (height, bits, keep_with_next) where bits is a list
        of images (one for each word) with relative coordinates.
        """
        font = self.font
        leftindent = 0
        tabstop = 0
        keep_with_next = False
        justify = False
        if paragraph.startswith('=') and paragraph.endswith('='):
            # =Title=
            paragraph = paragraph[1:-1]
            font = self.bold_font
            keep_with_next = True
        elif paragraph.startswith(' '):
            # Indented block
            leftindent += self.indent
            width -= self.indent
            tabstop = self.tabstop
        else:
            # Regular text
            justify = True
        word_spacing = font.size(' ')[0]
        line_spacing = font.get_linesize()
        bits = []
        y = 0
        for line in paragraph.splitlines():
            if tabstop and u'\u2014' in line:
                prefix, line = line.split(u'\u2014', 1)
                prefix_img = font.render(prefix.strip(), True, self.color)
                bits.append((prefix_img, (leftindent, y)))
                wrapwidth = width - tabstop
                cur_tabstop = tabstop
            else:
                wrapwidth = width
                cur_tabstop = 0
            words = [font.render(word, True, self.color)
                     for word in line.split()]
            items = [(img.get_width(), img) for img in words]
            groups = self.split_items_into_groups(items, wrapwidth,
                                                  word_spacing)
            for group in groups:
                x = leftindent + cur_tabstop
                extra_spacing = 0
                if justify and len(group) > 1 and group is not groups[-1]:
                    extra_spacing = wrapwidth
                    for img_width, img in group:
                        extra_spacing -= img_width
                    extra_spacing -= word_spacing * (len(group) - 1)
                    extra_spacing = float(extra_spacing) / (len(group) - 1)
                for img_width, img in group:
                    bits.append((img, (int(x), y)))
                    x += img_width + word_spacing + extra_spacing
                y += line_spacing
        return y, bits, keep_with_next

    def layout_pages(self, text, page_size):
        """Render and lay out text into pages.

        Returns a list of pages, where each page is a list of of images (one
        for each word) with relative coordinates.

        Currently the page layout engine doesn't try to split paragraphs.
        """
        width, height = page_size
        paragraph_spacing = self.font.get_linesize()
        last_item_size = 0
        last_item_bits = []
        items = []
        for paragraph in self.split_to_paragraphs(text):
            size, bits, keep_with_next = self.layout_paragraph(paragraph,
                                                               width)
            if last_item_bits:  # join with previous
                dy = last_item_size + paragraph_spacing
                bits = last_item_bits + [(img, (x, y+dy))
                                         for (img, (x, y)) in bits]
                size += dy
            if keep_with_next:
                last_item_size = size
                last_item_bits = bits
            else:
                items.append((size, bits))
                last_item_size = 0
                last_item_bits = []
        if last_item_bits:  # last paragraph had "keep with next" set
            items.append((last_item_size, last_item_bits))
        pages = self.split_items_into_groups(items, height, paragraph_spacing)
        return pages

    def render_text(self, surface, page_rect):
        """Render the text onto surface."""
        paragraph_spacing = self.font.get_linesize()
        width, height = page_rect.size
        height -= self.small_font.get_linesize() * 2
        pages = self.layout_pages(self.text, (width, height))
        self.n_pages = len(pages)
        if not pages:
            # This cannot happen due to the way str.split() works in
            # python -- we'll always have at least one page with at
            # least one paragraph, even if it is empty.
            return  # pragma: nocover
        self.page = max(0, min(self.page, len(pages)-1))
        left = page_rect.left
        top = page_rect.top
        for para_size, para in pages[self.page]:
            for img, (x, y) in para:
                surface.blit(img, (left + x, top + y))
            top += para_size + paragraph_spacing
        page_text = 'Page %d of %d' % (self.page + 1, self.n_pages)
        img = self.small_font.render(page_text, True, self.page_number_color)
        r = img.get_rect()
        r.bottomright = page_rect.bottomright
        surface.blit(img, r.topleft)


class HUDInfoPanel(HUDElement):
    """Heads-up status display base class."""

    STD_COLORS = [(0xff, 0xff, 0xff), (0xcc, 0xff, 0xff)]
    GREEN_COLORS = [(0x7f, 0xff, 0x00), (0xcc, 0xff, 0xff)]

    def __init__(self, font, ncols, nrows=None, xalign=0, yalign=0,
                 colors=STD_COLORS, content=None):
        self.font = font
        self.width = int(self.font.size('x')[0] * ncols)
        self.row_height = self.font.get_linesize()
        if nrows is None:
            nrows = len(content)
        self.height = int(nrows * self.row_height)
        self.xalign = xalign
        self.yalign = yalign
        self.color1, self.color2 = colors
        self.surface = pygame.Surface((self.width, self.height))
        self.surface.set_alpha(255 * 0.8)
        self.surface.set_colorkey((1, 1, 1))
        self.surface.fill((8, 8, 8))
        for x in (0, self.width-1):
            for y in (0, self.height-1):
                self.surface.set_at((x, y), (1, 1, 1))
        self.content = content or []

    def draw_rows(self, surface, *rows):
        """Draw some information.

        ``rows`` is a list of 2-tuples.
        """
        x, y = self.position(surface)
        surface.blit(self.surface, (x, y))
        x += 1
        y += 1
        for a, b in rows:
            img = self.font.render(str(a), True, self.color1)
            surface.blit(img, (x, y))
            img = self.font.render(str(b), True, self.color2)
            surface.blit(img, (x + self.width - 2 - img.get_width(), y))
            y += self.row_height

    def draw(self, surface):
        """Draw the panel."""
        rows = []
        for content_row in self.content:
            row = []
            for value in content_row:
                if callable(value):
                    row.append(value())
                else:
                    row.append(unicode(value))
            rows.append(row)
        self.draw_rows(surface, *rows)


class HUDShipInfo(HUDInfoPanel):
    """Heads-up ship status display."""

    def __init__(self, ship, font, xalign=0, yalign=0,
                 colors=HUDInfoPanel.STD_COLORS):
        HUDInfoPanel.__init__(self, font, 12, 4.75, xalign, yalign, colors)
        self.ship = ship

    def draw(self, surface):
        self.draw_rows(
            surface,
            ('direction', '%d' % self.ship.direction),
            ('heading', '%d' % self.ship.velocity.direction()),
            ('speed', '%.1f' % self.ship.velocity.length()),
            ('frags', '%d' % self.ship.frags),
        )
        x, y = self.position(surface)
        x += 1
        y += self.height - 5
        w = max(0, int((self.width - 4) * self.ship.health))
        pygame.draw.rect(surface, self.color2, (x, y, self.width-2, 4), 1)
        surface.fill(self.color1, (x+1, y+1, w, 2))


class HUDCompass(HUDElement):
    """Heads-up ship compass display.

    Shows two vectors: direction of the ship, and the current velocity.
    """

    alpha = int(0.9*255)

    BLUE_COLORS = (
        (0x00, 0x11, 0x22),
        (0x99, 0xaa, 0xff),
        (0x44, 0x55, 0x66),
        (0xaa, 0x77, 0x66),
    )

    GREEN_COLORS = (
        (0x00, 0x22, 0x11),
        (0x99, 0xff, 0xaa),
        (0x44, 0x66, 0x55),
        (0xaa, 0x66, 0x77),
    )

    radius = 50
    radar_scale = 0.05
    velocity_scale = 50

    def __init__(self, world, ship, viewport, xalign=0, yalign=1,
                 colors=BLUE_COLORS):
        self.world = world
        self.ship = ship
        self.viewport = viewport
        self.width = self.height = 2*self.radius
        self.surface = pygame.Surface((self.width, self.height))
        self.bgcolor, self.fgcolor1, self.fgcolor2, self.fgcolor3 = colors
        self.xalign = xalign
        self.yalign = yalign

    def draw(self, surface):
        if surface.get_bitsize() >= 24:
            # Only 24 and 32 bpp modes support aaline
            draw_line = pygame.draw.aaline
        else:
            draw_line = pygame.draw.line
        x = y = self.radius
        self.surface.set_colorkey((1, 1, 1))
        self.surface.fill((1, 1, 1))
        self.surface.set_alpha(self.alpha)

        pygame.draw.circle(self.surface, self.bgcolor, (x, y), self.radius)
        self.surface.set_at((x, y), self.fgcolor1)

        scale = self.radar_scale * self.viewport.scale
        for body in self.world.objects:
            if body.mass == 0:
                continue
            pos = (body.position - self.ship.position) * scale
            if pos.length() > self.radius:
                continue
            radius = max(0, int(body.radius * scale))
            px = x + int(pos.x)
            py = y - int(pos.y)
            if radius < 1:
                self.surface.set_at((px, py), self.fgcolor3)
            elif radius == 1:
                self.surface.fill(self.fgcolor3, (px, py, 2, 2))
            else:
                pygame.draw.circle(self.surface, self.fgcolor3, (px, py),
                                   radius)

        d = self.ship.direction_vector
        d = d.scaled(self.radius * 0.9)
        x2 = x + int(d.x)
        y2 = y - int(d.y)
        draw_line(self.surface, self.fgcolor2, (x, y), (x2, y2))

        v = self.ship.velocity * self.velocity_scale
        if v.length() > self.radius * 0.9:
            v = v.scaled(self.radius * 0.9)
        x2 = x + int(v.x)
        y2 = y - int(v.y)
        draw_line(self.surface, self.fgcolor1, (x, y), (x2, y2))

        surface.blit(self.surface, self.position(surface))


class FadingImage(object):
    """An image that can smoothly fade away.

    Uses a color key and surface alpha, as an approximation of a smooth fade
    out.  Drops the alpha information in the source image, so instead of
    smooth anti-aliased text being faded out the users will see ragged text
    being faded out.

    This happens quickly enough so that nobody will likely notice -- it took me
    a good ten minutes to remember why I even had the more advanced fading
    methods ;)
    """

    def __init__(self, image):
        self.image = image.convert()  # drop the alpha channel
        self.image.set_colorkey((0, 0, 0))

    def draw(self, surface, x, y, alpha):
        """Draw the image.

        ``alpha`` is a floating point value between 0 and 255.
        """
        self.image.set_alpha(alpha)
        surface.blit(self.image, (x, y))


class NumPyFadingImage(object):
    """An image that can smoothly fade away.

    Implemented using NumPy arrays to scale the alpha channel on the fly.
    """

    def __init__(self, image):
        import numpy  # noqa
        self.image = image
        self.mask = pygame.surfarray.array_alpha(image)
        if hasattr(pygame.surfarray, 'use_arraytype'):
            # This is a global switch, which breaks the abstraction a bit. :(
            pygame.surfarray.use_arraytype('numpy')

    def draw(self, surface, x, y, alpha):
        """Draw the image.

        ``alpha`` is a floating point value between 0 and 255.
        """
        import numpy
        numpy.multiply(self.mask, alpha / 255,
                       pygame.surfarray.pixels_alpha(self.image),
                       casting='unsafe')
        surface.blit(self.image, (x, y))


class HUDTitle(HUDElement):
    """Fading out title."""

    paused = False

    def __init__(self, image, xalign=0.5, yalign=0.25):
        HUDElement.__init__(self, image.get_width(), image.get_height(),
                            xalign, yalign)
        self.alpha = 255
        for cls in NumPyFadingImage, FadingImage:
            try:
                self.image = cls(image)
            except ImportError:
                pass
            else:
                break

    def draw(self, surface):
        """Draw the element."""
        if self.alpha < 1:
            return
        x, y = self.position(surface)
        self.image.draw(surface, x, y, self.alpha)
        if not self.paused:
            self.alpha *= 0.95


class HUDMenu(HUDElement):
    """A menu."""

    normal_fg_color = (220, 255, 64)
    normal_bg_color = (120, 24, 24)
    selected_fg_color = (255, 255, 220)
    selected_bg_color = (210, 48, 48)

    def __init__(self, font, items, xalign=0.5, yalign=0.5,
                 xpadding=32, ypadding=8, yspacing=16):
        width, item_height = self.itemsize(font, items, xpadding, ypadding)
        height = max(0, (item_height + yspacing) * len(items) - yspacing)
        HUDElement.__init__(self, width, height, xalign, yalign)
        self.full_height = height
        self.font = font
        self.items = items
        self.yspacing = yspacing
        self.xpadding = xpadding
        self.ypadding = ypadding
        self.selected_item = 0
        self.top = 0
        self.item_height = item_height
        self.resize()

    def position(self, surface, margin=10):
        """Calculate screen position for the widget."""
        max_height = surface.get_height() - 2 * margin
        item_spacing = self.item_height + self.yspacing
        self.height = self.full_height
        while self.height > max_height:
            self.height -= item_spacing
        if self.selected_item * item_spacing < self.top:
            self.top = self.selected_item * item_spacing
        while (self.selected_item * item_spacing + self.item_height >
               self.top + self.height):
            self.top += item_spacing
        return HUDElement.position(self, surface, margin)

    def resize(self):
        self.surface = pygame.Surface((self.width, self.full_height))
        self.surface.set_alpha(255 * 0.9)
        self.surface.set_colorkey((1, 1, 1))
        self.invalidate()

    def invalidate(self):
        """Indicate that the menu needs to be redrawn."""
        self._drawn_with = None

    def itemsize(self, font, items, xpadding, ypadding):
        """Calculate the size of the largest item."""
        width = 0
        height = 0
        for item in items:
            size = font.size(item)
            if '\t' in item:
                size = (size[0] + xpadding * 2, size[1])
            width = max(width, size[0])
            height = max(height, size[1])
        return width + 2 * xpadding, height + 2 * ypadding

    def find(self, surface, pos):
        """Find the item at given coordinates."""
        x, y = pos
        ix, iy = self.position(surface)
        iy -= self.top
        for idx, item in enumerate(self.items):
            if ix <= x < ix + self.width and iy <= y < iy + self.item_height:
                return idx
            iy += self.item_height + self.yspacing
        return -1

    def _draw(self):
        """Draw the menu on self.surface."""
        self._drawn_with = self.selected_item
        self.surface.fill((1, 1, 1))
        x = 0
        y = 0
        for idx, item in enumerate(self.items):
            if idx == self.selected_item:
                fg_color = self.selected_fg_color
                bg_color = self.selected_bg_color
            else:
                fg_color = self.normal_fg_color
                bg_color = self.normal_bg_color
            self.surface.fill(bg_color, (x, y, self.width, self.item_height))
            if '\t' in item:
                # align left and right
                parts = item.split('\t', 1)
                img = self.font.render(parts[0], True, fg_color)
                margin = (self.item_height - img.get_height()) // 2
                self.surface.blit(img, (x + self.xpadding, y + margin))
                img = self.font.render(parts[1], True, fg_color)
                self.surface.blit(
                    img,
                    (x + self.width - img.get_width() - self.xpadding,
                     y + margin))
            else:
                # center
                img = self.font.render(item, True, fg_color)
                margin = (self.item_height - img.get_height()) // 2
                self.surface.blit(img,
                                  (x + (self.width - img.get_width()) // 2,
                                   y + margin))
            for ax in (0, self.width-1):
                for ay in (0, self.item_height-1):
                    self.surface.set_at((x+ax, y+ay), (1, 1, 1))
            y += self.item_height + self.yspacing

    def draw(self, surface):
        """Draw the element."""
        # NB: self.position() might call self.resize() so we must
        # call it before _draw()
        x, y = self.position(surface)
        if self.selected_item != self._drawn_with:
            self._draw()
        surface.blit(self.surface, (x, y),
                     (0, self.top, self.width, self.height))


class HUDControlsMenu(HUDMenu):
    """A scrolling menu for keyboard controls."""

    def __init__(self, font, items, xalign=0.5, yalign=0.5,
                 xpadding=8, ypadding=4, yspacing=2):
        HUDMenu.__init__(self, font, items, xalign, yalign, xpadding,
                         ypadding, yspacing)

    def position(self, surface, margin=20):
        """Calculate screen position for the widget."""
        width = surface.get_width() - 2 * margin - 2 * self.xpadding
        if width != self.width:
            self.width = width
            self.resize()
        return HUDMenu.position(self, surface, margin)


class HUDInput(HUDElement):
    """An input box."""

    bgcolor = (0x01, 0x02, 0x08)
    color1 = (0x80, 0xcc, 0xff)
    color2 = (0xee, 0xee, 0xee)
    alpha = int(0.8 * 255)

    def __init__(self, font, prompt, text='', xmargin=20, ymargin=120,
                 xpadding=8, ypadding=8):
        self.font = font
        self.prompt = prompt
        self.text = text
        self.xmargin = xmargin
        self.ymargin = ymargin
        self.xpadding = xpadding
        self.ypadding = ypadding

    def draw(self, surface):
        """Draw the element."""
        surface_w, surface_h = surface.get_size()
        width = surface_w - 2*self.xmargin
        height = self.font.get_linesize() + 2*self.ypadding
        buffer = pygame.Surface((width, height))
        buffer.set_alpha(self.alpha)
        buffer.set_colorkey((1, 1, 1))
        buffer.fill(self.bgcolor)
        img1 = self.font.render(self.prompt, True, self.color1)
        buffer.blit(img1, (self.xpadding, self.ypadding))
        img2 = self.font.render(self.text, True, self.color2)
        buffer.blit(img2, (self.xpadding + img1.get_width(), self.ypadding))
        for x in (0, width-1):
            for y in (0, height-1):
                buffer.set_at((x, y), (1, 1, 1))
        surface.blit(buffer, (self.xmargin,
                              surface_h - self.ymargin - buffer.get_height()))


class HUDMessage(HUDElement):
    """An message box."""

    fg_color = (220, 255, 255)
    bg_color = (24, 120, 14)
    alpha = int(255 * 0.9)

    def __init__(self, font, text, xpadding=16, ypadding=16, xalign=0.5,
                 yalign=0.5):
        width, height = font.size(text)
        width += 2*xpadding
        height += 2*ypadding
        HUDElement.__init__(self, width, height, xalign, yalign)
        self.xpadding = xpadding
        self.ypadding = ypadding
        self.font = font
        self.text = text
        self.surface = pygame.Surface((self.width, self.height))
        self.surface.set_colorkey((1, 1, 1))
        self.surface.fill(self.bg_color)
        img = self.font.render(text, True, self.fg_color)
        x = (self.width - img.get_width()) // 2
        y = (self.height - img.get_height()) // 2
        self.surface.blit(img, (x, y))
        for dx, dy in (0, 0), (1, 0), (0, 1):
            self.surface.set_at((dx, dy), (1, 1, 1))
            self.surface.set_at((self.width-1-dx, dy), (1, 1, 1))
            self.surface.set_at((dx, self.height-1-dy), (1, 1, 1))
            self.surface.set_at((self.width-1-dx, self.height-1-dy), (1, 1, 1))

    def draw(self, surface):
        """Draw the element."""
        x, y = self.position(surface)
        self.surface.set_alpha(self.alpha)
        surface.blit(self.surface, (x, y))


class UIMode(object):
    """Mode of user interface.

    The mode determines several things:
      - what is displayed on screen
      - whether the game progresses
      - how keystrokes are interpreted

    Examples of modes: game play, paused, navigating a menu.
    """

    paused = False
    mouse_visible = False
    keys_repeat = False
    music = None

    inherit_pause_from_prev_mode = False

    def __init__(self, ui):
        self.ui = ui
        self.prev_mode = None
        self.clear_keymap()
        self.init()

    def __repr__(self):
        return '<{}>'.format(self.__class__.__name__)

    def init(self):
        """Initialize the mode."""
        pass

    def enter(self, prev_mode):
        """Enter the mode."""
        if self.prev_mode is None:
            # Only do this once, otherwise two modes might get in a loop
            self.prev_mode = prev_mode
            if self.inherit_pause_from_prev_mode and prev_mode is not None:
                self.paused = prev_mode.paused
        pygame.mouse.set_visible(self.mouse_visible)
        if self.keys_repeat:
            pygame.key.set_repeat(250, 30)
        else:
            pygame.key.set_repeat()
        if self.music:
            self.ui.play_music(self.music)

    def leave(self, next_mode=None):
        """Leave the mode."""
        pass

    def return_to_previous_mode(self):
        """Return to the previous game mode."""
        if self.prev_mode is not None:
            self.ui.ui_mode = self.prev_mode

    def draw(self, screen):
        """Draw extra things pertaining to the mode."""
        pass

    def clear_keymap(self):
        """Clear all key mappings."""
        self._keymap_once = {}
        self._keymap_repeat = {}

    def on_key(self, key, handler, *args):
        """Install a handler to be called once when a key is pressed."""
        self._keymap_once[key] = handler, args

    def while_key(self, key, handler, *args):
        """Install a handler to be called repeatedly while a key is pressed."""
        self._keymap_repeat[key] = handler, args

    def handle_key_press(self, event):
        """Handle a KEYDOWN event."""
        key = event.key
        if key in self.ui.rev_controls:
            action = self.ui.rev_controls[key]
            if action in self._keymap_once or action in self._keymap_repeat:
                key = action
        handler_and_args = self._keymap_once.get(key)
        if handler_and_args:
            handler, args = handler_and_args
            handler(*args)
        elif key not in self._keymap_repeat:
            self.handle_any_other_key(event)

    def handle_any_other_key(self, event):
        """Handle a KEYDOWN event for unknown keys."""
        pass

    def handle_held_keys(self, pressed):
        """Handle any keys that are pressed."""
        for key, (handler, args) in self._keymap_repeat.items():
            for key in self.ui.controls.get(key, [key]):
                if key is not None and pressed[key]:
                    handler(*args)

    def handle_mouse_press(self, event):
        """Handle a MOUSEBUTTONDOWN event."""
        if event.button == 4:
            self.ui.zoom_in()
        if event.button == 5:
            self.ui.zoom_out()

    def handle_mouse_release(self, event):
        """Handle a MOUSEBUTTONUP event."""
        pass

    def handle_mouse_motion(self, event):
        """Handle a MOUSEMOTION event."""
        if event.buttons[1] or event.buttons[2]:
            self.ui.viewport.shift_by_pixels(event.rel)


class PauseMode(UIMode):
    """Mode: paused."""

    paused = True

    show_message_after = 1  # seconds
    fade_in_time = 5  # seconds

    clock = staticmethod(time.time)

    def enter(self, prev_mode):
        """Enter the mode."""
        UIMode.enter(self, prev_mode)
        self.message = None
        self.pause_entered = self.clock()
        self.animate = self.wait_for_fade

    def draw(self, screen):
        """Draw extra things pertaining to the mode."""
        self.prev_mode.draw(screen)
        if self.animate:
            self.animate()
        if self.message:
            self.message.draw(screen)

    def wait_for_fade(self):
        if self.clock() >= self.pause_entered + self.show_message_after:
            self.message = HUDMessage(self.ui.menu_font, "Paused")
            self.message.alpha = 0
            self.animate = self.fade_in

    def fade_in(self):
        t = self.clock() - self.pause_entered - self.show_message_after
        if t > self.fade_in_time:
            self.message.alpha = int(255 * 0.9)
            self.animate = None
        else:
            self.message.alpha = int(smooth(t, self.fade_in_time, 0, 255*0.9))

    def handle_any_other_key(self, event):
        """Handle a KEYDOWN event for unknown keys."""
        if not is_modifier_key(event.key):
            self.return_to_previous_mode()

    def handle_mouse_release(self, event):
        """Handle a MOUSEBUTTONUP event."""
        self.return_to_previous_mode()


class DemoMode(UIMode):
    """Mode: demo."""

    paused = False
    music = 'demo'

    def init(self):
        """Initialize the mode."""
        self.on_key(K_PAUSE, self.ui.pause)
        self.while_key(K_EQUALS, self.ui.zoom_in)
        self.while_key(K_MINUS, self.ui.zoom_out)
        self.on_key(K_o, self.ui.toggle_missile_orbits)
        self.on_key(K_f, self.ui.toggle_fullscreen)

    def handle_mouse_release(self, event):
        """Handle a MOUSEBUTTONDOWN event."""
        if event.button == 1:
            self.ui.main_menu()
        else:
            UIMode.handle_mouse_press(self, event)

    def handle_any_other_key(self, event):
        """Handle a KEYDOWN event for unknown keys."""
        if not is_modifier_key(event.key):
            self.ui.main_menu()


class TitleMode(DemoMode):
    """Mode: fading out title."""

    def init(self):
        """Initialize the mode."""
        DemoMode.init(self)
        title_image = pygame.image.load(find('images', 'title.png'))
        self.title = HUDTitle(title_image)
        self.version = HUDLabel(self.ui.hud_font, self.ui.version_text,
                                0.5, 1)

    def draw(self, screen):
        """Draw extra things pertaining to the mode."""
        self.version.draw(screen)
        self.title.paused = self.ui.ui_mode.paused
        self.title.draw(screen)
        if self.title.alpha < 1:
            self.ui.watch_demo()


class MenuMode(UIMode):
    """Abstract base class for menu modes."""

    mouse_visible = True
    keys_repeat = True
    inherit_pause_from_prev_mode = True

    def init(self):
        """Initialize the mode."""
        self.init_menu()
        self.menu = self.create_menu()
        if self.has_no_action(self.menu.selected_item):
            self.select_next_item()
        self.on_key(K_UP, self.select_prev_item)
        self.on_key(K_DOWN, self.select_next_item)
        self.on_key(K_RETURN, self.activate_item)
        self.on_key(K_KP_ENTER, self.activate_item)
        self.on_key(K_ESCAPE, self.close_menu)
        self.menu.invalidate()
        # These might be overkill
        self.while_key(K_EQUALS, self.ui.zoom_in)
        self.while_key(K_MINUS, self.ui.zoom_out)
        self.on_key(K_o, self.ui.toggle_missile_orbits)
        self.on_key(K_f, self.ui.toggle_fullscreen)
        self.version = HUDLabel(self.ui.hud_font, self.ui.version_text, 0.5, 1)

    def init_menu(self):
        """Initialize the menu."""
        self.menu_items = [
            ('Quit',            self.ui.quit),
        ]

    def create_menu(self):
        """Create the menu control for display."""
        return HUDMenu(self.ui.menu_font,
                       [item[0] for item in self.menu_items])

    def has_no_action(self, item_idx):
        """Is this menu item just an unselectable label?"""
        return len(self.menu_items[item_idx]) == 1

    def reinit_menu(self):
        """Reinitialize the menu."""
        self.init_menu()
        assert len(self.menu_items) == len(self.menu.items)
        self.menu.items = [item[0] for item in self.menu_items]
        self.menu.invalidate()

    def _select_menu_item(self, pos):
        """Select menu item under cursor."""
        which = self.menu.find(self.ui.screen, pos)
        if which != -1 and not self.has_no_action(which):
            self.menu.selected_item = which
        return which

    def handle_mouse_press(self, event):
        """Handle a MOUSEBUTTONDOWN event."""
        if event.button == 1:
            self._select_menu_item(event.pos)
        else:
            UIMode.handle_mouse_press(self, event)

    def handle_mouse_motion(self, event):
        """Handle a MOUSEMOTION event."""
        if event.buttons[0]:
            self._select_menu_item(event.pos)
        UIMode.handle_mouse_motion(self, event)

    def handle_mouse_release(self, event):
        """Handle a MOUSEBUTTONUP event."""
        if event.button == 1:
            which = self._select_menu_item(event.pos)
            if which != -1:
                self.activate_item()
        else:
            UIMode.handle_mouse_release(self, event)

    def draw(self, screen):
        """Draw extra things pertaining to the mode."""
        self.version.draw(screen)
        self.menu.draw(screen)

    def select_prev_item(self):
        """Select the previous menu item."""
        if self.menu.selected_item == 0:
            self.menu.selected_item = len(self.menu.items)
        self.menu.selected_item -= 1
        if self.has_no_action(self.menu.selected_item):
            self.select_prev_item()

    def select_next_item(self):
        """Select the next menu item."""
        self.menu.selected_item += 1
        if self.menu.selected_item == len(self.menu.items):
            self.menu.selected_item = 0
            self.menu.top = 0
        if self.has_no_action(self.menu.selected_item):
            self.select_next_item()

    def activate_item(self):
        """Activate the selected menu item."""
        action = self.menu_items[self.menu.selected_item][1:]
        if action:
            self.ui.play_sound('menu')
            handler = action[0]
            args = action[1:]
            handler(*args)

    def close_menu(self):
        """Close the menu and return to the previous game mode."""
        self.return_to_previous_mode()


class MainMenuMode(MenuMode):
    """Mode: main menu."""

    def init_menu(self):
        """Initialize the mode."""
        self.menu_items = [
            ('New Game',        self.ui.new_game_menu),
            ('Options',         self.ui.options_menu),
            ('Help',            self.ui.help),
            ('Watch Demo',      self.ui.watch_demo),
            ('Quit',            self.ui.quit),
        ]
        self.on_key(K_PAUSE, self.ui.pause)
        self.on_key(K_q, self.ui.quit)  # hidden shortcut
        self.on_key(K_h, self.ui.help)  # hidden shortcut
        self.on_key(K_F1, self.ui.help)  # hidden shortcut


class NewGameMenuMode(MenuMode):
    """Mode: new game menu."""

    def init_menu(self):
        """Initialize the mode."""
        self.menu_items = [
            ('One Player Game', self.ui.start_single_player_game),
            ('Two Player Game', self.ui.start_two_player_game),
            ('Gravity Wars',    self.ui.start_gravity_wars),
            ('No, thanks',      self.close_menu),
        ]


class OptionsMenuMode(MenuMode):
    """Mode: options menu."""

    def init_menu(self):
        """Initialize the mode."""
        self.menu_items = [
            ('Video', self.ui.video_options_menu),
            ('Sound', self.ui.sound_options_menu),
            ('Controls', self.ui.controls_menu),
            ('Return to main menu', self.close_menu),
        ]


class VideoOptionsMenuMode(MenuMode):
    """Mode: video options menu."""

    def init_menu(self):
        """Initialize the mode."""
        def title(label, on):
            return label + '\t' + (on and 'on' or 'off')
        self.menu_items = [
            ('Screen size\t%dx%d' % self.ui.fullscreen_mode,
             self.ui.screen_resolution_menu),
            (title('Full screen mode', self.ui.fullscreen),
             self.toggle_fullscreen),
            (title('Missile orbits', self.ui.show_missile_trails),
             self.toggle_missile_orbits),
            ('Return to options menu', self.close_menu),
        ]

    def enter(self, prev_mode):
        """Enter the mode."""
        MenuMode.enter(self, prev_mode)
        # If we're coming back from the screen resolution menu, we need
        # to update the current resolution
        self.reinit_menu()

    def toggle_fullscreen(self):
        """Toggle full-screen mode and reflect the setting in the menu."""
        self.ui.toggle_fullscreen()
        self.reinit_menu()

    def toggle_missile_orbits(self):
        """Toggle missile orbits and reflect the setting in the menu."""
        self.ui.toggle_missile_orbits()
        self.reinit_menu()


class ScreenResolutionMenuMode(MenuMode):
    """Mode: screen resolution menu."""

    def init_menu(self):
        """Initialize the mode."""
        self.menu_items = [
            ('%dx%d' % mode, lambda mode=mode: self.switch_to_mode(mode))
            for mode in pygame.display.list_modes()
        ] + [
            ('Return to options menu', self.close_menu),
        ]

    def switch_to_mode(self, mode):
        """Switch to a specified video mode."""
        self.ui.switch_to_mode(mode)
        self.reinit_menu()


class SoundOptionsMenuMode(MenuMode):
    """Mode: sound options menu."""

    def init_menu(self):
        """Initialize the mode."""
        def title(label, on):
            return label + '\t' + (on and 'on' or 'off')
        if self.ui.sound_available:
            extra = ''
        else:
            extra = ' (not available)'
        self.menu_items = [
            (title('Music' + extra, self.ui.music),
             self.toggle_music),
            (title('Sound' + extra, self.ui.sound),
             self.toggle_sound),
            (title('Sound in vacuum', self.ui.sound_in_vacuum),
             self.toggle_sound_in_vacuum),
            ('Return to options menu', self.close_menu),
        ]

    def toggle_music(self):
        """Toggle music and reflect the setting in the menu."""
        self.ui.toggle_music()
        self.reinit_menu()

    def toggle_sound(self):
        """Toggle sound effects and reflect the setting in the menu."""
        self.ui.toggle_sound()
        self.reinit_menu()

    def toggle_sound_in_vacuum(self):
        """Toggle sound in vacuum and reflect the setting in the menu."""
        self.ui.toggle_sound_in_vacuum()
        self.reinit_menu()


class ControlsMenuMode(MenuMode):
    """Mode: controls menu."""

    def init(self):
        MenuMode.init(self)
        self.on_key(K_BACKSPACE, self.clear_item)
        self.on_key(K_DELETE, self.clear_item)
        self.on_key(K_KP_PERIOD, self.clear_item)
        self.version = HUDLabel(self.ui.hud_font,
                                "Press ENTER to change a binding,"
                                " BACKSPACE to clear it",
                                0.5, 1)

    def items(self, label, items):
        return ([(label, )] +
                [(title + '\t' + ', '.join(map(key_name,
                                               self.ui.controls[action])),
                  self.set_control, action)
                 for title, action in items])

    def init_menu(self):
        self.menu_items = self.items('Player 1', [
                ('Turn left', 'P1_LEFT'),
                ('Turn right', 'P1_RIGHT'),
                ('Accelerate', 'P1_FORWARD'),
                ('Decelerate', 'P1_BACKWARD'),
                ('Launch missile', 'P1_FIRE'),
                ('Brake', 'P1_BRAKE'),
                ('Toggle computer control', 'P1_TOGGLE_AI'),
        ]) + self.items('Player 2', [
                ('Turn left', 'P2_LEFT'),
                ('Turn right', 'P2_RIGHT'),
                ('Accelerate', 'P2_FORWARD'),
                ('Decelerate', 'P2_BACKWARD'),
                ('Launch missile', 'P2_FIRE'),
                ('Brake', 'P2_BRAKE'),
                ('Toggle computer control', 'P2_TOGGLE_AI'),
        ]) + [
            ('Return to options menu', self.close_menu),
        ]

    def create_menu(self):
        """Create the menu control for display."""
        return HUDControlsMenu(self.ui.input_font,
                               [item[0] for item in self.menu_items])

    def set_control(self, action):
        """Change a control"""
        self.ui.ui_mode = WaitingForControlMode(self.ui, action)

    def clear_item(self):
        """Clear the selected menu item."""
        action = self.menu_items[self.menu.selected_item][1:]
        if action:
            handler = action[0]
            args = action[1:]
            if handler == self.set_control:
                action = args[0]
                self.ui.set_control(action, None)
                self.reinit_menu()


class WaitingForControlMode(UIMode):
    """Mode: controls menu, waiting for a key press."""

    inherit_pause_from_prev_mode = True

    def __init__(self, ui, action):
        self.action = action
        UIMode.__init__(self, ui)

    def init(self):
        self.prompt = HUDMessage(self.ui.menu_font,
                                 "Press a key or ESC to cancel")
        self.on_key(K_PAUSE, self.ui.pause)
        self.on_key(K_ESCAPE, self.return_to_previous_mode)

    def draw(self, screen):
        """Draw extra things pertaining to the mode."""
        self.prev_mode.draw(screen)
        self.prompt.draw(screen)

    def handle_any_other_key(self, event):
        """Handle a KEYDOWN event for unknown keys."""
        self.ui.set_control(self.action, event.key)
        self.prev_mode.reinit_menu()
        self.return_to_previous_mode()

    def handle_mouse_release(self, event):
        """Handle a MOUSEBUTTONUP event."""
        self.return_to_previous_mode()


class GameMenuMode(MenuMode):
    """Mode: in-game menu."""

    paused = True
    inherit_pause_from_prev_mode = False

    def init_menu(self):
        """Initialize the mode."""
        self.menu_items = [
            ('Resume game',     self.close_menu),
            ('Options',         self.ui.options_menu),
            ('Help',            self.ui.help),
            ('End Game',        self.ui.end_game),
        ]


class PlayMode(UIMode):
    """Mode: play the game."""

    paused = False
    music = 'game'

    def init(self):
        """Initialize the mode."""
        self.on_key(K_PAUSE, self.ui.pause)
        self.on_key(K_ESCAPE, self.ui.game_menu)
        self.on_key(K_F1, self.ui.help)
        self.on_key(K_o, self.ui.toggle_missile_orbits)
        self.on_key(K_f, self.ui.toggle_fullscreen)
        self.while_key(K_EQUALS, self.ui.zoom_in)
        self.while_key(K_MINUS, self.ui.zoom_out)
        # Player 1
        self.on_key('P1_TOGGLE_AI', self.ui.toggle_ai, 0)
        self.while_key('P1_LEFT', self.ui.turn_left, 0)
        self.while_key('P1_RIGHT', self.ui.turn_right, 0)
        self.while_key('P1_FORWARD', self.ui.accelerate, 0)
        self.while_key('P1_BACKWARD', self.ui.backwards, 0)
        self.while_key('P1_BRAKE', self.ui.brake, 0)
        self.on_key('P1_FIRE', self.ui.launch_missile, 0)
        # Player 2
        self.on_key('P2_TOGGLE_AI', self.ui.toggle_ai, 1)
        self.while_key('P2_LEFT', self.ui.turn_left, 1)
        self.while_key('P2_RIGHT', self.ui.turn_right, 1)
        self.while_key('P2_FORWARD', self.ui.accelerate, 1)
        self.while_key('P2_BACKWARD', self.ui.backwards, 1)
        self.while_key('P2_BRAKE', self.ui.brake, 1)
        self.on_key('P2_FIRE', self.ui.launch_missile, 1)

    def handle_mouse_release(self, event):
        """Handle a MOUSEBUTTONUP event."""
        if event.button == 1:
            self.ui.game_menu()
        else:
            UIMode.handle_mouse_release(self, event)


class GravityWarsMode(UIMode):
    """Mode: play gravity wars."""

    paused = False
    music = 'gravitywars'

    def init(self):
        """Initialize the mode."""
        self.on_key(K_PAUSE, self.ui.pause)
        self.on_key(K_ESCAPE, self.ui.game_menu)
        self.on_key(K_F1, self.ui.help)
        self.on_key(K_o, self.ui.toggle_missile_orbits)
        self.on_key(K_f, self.ui.toggle_fullscreen)
        self.while_key(K_EQUALS, self.ui.zoom_in)
        self.while_key(K_MINUS, self.ui.zoom_out)
        self.prompt = None
        self.state = self.logic()
        next(self.state)

    def wait_for_input(self, prompt, value):
        """Ask the user to enter a value."""
        self.prompt = HUDInput(self.ui.input_font,
                               "%s (%s): " % (prompt, value))
        while True:
            yield None
            if not self.prompt.text:
                break
            try:
                yield float(self.prompt.text)
            except (ValueError):
                pass

    def logic(self):
        """Game logic."""
        num_players = len(self.ui.ships)
        for ship in self.ui.ships:
            ship.missile_recoil = 0
        for player in itertools.cycle(range(num_players)):
            ship = self.ui.ships[player]
            for value in self.wait_for_input("Player %d, launch angle"
                                             % (player + 1),
                                             ship.direction):
                if value is None:
                    yield None
                else:
                    ship.direction = value
                    break
            for value in self.wait_for_input("Player %d, launch speed"
                                             % (player + 1),
                                             ship.launch_speed):
                if value is None:
                    yield None
                else:
                    ship.launch_speed = value
                    break
            ship.launch()

    def draw(self, screen):
        """Draw extra things pertaining to the mode."""
        if self.prompt is not None:
            self.prompt.draw(screen)

    def handle_mouse_release(self, event):
        """Handle a MOUSEBUTTONUP event."""
        if event.button == 1:
            self.ui.game_menu()
        else:
            UIMode.handle_mouse_press(self, event)

    def handle_any_other_key(self, event):
        """Handle a KEYDOWN event for unknown keys."""
        if self.prompt is not None:
            if event.key == K_RETURN:
                next(self.state)
            elif event.key == K_BACKSPACE:
                self.prompt.text = self.prompt.text[:-1]
            elif event.unicode.isdigit() or event.unicode == '.':
                self.prompt.text += event.unicode


class HelpMode(UIMode):
    """Mode: show on-line help."""

    paused = True
    mouse_visible = True

    def init(self):
        """Initialize the mode."""
        self.on_key(K_f, self.ui.toggle_fullscreen)
        self.on_key(K_ESCAPE, self.return_to_previous_mode)
        self.on_key(K_RETURN, self.next_page)
        self.on_key(K_KP_ENTER, self.next_page)
        self.on_key(K_SPACE, self.next_page)
        self.on_key(K_PAGEDOWN, self.next_page)
        self.on_key(K_PAGEUP, self.prev_page)
        self.help_text = HUDFormattedText(self.ui.help_font,
                                          self.ui.help_bold_font,
                                          fixup_keys_in_text(HELP_TEXT,
                                                             self.ui.controls),
                                          small_font=self.ui.hud_font)

    def draw(self, screen):
        """Draw extra things pertaining to the mode."""
        self.help_text.draw(screen)

    def handle_mouse_release(self, event):
        """Handle a MOUSEBUTTONUP event."""
        if self.help_text.page + 1 == self.help_text.n_pages:
            self.return_to_previous_mode()
        else:
            self.next_page()

    def prev_page(self):
        """Turn to next page"""
        self.help_text.page -= 1

    def next_page(self):
        """Turn to next page"""
        self.help_text.page += 1


class GameUI(object):
    """User interface for the game."""

    ZOOM_FACTOR = 1.25              # Keyboard zoom factor

    MAX_TRAIL = 100                 # Maximum missile trail length

    fullscreen = False              # Start in windowed mode
    fullscreen_mode = None          # Desired video mode (w, h)
    show_missile_trails = True      # Show missile trails by default
    music = True                    # Do we have background music?
    sound = True                    # Do we have sound effects?
    sound_in_vacuum = True          # Can you hear what happens to AI ships?
    show_debug_info = False         # Hide debug info by default
    desired_zoom_level = 1.0        # The desired zoom level

    min_fps = 10                    # Minimum FPS

    ship_colors = [
        (255, 255, 255),            # Player 1 has a white ship
        (127, 255, 0),              # Player 2 has a green ship
    ]

    visibility_margin = 120         # Keep ships >=120px from screen edges

    respawn_animation = 100         # Duration (ticks) of respawn animation

    _ui_mode = None                 # Previous user interface mode

    now_playing = None              # Filename of the current music track

    # Some debug information
    time_to_draw = 0                # Time to draw everything
    time_to_draw_trails = 0         # Time to draw missile trails
    flip_time = 0                   # Time to draw debug info & flip
    total_time = 0                  # Time to process a frame
    last_time = None                # Timestamp of last frame

    def __init__(self):
        self.rng = random.Random()
        self.controls = {}
        for action in DEFAULT_CONTROLS:
            self.controls[action] = [None]
        self.rev_controls = {}
        for action, key in DEFAULT_CONTROLS.items():
            self.set_control(action, key)

    def get_settings_filename(self, filename=None):
        """Determine the filename for the settings file."""
        if not filename:
            filename = os.path.expanduser('~/.pyspacewarrc')
        return filename

    def load_settings(self, filename=None):
        """Load settings from a configuration file."""
        filename = self.get_settings_filename(filename)
        config = self.get_config_parser()
        config.read([filename])
        self.fullscreen = config.getboolean('video', 'fullscreen')
        mode = config.get('video', 'mode')
        try:
            w, h = mode.split('x')
            self.fullscreen_mode = int(w), int(h)
        except ValueError:
            self.fullscreen_mode = None
        self.show_missile_trails = config.getboolean('video',
                                                     'show_missile_trails')
        self.music = config.getboolean('sound', 'music')
        self.sound = config.getboolean('sound', 'sound')
        self.sound_in_vacuum = config.getboolean('sound', 'sound_in_vacuum')
        for action in self.controls:
            key = config.get('controls', action)
            if key:
                # clear all current keys first
                self.set_control(action, None)
            for key in key.split():
                try:
                    key = int(key)
                except ValueError:
                    key = None
                self.set_control(action, key)

    def save_settings(self, filename=None):
        """Save settings to a configuration file."""
        filename = self.get_settings_filename(filename)
        config = self.get_config_parser()
        with open(filename, 'w') as f:
            config.write(f)

    def get_config_parser(self):
        """Create a ConfigParser initialized with current settings."""
        config = ConfigParser()
        config.add_section('video')
        config.set('video', 'fullscreen', str(self.fullscreen))
        if self.fullscreen_mode:
            config.set('video', 'mode', '%dx%d' % self.fullscreen_mode)
        else:
            config.set('video', 'mode', '')
        config.set('video', 'show_missile_trails',
                   str(self.show_missile_trails))
        config.add_section('sound')
        config.set('sound', 'music', str(self.music))
        config.set('sound', 'sound', str(self.sound))
        config.set('sound', 'sound_in_vacuum', str(self.sound_in_vacuum))
        config.add_section('controls')
        for action, keys in self.controls.items():
            config.set('controls', action, ' '.join(map(str, keys)))
        return config

    def init(self):
        """Initialize the user interface."""
        self.version = version
        self.version_text = 'PySpaceWar version %s' % self.version
        self._init_pygame()
        self._init_trail_colors()
        self._load_sounds()
        self._load_music()
        self._load_planet_images()
        self._load_background()
        self._init_fonts()
        self._set_display_mode()
        self._optimize_images()
        self.viewport = Viewport(self.screen)
        self.frame_counter = FrameRateCounter()
        self.framedrop_needed = False
        self.ui_mode = TitleMode(self)
        self._new_game(0)

    def _set_ui_mode(self, new_ui_mode):
        prev_mode = self._ui_mode
        if prev_mode is not None:
            prev_mode.leave(new_ui_mode)
        self._ui_mode = new_ui_mode
        self._ui_mode.enter(prev_mode)

    ui_mode = property(lambda self: self._ui_mode, _set_ui_mode)

    def _init_trail_colors(self):
        """Precalculate missile trail gradients."""
        self.trail_colors = {}
        for appearance, color in enumerate(self.ship_colors):
            self.trail_colors[appearance] = [[], ]
            r, g, b = color
            r1, g1, b1 = r*.1, g*.1, b*.1
            r2, g2, b2 = r*.5, g*.5, b*.5
            for n in range(1, self.MAX_TRAIL+1):
                dr, dg, db = (r2-r1) / n, (g2-g1) / n, (b2-b1) / n
                colors_for_length_n = [
                    (int(r1+dr*i), int(g1+dg*i), int(b1+db*i))
                    for i in range(n)]
                self.trail_colors[appearance].append(colors_for_length_n)

    def _init_pygame(self):
        """Initialize pygame, but don't create an output window just yet."""
        pygame.init()
        pygame.display.set_caption('PySpaceWar')
        icon = pygame.image.load(find('icons', 'pyspacewar48.png'))
        pygame.display.set_icon(icon)
        pygame.mouse.set_visible(False)
        if not self.fullscreen_mode:
            self.fullscreen_mode = self._choose_best_mode()
        self.sound_available = bool(pygame.mixer.get_init())
        if not self.sound_available:
            # Try again, at least we'll get an error message, maybe?
            try:
                pygame.mixer.init()
            except pygame.error as e:
                print("pyspacewar: disabling sound: %s" % e)
            else:
                self.sound_available = True

    def _choose_best_mode(self):
        """Choose a suitable display mode."""
        # Previously this function used to pick the largest sane video mode
        # Sadly, my laptop is not fast enough to sustain 20 fps at 1024x768
        # when there are too many missiles around.
        return (800, 600)

    def _set_display_mode(self, _depth=0):
        """Set display mode."""
        if self.fullscreen:
            # Consider using DOUBLEBUF and HWSURFACE flags here
            # http://aspn.activestate.com/ASPN/Mail/Message/pygame-users/2793695
            # On the other hand, alpha-blended blits are reportedly slow on
            # hardware surfaces, and there are other sorts of problems too:
            # http://aspn.activestate.com/ASPN/Mail/Message/pygame-users/1825852
            # According to my measurements, using HWSURFACE|DOUBLEBUF had no
            # impact on pygame.display.flip() time.
            self.screen = pygame.display.set_mode(self.fullscreen_mode,
                                                  FULLSCREEN)
        else:
            w, h = self.fullscreen_mode
            windowed_mode = (int(w * 0.8), int(h * 0.8))
            self.screen = pygame.display.set_mode(windowed_mode, RESIZABLE)
        self._prepare_background()
        if self.screen.get_bitsize() >= 24:
            # Only 24 and 32 bpp modes support aaline
            self.draw_line = pygame.draw.aaline
        else:
            self.draw_line = pygame.draw.line

    def _resize_window(self, size):
        """Resize the PyGame window as requested."""
        self.screen = pygame.display.set_mode(size, RESIZABLE)
        self._prepare_background()

    def _optimize_images(self):
        """Convert loaded images to native format for faster blitting.

        Must be called after _set_display_mode, and, of course, after
        _load_planet_images.
        """
        self.planet_images = [img.convert_alpha()
                              for img in self.planet_images]

    def _load_planet_images(self):
        """Load bitmaps of planets."""
        self.planet_images = [
            pygame.image.load(img)
            for img in glob.glob(find('images', 'planet*.png'))
        ]
        if not self.planet_images:  # pragma: nocover
            raise RuntimeError("Could not find planet bitmaps")

    def _load_background(self):
        """Load background bitmap."""
        self.background = pygame.image.load(find('images',
                                                 'background.jpg'))
        self.background_surface = None

    def _prepare_background(self):
        """Prepare a background surface."""
        if self.background_surface is None:
            self.background_surface = self.background.convert()
        w, h = self.background_surface.get_size()
        screen_w, screen_h = self.screen.get_size()
        if w != screen_w or h != screen_h:
            scaled = pygame.transform.scale(self.background,
                                            (screen_w, screen_h))
            # The call to surface.convert dramatically affects performance
            # of subsequent blits
            self.background_surface = scaled.convert()

    _sound_effect_names = [
        'thruster', 'fire', 'bounce', 'hit', 'explode', 'respawn', 'menu',
    ]

    def _load_sounds(self):
        """Load sound effects."""
        self.sounds = {}
        self.sound_looping = set()
        if not self.sound_available:
            return
        config = ConfigParser()
        config.add_section('sounds')
        config.read([find('sounds', 'sounds.ini')])
        for name in self._sound_effect_names:
            if config.has_option('sounds', name):
                filename = config.get('sounds', name)
                if filename:
                    try:
                        sound = pygame.mixer.Sound(find('sounds', filename))
                        self.sounds[name] = sound
                    except pygame.error:
                        print("pyspacewar: could not load %s" % filename)
        if 'thruster' in self.sounds:
            self.sounds['thruster'].set_volume(0.5)

    def _load_music(self):
        """Load music files."""
        self.music_files = {}
        if not self.sound_available:
            return
        config = ConfigParser()
        config.add_section('music')
        config.read([find('music', 'music.ini')])
        for what in ['demo', 'game', 'gravitywars']:
            if config.has_option('music', what):
                filename = config.get('music', what)
                if filename:
                    self.music_files[what] = find('music', filename)

    def play_music(self, which, restart=False):
        """Loop the music file for a certain mode."""
        if not self.sound_available:
            return
        if which == self.now_playing and not restart:
            return
        self.now_playing = which
        if not self.music:
            return
        filename = self.music_files.get(which)
        if not filename:
            pygame.mixer.music.stop()
        else:
            try:
                pygame.mixer.music.load(filename)
                pygame.mixer.music.play(-1)
            except pygame.error:
                print("pyspacewar: could not load %s" % filename)
                pygame.mixer.music.stop()

    def play_sound(self, which):
        """Play a certain sound effect."""
        if which in self.sounds and self.sound:
            self.sounds[which].play()

    def start_sound(self, which):
        """Start looping a certain sound effect."""
        if which not in self.sound_looping and which in self.sounds:
            if self.sound:
                self.sounds[which].play(-1)
            self.sound_looping.add(which)

    def stop_sound(self, which):
        """Stop playing a certain sound effect."""
        if which in self.sound_looping:
            self.sounds[which].stop()
            self.sound_looping.remove(which)

    def _init_fonts(self):
        """Load fonts."""
        font = find('fonts', 'NotoSans-Regular.ttf')
        bold_font = find('fonts', 'NotoSans-Bold.ttf')
        self.hud_font = pygame.font.Font(font, 14)
        self.help_font = pygame.font.Font(font, 16)
        self.help_bold_font = pygame.font.Font(bold_font, 16)
        self.input_font = pygame.font.Font(font, 24)
        self.menu_font = pygame.font.Font(bold_font, 30)

    def _new_game(self, players=1):
        """Start a new game."""
        self.game = Game.new(ships=2,
                             planet_kinds=len(self.planet_images),
                             rng=self.rng)
        self.ships = self.game.ships
        for ship in self.ships:
            ship.launch_effect = self.launch_effect_Ship
            ship.bounce_effect = self.bounce_effect_Ship
            ship.hit_effect = self.hit_effect_Ship
            ship.explode_effect = self.explode_effect_Ship
            ship.respawn_effect = self.respawn_effect_Ship
        self.ai = [AIController(ship) for ship in self.ships]
        self.ai_controlled = [False] * len(self.ships)
        self.missile_trails = {}
        self.angular_momentum = {}
        self.viewport.origin = (self.ships[0].position +
                                self.ships[1].position) / 2
        self.viewport.scale = 1
        self.desired_zoom_level = 1
        self._init_hud()
        if players == 0:  # demo mode
            self.toggle_ai(0)
            self.toggle_ai(1)
        elif players == 1:  # player vs computer
            self.toggle_ai(1)
        else:  # player vs player
            pass

    def _count_trails(self):
        """Count the number of pixels in missile trails."""
        return sum(len(trail) for trail in self.missile_trails.values())

    def _init_hud(self):
        """Initialize the heads-up display."""
        time_format = '%.f ms'
        self.fps_hud1 = HUDInfoPanel(
            self.hud_font, 16, xalign=0.5, yalign=0,
            content=[
                ('objects', lambda: len(self.game.world.objects)),
                ('missile trails', self._count_trails),
                ('fps', lambda: '%.0f' % self.frame_counter.fps()),
            ])
        self.fps_hud2 = HUDCollection([
            HUDInfoPanel(
                self.hud_font, 16, xalign=0.25, yalign=0.95,
                content=[
                    ('update', lambda: time_format %
                     (self.game.time_to_update * 1000)),
                    ('  gravity', lambda: time_format %
                     (self.game.world.time_for_gravitation * 1000)),
                    ('  collisions', lambda: time_format %
                     (self.game.world.time_for_collisions * 1000)),
                    ('  other', lambda: time_format %
                     ((self.game.time_to_update
                       - self.game.world.time_for_gravitation
                       - self.game.world.time_for_collisions)
                      * 1000)),
                ]),
            HUDInfoPanel(
                self.hud_font, 16, xalign=0.5, yalign=0.95,
                content=[
                    ('draw', lambda: time_format %
                     (self.time_to_draw * 1000)),
                    ('  trails', lambda: time_format %
                     (self.time_to_draw_trails * 1000)),
                    ('  other', lambda: time_format %
                     ((self.time_to_draw - self.time_to_draw_trails) * 1000)),
                    ('    flip', lambda: time_format %
                     (self.flip_time * 1000)),
                ]),
            HUDInfoPanel(
                self.hud_font, 16, xalign=0.75, yalign=0.95,
                content=[
                    ('other', lambda: time_format %
                     ((self.total_time - self.game.time_to_update
                       - self.time_to_draw - self.game.time_waiting)
                      * 1000)),
                    ('idle', lambda: time_format %
                     (self.game.time_waiting * 1000)),
                    ('total', lambda: time_format %
                     (self.total_time * 1000)),
                ]),
        ])
        self.hud = HUDCollection([
            HUDShipInfo(self.ships[0], self.hud_font, 1, 0),
            HUDShipInfo(self.ships[1], self.hud_font, 0, 0,
                        HUDShipInfo.GREEN_COLORS),
            HUDCompass(self.game.world, self.ships[0], self.viewport, 1, 1,
                       HUDCompass.BLUE_COLORS),
            HUDCompass(self.game.world, self.ships[1], self.viewport, 0, 1,
                       HUDCompass.GREEN_COLORS),
        ])

    def _keep_ships_visible(self):
        """Update viewport origin/scale so that all ships are on screen."""
        self.viewport.scale = self.desired_zoom_level
        self.viewport.keep_visible([s.position for s in self.ships],
                                   self.visibility_margin)

    def interact(self):
        """Process pending keyboard/mouse events."""
        for event in pygame.event.get():
            if event.type == QUIT:
                self.quit()
            elif event.type == VIDEORESIZE:
                self._resize_window(event.size)
            elif event.type == KEYDOWN:
                if event.key == K_F12:
                    self.toggle_debug_info()
                elif (event.key in (K_RETURN, K_KP_ENTER) and
                      event.mod & KMOD_ALT):
                    self.toggle_fullscreen()
                else:
                    self.ui_mode.handle_key_press(event)
            elif event.type == MOUSEBUTTONDOWN:
                self.ui_mode.handle_mouse_press(event)
            elif event.type == MOUSEBUTTONUP:
                self.ui_mode.handle_mouse_release(event)
            elif event.type == MOUSEMOTION:
                self.ui_mode.handle_mouse_motion(event)
        pressed = pygame.key.get_pressed()
        self.ui_mode.handle_held_keys(pressed)
        self.update_continuous_sounds()

    def quit(self):
        """Exit the game."""
        sys.exit(0)

    def pause(self):
        """Pause whatever is happening (so I can take a screenshot)."""
        self.ui_mode = PauseMode(self)

    def main_menu(self):
        """Enter the main menu."""
        self.play_sound('menu')
        self.ui_mode = MainMenuMode(self)

    def new_game_menu(self):
        """Enter the new game menu."""
        self.ui_mode = NewGameMenuMode(self)

    def options_menu(self):
        """Enter the options menu."""
        self.ui_mode = OptionsMenuMode(self)

    def video_options_menu(self):
        """Enter the video options menu."""
        self.ui_mode = VideoOptionsMenuMode(self)

    def sound_options_menu(self):
        """Enter the sound options menu."""
        self.ui_mode = SoundOptionsMenuMode(self)

    def screen_resolution_menu(self):
        """Enter the screen resolution menu."""
        self.ui_mode = ScreenResolutionMenuMode(self)

    def controls_menu(self):
        """Enter the controls menu."""
        self.ui_mode = ControlsMenuMode(self)

    def watch_demo(self):
        """Go back to demo mode."""
        self.ui_mode = DemoMode(self)

    def start_single_player_game(self):
        """Start a new single-player game."""
        self._new_game(1)
        self.ui_mode = PlayMode(self)

    def start_two_player_game(self):
        """Start a new two-player game."""
        self._new_game(2)
        self.ui_mode = PlayMode(self)

    def start_gravity_wars(self):
        """Start a new two-player gravity wars game."""
        self._new_game(2)
        self.ui_mode = GravityWarsMode(self)

    def help(self):
        """Show the help screen."""
        self.ui_mode = HelpMode(self)

    def game_menu(self):
        """Enter the game menu."""
        self.play_sound('menu')
        self.ui_mode = GameMenuMode(self)

    def resume_game(self):
        """Resume a game in progress."""
        self.ui_mode = PlayMode(self)

    def end_game(self):
        """End the game in progress."""
        self._new_game(0)
        self.watch_demo()
        self.ui_mode = MainMenuMode(self)

    def toggle_fullscreen(self):
        """Toggle fullscreen mode."""
        self.fullscreen = not self.fullscreen
        self._set_display_mode()

    def switch_to_mode(self, mode):
        """Toggle fullscreen mode."""
        self.fullscreen_mode = mode
        self._set_display_mode()

    def set_control(self, action, key):
        """Change a key mapping"""
        if key in self.rev_controls:
            old_action = self.rev_controls[key]
            self.controls[old_action].remove(key)
            if not self.controls[old_action]:
                self.controls[old_action] = [None]
        keys = self.controls[action]
        if len(keys) > 1 or key is None or keys == [None]:
            for old_key in keys:
                if old_key is not None:
                    del self.rev_controls[old_key]
            self.controls[action] = []
        self.controls[action].append(key)
        if key is not None:
            self.rev_controls[key] = action

    def zoom_in(self):
        """Zoom in."""
        self.desired_zoom_level = self.viewport.scale * self.ZOOM_FACTOR

    def zoom_out(self):
        """Zoom in."""
        self.desired_zoom_level = self.viewport.scale / self.ZOOM_FACTOR

    def toggle_debug_info(self):
        """Show/hide debug info."""
        self.show_debug_info = not self.show_debug_info

    def toggle_missile_orbits(self):
        """Show/hide missile trails."""
        self.show_missile_trails = not self.show_missile_trails

    def toggle_music(self):
        """Toggle music."""
        self.music = not self.music
        if not self.sound_available:
            return
        if self.music:
            self.play_music(self.now_playing, restart=True)
        else:
            pygame.mixer.music.stop()

    def toggle_sound(self):
        """Toggle sound effects."""
        self.sound = not self.sound
        for sound in self.sound_looping:
            if self.sound:
                self.sounds[sound].play(-1)
            else:
                self.sounds[sound].stop()

    def toggle_sound_in_vacuum(self):
        """Toggle sound in vacuum."""
        self.sound_in_vacuum = not self.sound_in_vacuum

    def toggle_ai(self, player_id):
        """Toggle AI control for player."""
        self.ai_controlled[player_id] = not self.ai_controlled[player_id]
        if self.ai_controlled[player_id]:
            self.game.controllers.append(self.ai[player_id])
        else:
            self.game.controllers.remove(self.ai[player_id])

    def turn_left(self, player_id):
        """Manual ship control: turn left."""
        if not self.ai_controlled[player_id]:
            self.ships[player_id].turn_left()

    def turn_right(self, player_id):
        """Manual ship control: turn right."""
        if not self.ai_controlled[player_id]:
            self.ships[player_id].turn_right()

    def accelerate(self, player_id):
        """Manual ship control: accelerate."""
        if not self.ai_controlled[player_id]:
            self.ships[player_id].accelerate()

    def backwards(self, player_id):
        """Manual ship control: accelerate backwards."""
        if not self.ai_controlled[player_id]:
            self.ships[player_id].backwards()

    def brake(self, player_id):
        """Manual ship control: brake."""
        if not self.ai_controlled[player_id]:
            self.ships[player_id].brake()

    def launch_missile(self, player_id):
        """Manual ship control: launch a missile."""
        if not self.ai_controlled[player_id]:
            self.ships[player_id].launch()

    def launch_effect_Ship(self, ship, obstacle):
        """Play a sound effect when the player's ship bounces off something."""
        player_id = self.ships.index(ship)
        if not self.ai_controlled[player_id] or self.sound_in_vacuum:
            self.play_sound('fire')

    def bounce_effect_Ship(self, ship, obstacle):
        """Play a sound effect when the player's ship bounces off something."""
        player_id = self.ships.index(ship)
        if not ship.dead:
            # It sounds weird to hear that sound when dead ships bounce
            if not self.ai_controlled[player_id] or self.sound_in_vacuum:
                self.play_sound('bounce')

    def hit_effect_Ship(self, ship, missile):
        """Play a sound effect when the player's ship is hit."""
        player_id = self.ships.index(ship)
        if not self.ai_controlled[player_id] or self.sound_in_vacuum:
            self.play_sound('hit')

    def explode_effect_Ship(self, ship, killer):
        """Play a sound effect when the player's ship explodes."""
        player_id = self.ships.index(ship)
        if not self.ai_controlled[player_id] or self.sound_in_vacuum:
            self.play_sound('explode')

    def respawn_effect_Ship(self, ship):
        """Play a sound effect when the player's ship respawns."""
        self.play_sound('respawn')

    def update_continuous_sounds(self):
        """Loop certain sound effects while certain conditions hold true."""
        makes_noise = False
        for player_id, ship in enumerate(self.ships):
            if not self.ai_controlled[player_id] or self.sound_in_vacuum:
                makes_noise = (ship.forward_thrust or ship.rear_thrust or
                               ship.left_thrust or ship.right_thrust or
                               ship.engage_brakes) or makes_noise
        if makes_noise:
            self.start_sound('thruster')
        else:
            self.stop_sound('thruster')

    def draw(self):
        """Draw the state of the game"""
        self.time_to_draw = 0
        self.time_to_draw_trails = 0
        drop_this_frame = (self.framedrop_needed and
                           self.frame_counter.notional_fps() >= self.min_fps)
        if not drop_this_frame:
            start = time.time()
            self._keep_ships_visible()
            self.screen.blit(self.background_surface, (0, 0))
            if self.show_missile_trails:
                self.draw_missile_trails()
            for obj in self.game.world.objects:
                getattr(self, 'draw_' + obj.__class__.__name__)(obj)
            self.hud.draw(self.screen)
            self.ui_mode.draw(self.screen)
            self.time_to_draw = time.time() - start
            self.frame_counter.frame()
        now = time.time()
        if self.last_time is not None:
            self.total_time = now - self.last_time
        self.last_time = now
        if self.show_debug_info:
            self.fps_hud1.draw(self.screen)
            if not drop_this_frame:
                self.fps_hud2.draw(self.screen)
        now = time.time()
        pygame.display.flip()
        self.flip_time = time.time() - now

    def draw_Planet(self, planet):
        """Draw a planet."""
        pos = self.viewport.screen_pos(planet.position)
        size = self.viewport.screen_len(planet.radius * 2)
        unscaled_img = self.planet_images[planet.appearance]
        img = pygame.transform.scale(unscaled_img, (size, size))
        self.screen.blit(img, (pos[0] - size/2, pos[1] - size/2))

    def draw_Ship(self, ship):
        """Draw a ship."""
        color = self.ship_colors[ship.appearance]
        if ship.dead:
            ratio = self.game.time_to_respawn(ship) / self.game.respawn_time
            color = colorblend(color, (0x20, 0x20, 0x20), 0.2)
            color = colorblend(color, (0, 0, 0), ratio)
        elif self.game.world.time - ship.spawn_time < self.respawn_animation:
            self.draw_Ship_spawn_animation(ship)
        direction_vector = ship.direction_vector * ship.size
        side_vector = direction_vector.perpendicular()
        sp = self.viewport.screen_pos
        pt1 = sp(ship.position - direction_vector + side_vector * 0.5)
        pt2 = sp(ship.position + direction_vector)
        pt3 = sp(ship.position - direction_vector - side_vector * 0.5)
        self.draw_line(self.screen, color, pt1, pt2)
        self.draw_line(self.screen, color, pt2, pt3)
        (front, back, left_front, left_back,
         right_front, right_back) = self.calc_Ship_thrusters(ship)
        thrust_lines = []
        if back:
            thrust_lines.append(((-0.1, -0.9), (-0.1, -0.9-back)))
            thrust_lines.append(((+0.1, -0.9), (+0.1, -0.9-back)))
        if front:
            thrust_lines.append(((-0.6, -0.2), (-0.6, -0.2+front)))
            thrust_lines.append(((+0.6, -0.2), (+0.6, -0.2+front)))
        if left_front:
            thrust_lines.append(((-0.2, +0.8), (-0.2-left_front, +0.8)))
        if right_front:
            thrust_lines.append(((+0.2, +0.8), (+0.2+right_front, +0.8)))
        if left_back:
            thrust_lines.append(((-0.6, -0.8), (-0.6-left_back, -0.8)))
        if right_back:
            thrust_lines.append(((+0.6, -0.8), (+0.6+right_back, -0.8)))
        for (s1, d1), (s2, d2) in thrust_lines:
            pt1 = sp(ship.position + direction_vector * d1 + side_vector * s1)
            pt2 = sp(ship.position + direction_vector * d2 + side_vector * s2)
            self.draw_line(self.screen, (255, 120, 20), pt1, pt2)

    def calc_Ship_thrusters(self, ship):
        """Calculate the output of the ship's thrusters.

        Returns (front, back, left_front, left_back, right_front, right_back)
        where each value is the ratio of world units to the ship size.

        Keeps track of the ship's rotation and only shows turn thrusters firing
        if there was any change.  Updates self.angular_momentum as a side
        effect.
        """
        front = back = left_front = left_back = right_front = right_back = 0
        if ship.forward_thrust:
            back += ship.forward_thrust * 0.3 / ship.forward_power
        if ship.rear_thrust:
            front += ship.rear_thrust * 0.15 / ship.backward_power
        rotation = ship.left_thrust - ship.right_thrust
        prev_rotation = self.angular_momentum.get(ship, 0)
        self.angular_momentum[ship] = rotation
        if rotation > prev_rotation:
            amount = (rotation - prev_rotation) * 0.15 / ship.rotation_speed
            left_back += amount
            right_front += amount
        elif rotation < prev_rotation:
            amount = (prev_rotation - rotation) * 0.15 / ship.rotation_speed
            left_front += amount
            right_back += amount
        if ship.engage_brakes:
            delta_v = ship.velocity * (ship.brake_factor - 1)
            front_back_proj = delta_v.dot_product(ship.direction_vector)
            front_back_proj *= 0.45 / (ship.forward_power+ship.backward_power)
            if front_back_proj > 0:
                back += front_back_proj
            elif front_back_proj < 0:
                front -= front_back_proj
            left_right_proj = delta_v.dot_product(
                                        ship.direction_vector.perpendicular())
            left_right_proj *= 0.45 / (ship.forward_power+ship.backward_power)
            if left_right_proj > 0:
                left_front += left_right_proj
                left_back += left_right_proj
            elif left_right_proj < 0:
                right_front -= left_right_proj
                right_back -= left_right_proj
        # Very high accelerations (caused by braking or the AI code) look
        # slightly ridiculous.  Clamp all the values
        front = min(front, 0.2)
        back = min(back, 0.4)
        left_front = min(left_front, 0.2)
        left_back = min(left_back, 0.2)
        right_front = min(right_front, 0.2)
        right_back = min(right_back, 0.2)
        return (front, back, left_front, left_back, right_front, right_back)

    def draw_Ship_spawn_animation(self, ship):
        sp = self.viewport.screen_pos(ship.position)
        color = self.ship_colors[ship.appearance]
        t = math.sqrt((self.game.world.time - ship.spawn_time)
                      / self.respawn_animation)
        radius = linear(t, 1, 1, 100)
        color = colorblend((0, 0, 0), color, linear(t, 1, 0.2, 0.9))
        pygame.draw.circle(self.screen, color, sp, int(radius), 1)

    def update_missile_trails(self):
        """Update missile trails."""
        for missile, trail in list(self.missile_trails.items()):
            if missile.world is None:
                del trail[:2]
                if not trail:
                    del self.missile_trails[missile]
            else:
                trail.append(missile.position)
                if len(trail) > self.MAX_TRAIL:
                    del trail[0]
        for obj in self.game.world.objects:
            if isinstance(obj, Missile) and obj not in self.missile_trails:
                self.missile_trails[obj] = [obj.position]

    def draw_missile_trails(self):
        """Draw missile trails."""
        start = time.time()
        for missile, trail in self.missile_trails.items():
            self.draw_missile_trail(missile, trail)
        self.time_to_draw_trails = time.time() - start

    def draw_missile_trail(self, missile, trail):
        """Draw a missile orbit trail."""
        r, g, b = self.ship_colors[missile.appearance]
        gradient = self.trail_colors[missile.appearance][len(trail)]
        self.viewport.draw_trail(trail, gradient, self.screen.set_at)

    def draw_Missile(self, missile):
        """Draw a missile."""
        color = self.ship_colors[missile.appearance]
        x, y = self.viewport.screen_pos(missile.position)
        self.screen.set_at((x, y), color)
        if self.viewport.scale > 0.5:
            color = colorblend(color, (0, 0, 0), 0.4)
            self.screen.set_at((x+1, y), color)
            self.screen.set_at((x, y+1), color)
            self.screen.set_at((x-1, y), color)
            self.screen.set_at((x, y-1), color)

    def draw_Debris(self, debris):
        """Draw debris."""
        self.screen.set_at(self.viewport.screen_pos(debris.position),
                           debris.appearance)

    def wait_for_tick(self):
        """Wait for the next game time tick.  World moves during this time."""
        if self.ui_mode.paused:
            self.game.skip_a_tick()
            self.framedrop_needed = False
        else:
            self.update_missile_trails()
            self.framedrop_needed = not self.game.wait_for_tick()
