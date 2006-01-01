"""
Graphical user interface for PySpaceWar
"""

import pygame
from pygame.locals import *

from world import Vector


class Viewport(object):
    """A viewport to the universe.

    The responsibility of this class is to provide a mapping from screen
    coordinates to world coordinates and back.

    Attributes and properties:

        ``origin`` -- point in the universe corresponding to the center of
        the screen.

        ``scale`` -- ratio of pixels to world coordinate units.

    """

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

