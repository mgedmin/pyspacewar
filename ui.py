"""
Graphical user interface for PySpaceWar
"""

import os
import sys
import glob

import pygame
from pygame.locals import *

from world import Vector, Ship
from game import Game


def find(filespec):
    """Construct a pathname relative to the location of this module."""
    basedir = os.path.dirname(__file__)
    return os.path.join(basedir, filespec)


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

    def surface_size_changed(self):
        """Notify that surface size has changed."""
        self._recalc()

    def screen_len(self, world_len):
        """Convert a length in world coordinate units to pixels."""
        return int(world_len * self.scale)

    def screen_pos(self, world_pos):
        """Convert world coordinates to screen coordinates."""
        x = self._screen_x + world_pos.x * self._scale
        y = self._screen_y - world_pos.y * self._scale
        return (int(x), int(y))

    def world_pos(self, screen_pos):
        """Convert screen coordinates into world coordinates."""
        x = (screen_pos[0] - self._screen_x) / self._scale
        y = -(screen_pos[1] - self._screen_y) / self._scale
        return (x, y)

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
            while True:
                xmin, ymin, xmax, ymax = self.world_inner_bounds(margin)
                if w <= xmax - xmin and h <= ymax - ymin:
                    break
                self.scale /= self.AUTOSCALE_FACTOR

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


class GameUI(object):
    """User interface for the game."""

    fullscreen = False

    ship_colors = [
        (255, 255, 255),     # Player 1 has a white ship
        (127, 255, 0),       # Player 2 has a green ship
    ]

    visibility_margin = 120  # Keep ships at least 120px from screen edges

    def init(self):
        """Initialize the user interface."""
        self._init_pygame()
        self._load_planet_images()
        self._init_keymap()
        self._set_mode()
        self.viewport = Viewport(self.screen)
        self._new_game()

    def _init_pygame(self):
        """Initialize pygame, but don't create an output window just yet."""
        pygame.init()
        pygame.display.set_caption('PySpace War')
        pygame.mouse.set_visible(False)
        self.fullscreen_mode = self._choose_best_mode()

    def _choose_best_mode(self):
        """Choose a suitable display mode."""
        return (1024, 768)

    def _set_mode(self):
        """Set display mode."""
        if self.fullscreen:
            self.screen = pygame.display.set_mode(self.fullscreen_mode,
                                                  FULLSCREEN)
        else:
            w, h = self.fullscreen_mode
            windowed_mode = (int(w * 0.8), int(h * 0.8))
            self.screen = pygame.display.set_mode(windowed_mode)

    def _load_planet_images(self):
        """Load bitmaps of planets."""
        self.planet_images = map(pygame.image.load,
                                 glob.glob(find('planet*.png')))
        if not self.planet_images:
            raise RuntimeError("Could not find planet bitmaps")

    def _new_game(self):
        """Start a new game."""
        self.game = Game.new(ships=2,
                             planet_kinds=len(self.planet_images))
        self.ships = sorted([obj for obj in self.game.world.objects
                             if isinstance(obj, Ship)],
                            key=lambda ship: ship.appearance)
        self.viewport.origin = (self.ships[0].position +
                                self.ships[1].position) / 2
        self.viewport.scale = 1

    def _keep_ships_visible(self):
        """Update viewport origin/scale so that all ships are on screen."""
        self.viewport.keep_visible([s.position for s in self.ships],
                                   self.visibility_margin)

    def _init_keymap(self):
        """Initialize the keymap."""
        self._keymap = {}
        self._keymap[K_ESCAPE] = self.quit
        self._keymap[K_q] = self.quit

    def interact(self):
        """Process pending keyboard/mouse events."""
        for event in pygame.event.get():
            if event.type == QUIT:
                self.quit()
            elif event.type == KEYDOWN:
                handler = self._keymap.get(event.key)
                if handler:
                    handler(event)

    def quit(self, event=None):
        """Exit the game."""
        sys.exit(0)

    def draw(self):
        """Draw the state of the game"""
        self._keep_ships_visible()
        self.screen.fill((0, 0, 0))
        for obj in self.game.world.objects:
            getattr(self, 'draw_' + obj.__class__.__name__)(obj)
        pygame.display.flip()

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
        direction_vector = ship.direction_vector * ship.size
        side_vector = direction_vector.perpendicular()
        pt1 = ship.position - direction_vector + side_vector * 0.5
        pt2 = ship.position + direction_vector
        pt3 = ship.position - direction_vector - side_vector * 0.5
        points = map(self.viewport.screen_pos, [pt1, pt2, pt3])
        pygame.draw.aalines(self.screen, color, False, points)
        # TODO: draw thrusters

    def wait_for_tick(self):
        """Wait for the next game time tick.  World moves during this time."""
        self.game.wait_for_tick()


def main():
    ui = GameUI()
    ui.init()
    while True:
        ui.wait_for_tick()
        ui.interact()
        ui.draw()


if __name__ == '__main__':
    main()
