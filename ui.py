"""
Graphical user interface for PySpaceWar
"""

import os
import sys
import glob

import pygame
from pygame.locals import *

from world import Vector, Ship, Missile
from game import Game
from ai import AIController


def find(filespec):
    """Construct a pathname relative to the location of this module."""
    basedir = os.path.dirname(__file__)
    return os.path.join(basedir, filespec)


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
        x = self._screen_x + world_pos.x * self._scale
        y = self._screen_y - world_pos.y * self._scale
        return (int(x), int(y))

    def world_pos(self, screen_pos):
        """Convert screen coordinates into world coordinates."""
        x = (screen_pos[0] - self._screen_x) / self._scale
        y = -(screen_pos[1] - self._screen_y) / self._scale
        return (x, y)

    def in_screen(self, world_pos):
        """Is a position visible on screen?"""
        xmin, ymin, xmax, ymax = self.world_bounds
        return xmin <= world_pos.x <= xmax and ymin <= world_pos.y <= ymax

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
            return 0
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

    def __init__(self, font, ncols, nrows, xalign=0, yalign=0,
                 colors=STD_COLORS, content=None):
        self.font = font
        self.width = int(self.font.size('x')[0] * ncols)
        self.row_height = self.font.get_linesize()
        self.height = int(nrows * self.row_height)
        self.xalign = xalign
        self.yalign = yalign
        self.color1, self.color2 = colors
        self.surface = pygame.Surface((self.width,
                                       self.height)).convert_alpha()
        self.surface.fill((8, 8, 8, int(255 * 0.8)))
        for x in (0, self.width-1):
            for y in (0, self.height-1):
                self.surface.set_at((x, y), (0, 0, 0, 0))
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
        (0x00, 0x11, 0x22, alpha),
        (0x99, 0xaa, 0xff, alpha),
        (0x44, 0x55, 0x66, alpha),
        (0xaa, 0x77, 0x66, alpha),
    )

    GREEN_COLORS = (
        (0x00, 0x22, 0x11, alpha),
        (0x99, 0xff, 0xaa, alpha),
        (0x44, 0x66, 0x55, alpha),
        (0xaa, 0x66, 0x77, alpha),
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
        self.surface = pygame.Surface((self.width,
                                       self.height)).convert_alpha()
        self.bgcolor, self.fgcolor1, self.fgcolor2, self.fgcolor3 = colors
        self.xalign = xalign
        self.yalign = yalign

    def draw(self, surface):
        x = y = self.radius
        self.surface.fill((0, 0, 0, 0))

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


class GameUI(object):
    """User interface for the game."""

    ZOOM_FACTOR = 1.25              # Keyboard zoom factor

    fullscreen = False              # Start in windowed mode
    show_missile_trails = True      # Show missile trails by default

    min_fps = 10                    # Minimum FPS

    ship_colors = [
        (255, 255, 255),            # Player 1 has a white ship
        (127, 255, 0),              # Player 2 has a green ship
    ]

    visibility_margin = 120 # Keep ships at least 120px from screen edges


    def init(self):
        """Initialize the user interface."""
        self._init_pygame()
        self._load_planet_images()
        self._init_fonts()
        self._init_keymap()
        self._set_mode()
        self.viewport = Viewport(self.screen)
        self._new_game()
        self.frame_counter = FrameRateCounter()
        self.framedrop_needed = False

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

    def _init_fonts(self):
        """Load fonts."""
        self.hud_font = self._load_font('Verdana', 14)

    def _load_font(self, name, size):
        """Try to load a font."""
        filename = '/usr/share/fonts/truetype/msttcorefonts/%s.ttf' % name
        if not os.path.exists(filename):
            filename = None
        return pygame.font.Font(filename, size)

    def _new_game(self):
        """Start a new game."""
        self.game = Game.new(ships=2,
                             planet_kinds=len(self.planet_images))
        self.ships = sorted([obj for obj in self.game.world.objects
                             if isinstance(obj, Ship)],
                            key=lambda ship: ship.appearance)
        self.ai = map(AIController, self.ships)
        self.ai_controlled = [False] * len(self.ships)
        self.missile_trails = {}
        self.viewport.origin = (self.ships[0].position +
                                self.ships[1].position) / 2
        self.viewport.scale = 1
        self._init_hud()

    def _init_hud(self):
        """Initialize the heads-up display."""
        self.fps_hud = HUDInfoPanel(self.hud_font, 10, 2, xalign=0.5, yalign=0,
                content=[('objects', lambda: len(self.game.world.objects)),
                         ('fps', lambda: '%.0f' % self.frame_counter.fps())])
        self.hud = [
            HUDShipInfo(self.ships[0], self.hud_font, 1, 0),
            HUDShipInfo(self.ships[1], self.hud_font, 0, 0,
                        HUDShipInfo.GREEN_COLORS),
            HUDCompass(self.game.world, self.ships[0], self.viewport, 1, 1,
                       HUDCompass.BLUE_COLORS),
            HUDCompass(self.game.world, self.ships[1], self.viewport, 0, 1,
                       HUDCompass.GREEN_COLORS),
            self.fps_hud,
        ]

    def _keep_ships_visible(self):
        """Update viewport origin/scale so that all ships are on screen."""
        self.viewport.keep_visible([s.position for s in self.ships],
                                   self.visibility_margin)

    def _init_keymap(self):
        """Initialize the keymap."""
        self.clear_keymap()
        self.on_key(K_ESCAPE, self.quit)
        self.on_key(K_q, self.quit)
        self.on_key(K_o, self.toggle_missile_orbits)
        self.while_key(K_EQUALS, self.zoom_in)
        self.while_key(K_MINUS, self.zoom_out)
        # Player 1
        self.on_key(K_1, lambda *a: self.toggle_ai(0))
        self.while_key(K_LEFT, lambda *a: self.turn_left(0))
        self.while_key(K_RIGHT, lambda *a: self.turn_right(0))
        self.while_key(K_UP, lambda *a: self.accelerate(0))
        self.while_key(K_DOWN, lambda *a: self.backwards(0))
        self.on_key(K_RCTRL, lambda *a: self.launch_missile(0))
        # Player 2
        self.on_key(K_2, lambda *a: self.toggle_ai(1))
        self.while_key(K_a, lambda *a: self.turn_left(1))
        self.while_key(K_d, lambda *a: self.turn_right(1))
        self.while_key(K_w, lambda *a: self.accelerate(1))
        self.while_key(K_s, lambda *a: self.backwards(1))
        self.on_key(K_LCTRL, lambda *a: self.launch_missile(1))

    def clear_keymap(self):
        """Clear all key mappings."""
        self._keymap_once = {}
        self._keymap_repeat = {}

    def on_key(self, key, handler):
        """Install a handler to be called once when a key is pressed."""
        self._keymap_once[key] = handler

    def while_key(self, key, handler):
        """Install a handler to be called repeatedly while a key is pressed."""
        self._keymap_repeat[key] = handler

    def interact(self):
        """Process pending keyboard/mouse events."""
        for event in pygame.event.get():
            if event.type == QUIT:
                self.quit()
            elif event.type == KEYDOWN:
                handler = self._keymap_once.get(event.key)
                if handler:
                    handler(event)
        pressed = pygame.key.get_pressed()
        for key, handler in self._keymap_repeat.items():
            if pressed[key]:
                handler()

    def quit(self, event=None):
        """Exit the game."""
        sys.exit(0)

    def zoom_in(self, event=None):
        """Zoom in."""
        self.viewport.scale *= self.ZOOM_FACTOR

    def zoom_out(self, event=None):
        """Zoom in."""
        self.viewport.scale /= self.ZOOM_FACTOR

    def toggle_missile_orbits(self, event=None):
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

    def launch_missile(self, player_id):
        """Manual ship control: launch a missile."""
        if not self.ai_controlled[player_id]:
            self.ships[player_id].launch()

    def draw(self):
        """Draw the state of the game"""
        if (self.framedrop_needed and
            self.frame_counter.notional_fps() >= self.min_fps):
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
            color = colorblend(color, (0x20, 0x20, 0x20), 0.2)
        direction_vector = ship.direction_vector * ship.size
        side_vector = direction_vector.perpendicular()
        pt1 = ship.position - direction_vector + side_vector * 0.5
        pt2 = ship.position + direction_vector
        pt3 = ship.position - direction_vector - side_vector * 0.5
        points = map(self.viewport.screen_pos, [pt1, pt2, pt3])
        pygame.draw.aalines(self.screen, color, False, points)
        thrust_lines = []
        if ship.forward_thrust:
            thrust_lines.append(((-0.1, -0.9), (-0.1, -1.2)))
            thrust_lines.append(((+0.1, -0.9), (+0.1, -1.2)))
        if ship.rear_thrust:
            thrust_lines.append(((-0.6, -0.2), (-0.6, +0.1)))
            thrust_lines.append(((+0.6, -0.2), (+0.6, +0.1)))
        if ship.left_thrust:
            thrust_lines.append(((-0.2, +0.8), (-0.4, +0.8)))
            thrust_lines.append(((+0.8, -0.8), (+0.6, -0.8)))
        if ship.right_thrust:
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
        for missile, trail in self.missile_trails.items():
            self.draw_missile_trail(missile, trail)

    def draw_missile_trail(self, missile, trail):
        """Draw a missile orbit trail."""
        red, green, blue = self.ship_colors[missile.appearance]
        a = 0.1
        b = 0.7 / len(trail)
        f = a
        for pt in trail:
            color = (red*f, green*f, blue*f)
            if self.viewport.in_screen(pt):
                self.screen.set_at(self.viewport.screen_pos(pt), color)
            f += b

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
        self.update_missile_trails()
        self.framedrop_needed = not self.game.wait_for_tick()


def main():
    ui = GameUI()
    ui.init()
    while True:
        ui.wait_for_tick()
        ui.interact()
        ui.draw()


if __name__ == '__main__':
    main()
