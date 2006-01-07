"""
Graphical user interface for PySpaceWar

$Id$
"""

import os
import sys
import sets
import glob
import time
import random
import itertools

import pygame
from pygame.locals import *

from world import Vector, Ship, Missile
from game import Game
from ai import AIController


MODIFIER_KEYS = sets.Set([K_NUMLOCK, K_NUMLOCK, K_CAPSLOCK, K_SCROLLOCK,
                          K_RSHIFT, K_LSHIFT, K_RCTRL, K_LCTRL, K_RALT, K_LALT,
                          K_RMETA, K_LMETA, K_LSUPER, K_RSUPER, K_MODE])


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
    return (int(alpha*r1+beta*r2), int(alpha*g1+beta*g2), int(alpha*b1+beta*b2))


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

    def list_of_screen_pos(self, list_of_world_pos):
        """Convert world coordinates to screen coordinates."""
        return [(int(self._screen_x + x * self._scale),
                 int(self._screen_y - y * self._scale))
                for x, y in list_of_world_pos]

    def world_pos(self, screen_pos):
        """Convert screen coordinates into world coordinates."""
        x = (screen_pos[0] - self._screen_x) / self._scale
        y = -(screen_pos[1] - self._screen_y) / self._scale
        return (x, y)

    def in_screen(self, world_pos):
        """Is a position visible on screen?"""
        xmin, ymin, xmax, ymax = self.world_bounds
        return xmin <= world_pos[0] <= xmax and ymin <= world_pos[1] <= ymax

    def shift_by_pixels(self, (delta_x, delta_y)):
        """Shift the origin by a given number of screen pixels."""
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

    def __init__(self):
        self.frames = []

    def frame(self):
        """Tell the counter that a new frame has just been drawn."""
        self.frames.append(pygame.time.get_ticks())
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
        frames = len(self.frames) - 1
        return frames * 1000.0 / ms

    def notional_fps(self):
        """Calculate the frame rate assuming that I'm about to draw a frame.

        Returns 0 if not enough frames have been drawn yet.
        """
        if len(self.frames) < 1:
            return 0.0
        ms = pygame.time.get_ticks() - self.frames[0]
        frames = len(self.frames)
        return frames * 1000.0 / ms


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
        self.draw_rows(surface,
                ('direction', '%d' % self.ship.direction),
                ('heading', '%d' % self.ship.velocity.direction()),
                ('speed', '%.1f' % self.ship.velocity.length()),
                ('frags', '%d' % self.ship.frags),)
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
        x = y = self.radius
        self.surface.fill((1, 1, 1))
        self.surface.set_colorkey((1, 1, 1))
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
        pygame.draw.aaline(self.surface, self.fgcolor2, (x, y), (x2, y2))

        v = self.ship.velocity * self.velocity_scale
        if v.length() > self.radius * 0.9:
            v = v.scaled(self.radius * 0.9)
        x2 = x + int(v.x)
        y2 = y - int(v.y)
        pygame.draw.aaline(self.surface, self.fgcolor1, (x, y), (x2, y2))

        surface.blit(self.surface, self.position(surface))


class HUDTitle(HUDElement):
    """Fading out title."""

    def __init__(self, image, xalign=0.5, yalign=0.25):
        HUDElement.__init__(self, image.get_width(), image.get_height(),
                            xalign, yalign)
        self.image = image
        self.alpha = 255
        try:
            import Numeric
        except ImportError:
            self.image = self.image.convert()
            self.image.set_colorkey((0, 0, 0))
            self.draw = self.draw_plainly
        else:
            self.mask = pygame.surfarray.array_alpha(image).astype(Numeric.Int)
            self.draw = self.draw_using_Numeric

    def draw_plainly(self, surface):
        """Draw the element.

        Uses a color key and surface alpha, as an approximation of smooth fade
        out.
        """
        if self.alpha < 1:
            return
        x, y = self.position(surface)
        self.image.set_alpha(self.alpha)
        surface.blit(self.image, (x, y))
        self.alpha *= 0.95

    def draw_using_Numeric(self, surface):
        """Draw the element.

        Scales the picture alpha channel smoothly using NumPy.
        """
        if self.alpha < 1:
            return
        import Numeric
        x, y = self.position(surface)
        array = pygame.surfarray.pixels_alpha(self.image)
        array[:] = (self.mask * self.alpha / 255).astype(Numeric.UnsignedInt8)
        surface.blit(self.image, (x, y))
        self.alpha *= 0.95


class HUDMenu(HUDElement):
    """A menu."""

    normal_fg_color = (220, 255, 64)
    normal_bg_color = (120, 24, 24)
    selected_fg_color = (255, 255, 220)
    selected_bg_color = (210, 48, 48)

    def __init__(self, font, items, xalign=0.5, yalign=0.5,
                 xpadding=32, ypadding=8, yspacing=16):
        width = max([font.size(item)[0] for item in items]) + 2*xpadding
        item_height = max([font.size(item)[1] for item in items]) + 2*ypadding
        height = max(0, (item_height + yspacing) * len(items) - yspacing)
        HUDElement.__init__(self, width, height, xalign, yalign)
        self.font = font
        self.items = items
        self.yspacing = yspacing
        self.xpadding = xpadding
        self.ypadding = ypadding
        self.selected_item = 0
        self.item_height = item_height
        self.surface = pygame.Surface((self.width, self.height))
        self.surface.set_alpha(255 * 0.9)
        self.surface.set_colorkey((1, 1, 1))
        self._draw()

    def find(self, surface, (x, y)):
        """Find the item at given coordinates."""
        ix, iy = self.position(surface)
        for idx, item in enumerate(self.items):
            if (ix <= x < ix + self.width and
                iy <= y < iy + self.item_height):
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
            img = self.font.render(item, True, fg_color)
            self.surface.fill(bg_color, (x, y, self.width, self.item_height))
            self.surface.blit(img,
                              (x + (self.width - img.get_width())/2,
                               y + (self.item_height - img.get_height())/2))
            for ax in (0, self.width-1):
                for ay in (0, self.item_height-1):
                    self.surface.set_at((x+ax, y+ay), (1, 1, 1))
            y += self.item_height + self.yspacing

    def draw(self, surface):
        """Draw the element."""
        if self.selected_item != self._drawn_with:
            self._draw()
        x, y = self.position(surface)
        surface.blit(self.surface, (x, y))


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


class UIMode(object):
    """Mode of user interface.

    The mode determines several things:
      - what is displayed on screen
      - whether the game progresses
      - how keystrokes are interpreted

    Examples of modes: game play, paused, navigating a menu.
    """

    paused = False

    def __init__(self, ui):
        self.ui = ui
        self.clear_keymap()
        self.init()

    def init(self):
        """Initialize the mode."""
        pass

    def enter(self, prev_mode=None):
        """Enter the mode."""
        pass

    def leave(self, next_mode=None):
        """Leave the mode."""
        pass

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
        handler_and_args = self._keymap_once.get(event.key)
        if handler_and_args:
            handler, args = handler_and_args
            handler(*args)
        elif event.key not in self._keymap_repeat:
            self.handle_any_other_key(event)

    def handle_any_other_key(self, event):
        """Handle a KEYDOWN event for unknown keys."""
        pass

    def handle_held_keys(self, pressed):
        """Handle any keys that are pressed."""
        for key, (handler, args) in self._keymap_repeat.items():
            if pressed[key]:
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


class DemoMode(UIMode):
    """Mode: demo."""

    paused = False

    def init(self):
        """Initialize the mode."""
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

    def draw(self, screen):
        """Draw extra things pertaining to the mode."""
        self.title.draw(screen)
        if self.title.alpha < 1:
            self.ui.watch_demo()


class MenuMode(UIMode):
    """Abstract base class for menu modes."""

    def init(self):
        """Initialize the mode."""
        self.init_menu()
        self.menu = HUDMenu(self.ui.menu_font,
                            [item[0] for item in self.menu_items])
        self.on_key(K_UP, self.select_prev_item)
        self.on_key(K_DOWN, self.select_next_item)
        self.on_key(K_RETURN, self.activate_item)
        self.on_key(K_KP_ENTER, self.activate_item)
        # These might be overkill
        self.while_key(K_EQUALS, self.ui.zoom_in)
        self.while_key(K_MINUS, self.ui.zoom_out)
        self.on_key(K_o, self.ui.toggle_missile_orbits)
        self.on_key(K_f, self.ui.toggle_fullscreen)

    def init_menu(self):
        """Initialize the menu."""
        self.menu_items = [
            ('Quit',            self.ui.quit),
        ]

    def enter(self, prev_mode=None):
        """Enter the mode."""
        pygame.mouse.set_visible(True)
        self.prev_mode = prev_mode

    def leave(self, next_mode=None):
        """Enter the mode."""
        pygame.mouse.set_visible(False)

    def _select_menu_item(self, pos):
        """Select menu item under cursor."""
        which = self.menu.find(self.ui.screen, pos)
        if which != -1:
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
        self.menu.draw(screen)

    def select_prev_item(self):
        """Select the previous menu item."""
        if self.menu.selected_item == 0:
            self.menu.selected_item = len(self.menu.items)
        self.menu.selected_item -= 1

    def select_next_item(self):
        """Select the next menu item."""
        self.menu.selected_item += 1
        if self.menu.selected_item == len(self.menu.items):
            self.menu.selected_item = 0

    def activate_item(self):
        """Activate the selected menu item."""
        action = self.menu_items[self.menu.selected_item][1:]
        handler = action[0]
        args = action[1:]
        handler(*args)

    def close_menu(self):
        """Close the menu and return to the previous game mode."""
        self.ui.ui_mode = self.prev_mode


class MainMenuMode(MenuMode):
    """Mode: main menu."""

    paused = False

    def init_menu(self):
        """Initialize the mode."""
        self.menu_items = [
            ('Watch Demo',      self.ui.watch_demo),
            ('One Player Game', self.ui.start_single_player_game),
            ('Two Player Game', self.ui.start_two_player_game),
            ('Gravity Wars',    self.ui.start_gravity_wars),
            ('Quit',            self.ui.quit),
        ]
        self.on_key(K_ESCAPE, self.ui.watch_demo)
        self.on_key(K_q, self.ui.quit)


class GameMenuMode(MenuMode):
    """Mode: in-game menu."""

    paused = True

    def init_menu(self):
        """Initialize the mode."""
        self.menu_items = [
            ('Resume game',     self.close_menu),
            ('End Game',        self.ui.end_game),
        ]
        self.on_key(K_ESCAPE, self.close_menu)



class PlayMode(UIMode):
    """Mode: play the game."""

    paused = False

    def init(self):
        """Initialize the mode."""
        self.on_key(K_ESCAPE, self.ui.game_menu)
        self.on_key(K_o, self.ui.toggle_missile_orbits)
        self.on_key(K_f, self.ui.toggle_fullscreen)
        self.while_key(K_EQUALS, self.ui.zoom_in)
        self.while_key(K_MINUS, self.ui.zoom_out)
        # Player 1
        self.on_key(K_1, self.ui.toggle_ai, 0)
        self.while_key(K_LEFT, self.ui.turn_left, 0)
        self.while_key(K_RIGHT, self.ui.turn_right, 0)
        self.while_key(K_UP, self.ui.accelerate, 0)
        self.while_key(K_DOWN, self.ui.backwards, 0)
        self.while_key(K_RALT, self.ui.brake, 0)
        self.on_key(K_RCTRL, self.ui.launch_missile, 0)
        # Player 2
        self.on_key(K_2, self.ui.toggle_ai, 1)
        self.while_key(K_a, self.ui.turn_left, 1)
        self.while_key(K_d, self.ui.turn_right, 1)
        self.while_key(K_w, self.ui.accelerate, 1)
        self.while_key(K_s, self.ui.backwards, 1)
        self.while_key(K_LALT, self.ui.brake, 1)
        self.on_key(K_LCTRL, self.ui.launch_missile, 1)

    def handle_mouse_release(self, event):
        """Handle a MOUSEBUTTONUP event."""
        if event.button == 1:
            self.ui.game_menu()
        else:
            UIMode.handle_mouse_press(self, event)


class GravityWarsMode(UIMode):
    """Mode: play gravity wars."""

    paused = False

    def init(self):
        """Initialize the mode."""
        self.on_key(K_ESCAPE, self.ui.game_menu)
        self.on_key(K_o, self.ui.toggle_missile_orbits)
        self.on_key(K_f, self.ui.toggle_fullscreen)
        self.while_key(K_EQUALS, self.ui.zoom_in)
        self.while_key(K_MINUS, self.ui.zoom_out)
        self.prompt = None
        self.state = self.logic()
        self.state.next()

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
                self.state.next()
            elif event.key == K_BACKSPACE:
                self.prompt.text = self.prompt.text[:-1]
            elif event.unicode.isdigit() or event.unicode in ('-', '.'):
                self.prompt.text += event.unicode


class GameUI(object):
    """User interface for the game."""

    ZOOM_FACTOR = 1.25              # Keyboard zoom factor

    fullscreen = False              # Start in windowed mode
    show_missile_trails = True      # Show missile trails by default
    show_debug_info = False         # Hide debug info by default
    desired_zoom_level = 1.0        # The desired zoom level

    min_fps = 10                    # Minimum FPS

    ship_colors = [
        (255, 255, 255),            # Player 1 has a white ship
        (127, 255, 0),              # Player 2 has a green ship
    ]

    visibility_margin = 120 # Keep ships at least 120px from screen edges

    _ui_mode = None         # Previous user interface mode

    # Some debug information
    time_to_draw = 0            # Time to draw everything
    time_to_draw_trails = 0     # Time to draw missile trails
    total_time = 0              # Time to process a frame
    last_time = None            # Timestamp of last frame

    def __init__(self):
        self.rng = random.Random()

    def init(self):
        """Initialize the user interface."""
        self._init_pygame()
        self._load_planet_images()
        self._init_fonts()
        self._set_display_mode()
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

    def _init_pygame(self):
        """Initialize pygame, but don't create an output window just yet."""
        pygame.init()
        pygame.display.set_caption('PySpace War')
        icon = pygame.image.load(find('images', 'pyspacewar-32x32.png'))
        pygame.display.set_icon(icon)
        pygame.mouse.set_visible(False)
        self.fullscreen_mode = self._choose_best_mode()

    def _choose_best_mode(self):
        """Choose a suitable display mode."""
        for (w, h) in pygame.display.list_modes():
            if w / h >= 2:
                # Dual-head modes (e.g. two 1024x768 monitors side by side)
                # return modes like (2048, 768).  These modes do not work
                # well for PyGame, so skip them.
                continue
            return (w, h)
        return (1024, 768) # *shrug*

    def _set_display_mode(self):
        """Set display mode."""
        if self.fullscreen:
            self.screen = pygame.display.set_mode(self.fullscreen_mode,
                                                  FULLSCREEN)
        else:
            w, h = self.fullscreen_mode
            windowed_mode = (int(w * 0.8), int(h * 0.8))
            self.screen = pygame.display.set_mode(windowed_mode, RESIZABLE)

    def _resize_window(self, size):
        """Resize the PyGame window as requested."""
        self.screen = pygame.display.set_mode(size, RESIZABLE)

    def _load_planet_images(self):
        """Load bitmaps of planets."""
        self.planet_images = map(pygame.image.load,
                                 glob.glob(find('images', 'planet*.png')))
        if not self.planet_images:
            raise RuntimeError("Could not find planet bitmaps")

    def _init_fonts(self):
        """Load fonts."""
        self.hud_font = self._load_font('Verdana', 14)
        self.input_font = self._load_font('Verdana', 24)
        self.menu_font = self._load_font('Verdanab', 40)

    def _load_font(self, name, size):
        """Try to load a font."""
        filename = '/usr/share/fonts/truetype/msttcorefonts/%s.ttf' % name
        if not os.path.exists(filename):
            filename = None
        return pygame.font.Font(filename, size)


    def _new_game(self, players=1):
        """Start a new game."""
        self.game = Game.new(ships=2,
                             planet_kinds=len(self.planet_images),
                             rng=self.rng)
        self.ships = self.game.ships
        self.ai = map(AIController, self.ships)
        self.ai_controlled = [False] * len(self.ships)
        self.missile_trails = {}
        self.viewport.origin = (self.ships[0].position +
                                self.ships[1].position) / 2
        self.viewport.scale = 1
        self.desired_zoom_level = 1
        self._init_hud()
        if players == 0: # demo mode
            self.toggle_ai(0)
            self.toggle_ai(1)
        elif players == 1: # player vs computer
            self.toggle_ai(1)
        else: # player vs player
            pass

    def _init_hud(self):
        """Initialize the heads-up display."""
        time_format = '%.f ms'
        self.fps_hud = HUDInfoPanel(self.hud_font, 20, xalign=0.5, yalign=0,
                content=[('objects', lambda: len(self.game.world.objects)),
                         ('trails', lambda: sum(len(trail)
                                for trail in self.missile_trails.values())),
                         ('fps', lambda: '%.0f' % self.frame_counter.fps()),
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
                         ('draw', lambda: time_format %
                                (self.time_to_draw * 1000)),
                         ('  trails', lambda: time_format %
                                (self.time_to_draw_trails * 1000)),
                         ('  other', lambda: time_format %
                                ((self.time_to_draw
                                  - self.time_to_draw_trails) * 1000)),
                         ('other', lambda: time_format %
                                ((self.total_time - self.game.time_to_update
                                  - self.time_to_draw - self.game.time_waiting)
                                 * 1000)),
                         ('idle', lambda: time_format %
                                (self.game.time_waiting * 1000)),
                         ('total', lambda: time_format %
                                (self.total_time * 1000)),
                        ])
        self.hud = [
            HUDShipInfo(self.ships[0], self.hud_font, 1, 0),
            HUDShipInfo(self.ships[1], self.hud_font, 0, 0,
                        HUDShipInfo.GREEN_COLORS),
            HUDCompass(self.game.world, self.ships[0], self.viewport, 1, 1,
                       HUDCompass.BLUE_COLORS),
            HUDCompass(self.game.world, self.ships[1], self.viewport, 0, 1,
                       HUDCompass.GREEN_COLORS),
        ]

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

    def quit(self):
        """Exit the game."""
        sys.exit(0)

    def main_menu(self):
        """Enter the main menu."""
        self.ui_mode = MainMenuMode(self)

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

    def game_menu(self):
        """Enter the game menu."""
        self.ui_mode = GameMenuMode(self)

    def resume_game(self):
        """Resume a game in progress."""
        self.ui_mode = PlayMode(self)

    def end_game(self):
        """End the game in progress."""
        self._new_game(0)
        self.ui_mode = MainMenuMode(self)

    def toggle_fullscreen(self):
        """Toggle fullscreen mode."""
        self.fullscreen = not self.fullscreen
        self._set_display_mode()

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

    def draw(self):
        """Draw the state of the game"""
        start = time.time()
        if self.last_time is not None:
            self.total_time = start - self.last_time
        self.last_time = start
        if (self.framedrop_needed and
            self.frame_counter.notional_fps() >= self.min_fps):
            if self.show_debug_info:
                self.fps_hud.draw(self.screen)
            pygame.display.flip()
            return
        self._keep_ships_visible()
        self.screen.fill((0, 0, 0))
        if self.show_missile_trails:
            self.draw_missile_trails()
        for obj in self.game.world.objects:
            getattr(self, 'draw_' + obj.__class__.__name__)(obj)
        for drawable in self.hud:
            drawable.draw(self.screen)
        self.ui_mode.draw(self.screen)
        if self.show_debug_info:
            self.fps_hud.draw(self.screen)
        self.time_to_draw = time.time() - start
        pygame.display.flip()
        self.frame_counter.frame()

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
        direction_vector = ship.direction_vector * ship.size
        side_vector = direction_vector.perpendicular()
        pt1 = ship.position - direction_vector + side_vector * 0.5
        pt2 = ship.position + direction_vector
        pt3 = ship.position - direction_vector - side_vector * 0.5
        points = map(self.viewport.screen_pos, [pt1, pt2, pt3])
        pygame.draw.aalines(self.screen, color, False, points)
        thrust_lines = []
        if ship.forward_thrust or ship.engage_brakes:
            thrust_lines.append(((-0.1, -0.9), (-0.1, -1.2)))
            thrust_lines.append(((+0.1, -0.9), (+0.1, -1.2)))
        if ship.rear_thrust or ship.engage_brakes:
            thrust_lines.append(((-0.6, -0.2), (-0.6, +0.1)))
            thrust_lines.append(((+0.6, -0.2), (+0.6, +0.1)))
        if ship.left_thrust or ship.engage_brakes:
            thrust_lines.append(((-0.2, +0.8), (-0.4, +0.8)))
            thrust_lines.append(((+0.8, -0.8), (+0.6, -0.8)))
        if ship.right_thrust or ship.engage_brakes:
            thrust_lines.append(((+0.2, +0.8), (+0.4, +0.8)))
            thrust_lines.append(((-0.8, -0.8), (-0.6, -0.8)))
        for (s1, d1), (s2, d2) in thrust_lines:
            pt1 = ship.position + direction_vector * d1 + side_vector * s1
            pt2 = ship.position + direction_vector * d2 + side_vector * s2
            pt1, pt2 = map(self.viewport.screen_pos, [pt1, pt2])
            pygame.draw.aaline(self.screen, (255, 120, 20), pt1, pt2)

    def update_missile_trails(self):
        """Update missile trails."""
        for missile, trail in self.missile_trails.items():
            if missile.world is None:
                del trail[:2]
                if not trail:
                    del self.missile_trails[missile]
            else:
                trail.append(missile.position)
                if len(trail) > 100:
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
        set_at = self.screen.set_at
        red, green, blue = self.ship_colors[missile.appearance]
        r = red * 0.1
        g = green * 0.1
        b = blue * 0.1
        n = len(trail)
        dr = red * 0.7 / n
        dg = green * 0.7 / n
        db = blue * 0.7 / n
        for pt in self.viewport.list_of_screen_pos(trail):
            set_at(pt, (r, g, b))
            r += dr
            g += dg
            b += db

    def draw_Missile(self, missile):
        """Draw a missile."""
        color = self.ship_colors[missile.appearance]
        self.screen.set_at(self.viewport.screen_pos(missile.position), color)

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

