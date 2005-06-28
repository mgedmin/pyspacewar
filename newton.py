#!/usr/bin/python
"""
A game based on Newtonian gravity (loosely).

Copyright (c) 2005 Marius Gedminas <marius@pov.lt>
Consider this game GPLed.
"""
import math
import random
import glob
import pygame
from pygame.locals import *


GRAVITY = 0.01 # constant of gravitation

FPS = 20
JIFFY_IN_MS = 1000 / FPS            # 1 jiffy in ms
DELTA_TIME = 2.0                    # world time units in one jiffy
SCALE_FACTOR = 1.25                 # scale factor per jiffy for +/-
ROTATION_SPEED = 10 / DELTA_TIME    # angles per time for left/right
FRONT_THRUST = 0.2 / DELTA_TIME     # forward acceleration
REAR_THRUST = 0.1 / DELTA_TIME      # backward acceleration
MISSILE_SPEED = 3                   # missile speed
MISSILE_RECOIL = 0.01               # recoil as factor of missile speed
MISSILE_DAMAGE = 0.6
COLLISSION_DAMAGE = 0.05


class Vector(tuple):

    x = property(lambda self: self[0])
    y = property(lambda self: self[1])

    def __new__(cls, *args):
        if len(args) == 2:
            return tuple.__new__(cls, args)
        else:
            return tuple.__new__(cls, *args)

    def from_polar(direction, magnitude=1.0):
        angle = direction * math.pi / 180
        return Vector(magnitude * math.cos(angle), magnitude * math.sin(angle))
    from_polar = staticmethod(from_polar)

    def __mul__(self, factor):
        return Vector(self[0] * factor, self[1] * factor)

    def __div__(self, divisor):
        return Vector(self[0] / float(divisor), self[1] / float(divisor))

    def __add__(self, other):
        return Vector(self[0] + other[0], self[1] + other[1])

    def __sub__(self, other):
        return Vector(self[0] - other[0], self[1] - other[1])

    def __neg__(self):
        return Vector(-self[0], -self[1])

    def perpendicular(self):
        return Vector(-self.y, self.x)

    def scaled(self, new_length=1.0):
        return self * new_length / length(self)


def length_sq(vector):
    return vector[0] ** 2 + vector[1] ** 2


def length(vector):
    return math.sqrt(length_sq(vector))


def arg(vector):
    angle = math.atan2(vector.y, vector.x) * 180 / math.pi
    if angle < 0:
        angle += 360
    return round(angle)


def colorblend(col1, col2, alpha=0.5):
    r1, g1, b1 = col1
    r2, g2, b2 = col2
    beta = 1-alpha
    return (alpha*r1+beta*r2, alpha*g1+beta*g2, alpha*b1+beta*b2)


class Viewport(object):

    show_orbits = True
    autoscale_factor = 1.001
    visibility_margin = 100

    def __init__(self, surface):
        self.surface = surface
        self._origin = Vector(0, 0)
        self._scale = 1.0
        self._recalc()

    def _recalc(self):
        surface_w, surface_h = self.surface.get_size()
        self.screen_x = surface_w * 0.5 - self.origin.x * self.scale + 0.5
        self.screen_y = surface_h * 0.5 + self.origin.y * self.scale + 0.5
        x1, y1 = self.world_pos((0, 0))
        x2, y2 = self.world_pos((surface_w, surface_h))
        self.world_bounds = min(x1, x2), min(y1, y2), max(x1, x2), max(y1, y2)
        m = self.visibility_margin
        x1, y1 = self.world_pos((m, m))
        x2, y2 = self.world_pos((surface_w-m, surface_h-m))
        self.world_inner_bounds = min(x1, x2), min(y1, y2), max(x1, x2), max(y1, y2)

    def resize_screen(self):
        self._recalc()

    def set_origin(self, new_origin):
        self._origin = new_origin
        self._recalc()

    origin = property(lambda self: self._origin, set_origin)

    def set_scale(self, new_scale):
        self._scale = new_scale
        self._recalc()

    scale = property(lambda self: self._scale, set_scale)

    def screen_len(self, world_len):
        return int(world_len * self.scale)

    def screen_pos(self, world_pos):
        # screen_pos((0, 0)) == (surface_w/2, surface_h/2)
        # screen_pos((1, 2)) == (surface_w/2 + scale, surface_h/2 + 2*scale)
        x = self.screen_x + world_pos[0] * self._scale
        y = self.screen_y - world_pos[1] * self._scale
        return (int(x), int(y))

    def in_screen(self, world_pos):
        xmin, ymin, xmax, ymax = self.world_bounds
        return xmin <= world_pos[0] <= xmax and ymin <= world_pos[1] <= ymax

    def world_pos(self, screen_pos):
        x = (screen_pos[0] - self.screen_x) / self._scale
        y = -(screen_pos[1] - self.screen_y) / self._scale
        return (x, y)

    def keep_visible(self, *points):
        if len(points) > 1:
            xs = [pt.x for pt in points]
            ys = [pt.y for pt in points]
            w = max(xs) - min(xs)
            h = max(ys) - min(ys)
            xmin, ymin, xmax, ymax = self.world_inner_bounds
            while (xmax - xmin) < w:
                self.scale /= self.autoscale_factor
                xmin, ymin, xmax, ymax = self.world_inner_bounds
            while (ymax - ymin) < h:
                self.scale /= self.autoscale_factor
                xmin, ymin, xmax, ymax = self.world_inner_bounds
        for pt in points:
            xmin, ymin, xmax, ymax = self.world_inner_bounds
            if pt.x < xmin:
                self.origin -= Vector(xmin - pt.x, 0)
            elif pt.x > xmax:
                self.origin -= Vector(xmax - pt.x, 0)
            if pt.y < ymin:
                self.origin -= Vector(0, ymin - pt.y)
            elif pt.y > ymax:
                self.origin -= Vector(0, ymax - pt.y)


class World(object):

    def __init__(self):
        self.objects = []
        self.massive_objects = []
        self.collision_objects = []
        self.in_update = False
        self.queued_additions = []
        self.queued_removals = []

    def add(self, obj):
        if self.in_update:
            self.queued_additions.append(obj)
            return
        obj.world = self
        self.objects.append(obj)
        if obj.mass != 0:
            self.massive_objects.append(obj)
        if obj.important_for_collision_detection:
            self.collision_objects.append(obj)

    def remove(self, obj):
        if self.in_update:
            self.queued_removals.append(obj)
            return
        self.objects.remove(obj)
        if obj.mass != 0:
            self.massive_objects.remove(obj)
        if obj.important_for_collision_detection:
            self.collision_objects.remove(obj)

    def collides(self, something, margin=0):
        for obj in self.collision_objects:
            if obj is not something and something.collides(obj, margin=0):
                return True
        return False

    def update(self, dt):
        self.in_update = True
        # This is somewhat expensive: 0.3 ms for 1 object
        for obj in self.objects:
            for other in self.massive_objects:
                if other is not obj:
                    obj.gravitate(other, dt)
        # The rest eats about 0.1 ms per 1 objects
        for obj in self.objects:
            obj.move(dt)
            for other in self.collision_objects:
                if obj is not other and obj.collides(other):
                    obj.collision(other)
                    other.collision(obj)
        self.in_update = False
        for obj in self.queued_additions:
            self.add(obj)
        for obj in self.queued_removals:
            self.remove(obj)
        self.queued_additions = []
        self.queued_removals = []

    def draw(self, viewport):
        for obj in self.objects:
            obj.draw(viewport)


class Body(object):

    important_for_collision_detection = True

    def __init__(self, position, mass=0, velocity=Vector(0, 0), radius=1):
        self.position = Vector(position)
        self.mass = mass
        self.radius = radius
        self.velocity = velocity
        self.pinned = False

    def pin(self):
        self.pinned = True

    def collides(self, other, margin=0):
        margin = 1.0 - margin
        distance_sq = length_sq(self.position - other.position)
        collision_distance = (self.radius + other.radius) * margin
        collision_distance_sq = collision_distance ** 2
        return distance_sq < collision_distance_sq

    def bounce(self, other):
        normal = (self.position - other.position).scaled()
        delta = normal.x * self.velocity.x + normal.y * self.velocity.y
        self.velocity -= normal.scaled(2 * delta) * 0.9
        self.position = other.position + normal.scaled(other.radius + self.radius)

    def stop(self, other):
        normal = (self.position - other.position).scaled()
        self.velocity = other.velocity
        self.position = other.position + normal.scaled(other.radius + self.radius)
        self.pin()

    def explode(self, other):
        self.world.remove(self)

    collision = explode

    def gravitate(self, other, dt=1.0):
        # F = m1 * a = G*m1*m2/r**2
        # a = G * m2 / r**2
        if other.mass == 0 or self.pinned:
            return
        vector = other.position - self.position
        sq_of_distance = length_sq(vector)
        magnitude = GRAVITY * other.mass / sq_of_distance
        acceleration = vector.scaled(magnitude * dt)
        self.velocity += acceleration

    def orbit(self, other):
        vector = other.position - self.position
        sq_of_distance = length_sq(vector)
        distance = math.sqrt(sq_of_distance)
        orbital_velocity = math.sqrt(GRAVITY * other.mass / distance)
        self.velocity = vector.perpendicular().scaled(orbital_velocity)

    def move(self, dt=1.0):
        self.position += self.velocity * dt

    def add_debris(self, howmany=None, maxdistance=1.0, time=5.0):
        if not howmany:
            howmany = random.randrange(3, 6)
        for n in range(howmany):
            color = (random.randrange(0xf0, 0xff),
                     random.randrange(0x70, 0x90),
                     random.randrange(0, 0x20))
            velocity = self.velocity * 0.3
            velocity += Vector.from_polar(random.randrange(0, 360),
                                          random.random() * maxdistance)
            debris = Debris(self.position, velocity, color, time=time)
            debris.pin()
            self.world.add(debris)


class Planet(Body):

    def __init__(self, position, radius, mass, color, image=None):
        Body.__init__(self, position, mass)
        self.radius = radius
        self.color = color

        self.image = image

    def draw(self, viewport):
        pos = viewport.screen_pos(self.position)
        radius = viewport.screen_len(self.radius)
        if self.image is None:
            pygame.draw.circle(viewport.surface, self.color, pos, radius)
        else:
            img = pygame.transform.scale(self.image, (radius*2, radius*2))
            viewport.surface.blit(img, (pos[0]-radius, pos[1]-radius))

    def collision(self, other):
        pass


class Ship(Body):

    def __init__(self, position, size=10, color=(255, 255, 255), direction=0):
        Body.__init__(self, position, 0)
        self.radius = size * 0.6
        self.size = size
        self.direction = direction
        self.color = color
        self.forward_thrust = 0
        self.rear_thrust = 0
        self.left_thrust = 0
        self.right_thrust = 0
        self.draw_forward_thrust = 0
        self.draw_rear_thrust = 0
        self.draw_left_thrust = 0
        self.draw_right_thrust = 0
        self.health = 1.0
        self.dead = False
        self.frags = 0

    def collision(self, other):
        # XXX this is ugly, I should use multimethods
        ship_responsible = self
        if isinstance(other, Debris):
            return
        elif isinstance(other, Missile):
            if other.exploded:
                return
            other.exploded = True
            self.health -= MISSILE_DAMAGE
            ship_responsible = other.launched_by
            v = other.velocity
            if other.dying:
                v = other.velocity_before_death
            self.velocity += v * MISSILE_RECOIL
        else:
            self.health -= COLLISSION_DAMAGE
            self.bounce(other)
        if self.health <= 0 and not self.dead:
            if ship_responsible is self or ship_responsible is None:
                self.frags -= 1
            else:
                ship_responsible.frags += 1
            self.dead = True
            self.dead_timer = 100
            self.add_debris(time=50, maxdistance=self.size * 0.5,
                            howmany=random.randrange(9, 21))

    def set_direction(self, direction):
        direction = direction % 360
        if direction < 0: direction += 360
        self._direction = direction
        self.direction_vector = Vector.from_polar(direction)

    direction = property(lambda self: self._direction, set_direction)

    def respawn(self):
        self.dead = False
        self.health = 1.0
        self.velocity = Vector(0, 0)
        while True:
            self.position = Vector.from_polar(random.randrange(0, 360),
                                              random.randrange(0, 600))
            if not self.world.collides(self, 0.1):
                break

    def move(self, dt=1.0):
        if self.dead:
            self.left_thrust = 0
            self.right_thrust = 0
            self.forward_thrust = 0
            self.rear_thrust = 0
            self.dead_timer -= dt
            if self.dead_timer < 0:
                self.respawn()
        self.draw_forward_thrust = self.forward_thrust
        self.draw_rear_thrust = self.rear_thrust
        self.draw_left_thrust = self.left_thrust
        self.draw_right_thrust = self.right_thrust
        if self.left_thrust:
            self.direction += self.left_thrust * dt
            self.left_thrust = 0
        if self.right_thrust:
            self.direction -= self.right_thrust * dt
            self.right_thrust = 0
        if self.forward_thrust:
            self.velocity += self.direction_vector * self.forward_thrust * dt
            self.forward_thrust = 0
        if self.rear_thrust:
            self.velocity -= self.direction_vector * self.rear_thrust * dt
            self.rear_thrust = 0
        Body.move(self, dt)

    def draw(self, viewport):
        color = self.color
        if self.dead:
            color = colorblend(color, (0x20, 0x20, 0x20), 0.2)
        direction_vector = self.direction_vector * self.size
        side_vector = direction_vector.perpendicular()
        pt1 = self.position - direction_vector + side_vector * 0.5
        pt2 = self.position + direction_vector
        pt3 = self.position - direction_vector - side_vector * 0.5
        points = map(viewport.screen_pos, [pt1, pt2, pt3])
        pygame.draw.aalines(viewport.surface, color, False, points)
        if self.draw_forward_thrust:
            for x in (-0.1, 0.1):
                pt1 = self.position - direction_vector * 0.9 + side_vector * x
                pt2 = self.position - direction_vector * 1.2 + side_vector * x
                pt1, pt2 = map(viewport.screen_pos, [pt1, pt2])
                pygame.draw.aaline(viewport.surface, (255, 120, 20), pt1, pt2)
        if self.draw_rear_thrust:
            for x in (-0.6, 0.6):
                pt1 = self.position - direction_vector * 0.2 + side_vector * x
                pt2 = self.position + direction_vector * 0.1 + side_vector * x
                pt1, pt2 = map(viewport.screen_pos, [pt1, pt2])
                pygame.draw.aaline(viewport.surface, (255, 120, 20), pt1, pt2)
        if self.draw_left_thrust:
            pt1 = self.position + direction_vector * 0.8 - side_vector * 0.2
            pt2 = self.position + direction_vector * 0.8 - side_vector * 0.4
            pt1, pt2 = map(viewport.screen_pos, [pt1, pt2])
            pygame.draw.aaline(viewport.surface, (255, 120, 20), pt1, pt2)
            pt1 = self.position - direction_vector * 0.8 + side_vector * 0.8
            pt2 = self.position - direction_vector * 0.8 + side_vector * 0.6
            pt1, pt2 = map(viewport.screen_pos, [pt1, pt2])
            pygame.draw.aaline(viewport.surface, (255, 120, 20), pt1, pt2)
        if self.draw_right_thrust:
            pt1 = self.position + direction_vector * 0.8 + side_vector * 0.2
            pt2 = self.position + direction_vector * 0.8 + side_vector * 0.4
            pt1, pt2 = map(viewport.screen_pos, [pt1, pt2])
            pygame.draw.aaline(viewport.surface, (255, 120, 20), pt1, pt2)
            pt1 = self.position - direction_vector * 0.8 - side_vector * 0.8
            pt2 = self.position - direction_vector * 0.8 - side_vector * 0.6
            pt1, pt2 = map(viewport.screen_pos, [pt1, pt2])
            pygame.draw.aaline(viewport.surface, (255, 120, 20), pt1, pt2)

    def shoot(self, extra_speed, recoil=MISSILE_RECOIL):
        missile = Missile(self.position + self.direction_vector * self.size,
                          self.velocity + self.direction_vector * extra_speed,
                          self.color, launched_by=self)
        self.velocity -= self.direction_vector * extra_speed * recoil
        return missile


class Debris(Body):

    important_for_collision_detection = False  # avoid n-square problem

    collision = Body.bounce

    def __init__(self, position, velocity, color, time=10):
        Body.__init__(self, position, velocity=velocity)
        self.color = color
        self.time = time

    def move(self, dt):
        if self.time < dt:
            self.world.remove(self)
            return
        self.time -= dt
        Body.move(self, dt)

    def draw(self, viewport):
        viewport.surface.set_at(viewport.screen_pos(self.position), self.color)


class Missile(Body):

    important_for_collision_detection = False  # avoid n-square problem

    def __init__(self, position, velocity, color, launched_by=None):
        Body.__init__(self, position, velocity=velocity)
        self.color = color
        self.orbit = []
        self.dying = False
        self.launched_by = launched_by

    def move(self, dt):
        if self.dying:
            if not self.orbit:
                self.world.remove(self)
            else:
                del self.orbit[:2]
            return
        self.orbit.append(self.position)
        if len(self.orbit) > 100:
            del self.orbit[0]
        Body.move(self, dt)

    def explode(self, other):
        if self.dying:
            return
        self.velocity_before_death = self.velocity
        self.exploded = False
        self.add_debris()
        self.stop(other)
        self.dying = True

    collision = explode

    def draw(self, viewport):
        if self.orbit and viewport.show_orbits:
            red, green, blue = self.color
            if length_sq(self.position) > 10000**2: # far outer space
                f = 0.2
                color = (red*f, green*f, blue*f)
                pygame.draw.line(viewport.surface, color,
                                 viewport.screen_pos(self.orbit[0]),
                                 viewport.screen_pos(self.position))
            else:
                a = 0.1
                b = 0.7 / len(self.orbit)
                f = a
                for pt in self.orbit:
                    color = (red*f, green*f, blue*f)
                    if viewport.in_screen(pt):
                        viewport.surface.set_at(viewport.screen_pos(pt), color)
                    f += b
        if not self.dying:
            viewport.surface.set_at(viewport.screen_pos(self.position), self.color)


def make_simple_world():
    world = World()
    planet = Planet((0, 0), 20, 100, (0x80, 0x20, 0x10))
    planet.pin()
    world.add(planet)
    moon = Planet((100, 80), 5, 10, (0x7f, 0x90, 0x20))
    world.add(moon)
    moon.orbit(planet)
    ship = Ship((-100, 80))
    ship.pin()
    # ship.orbit(planet)
    world.add(ship)
    world.ship = ship

    planet2 = Planet((400, 750), 30, 200, (0x20, 0x80, 0x10))
    planet2.pin()
    world.add(planet2)

    return world


def make_world():
    images = map(pygame.image.load, glob.glob('planet*.png'))
    world = World()
    n_planets = random.randrange(2, 20)
    for n in range(n_planets):
        color = [random.randrange(0x80, 0xA0),
                 random.randrange(0x20, 0x7F),
                 random.randrange(0, 0x20)]
        img = random.choice(images)
        random.shuffle(color)
        while True:
            pos = Vector.from_polar(random.randrange(0, 360),
                                    random.randrange(0, 600))
            radius = random.randrange(5, 40)
            mass = radius ** 3 * random.randrange(2, 6)
            p = Planet(pos, radius, mass, tuple(color), img)
            if not world.collides(p, 0.1):
                break
        p.pin()
        world.add(p)

    while True:
        pos = Vector.from_polar(random.randrange(0, 360),
                                random.randrange(0, 600))
        ship = Ship(pos)
        if not world.collides(ship, 0.1):
            break
    ship.pin()
    world.add(ship)
    world.ship = ship

    while True:
        pos = Vector.from_polar(random.randrange(0, 360),
                                random.randrange(0, 600))
        ship = Ship(pos, color=(0x7f, 0xff, 0), direction=180)
        if not world.collides(ship, 0.1):
            break
    ship.pin()
    world.add(ship)
    world.ship2 = ship
    return world


class FPSCounter(object):

    COUNT = 10

    def __init__(self):
        self.frames = []

    def frame(self):
        self.frames.append(pygame.time.get_ticks())
        if len(self.frames) > self.COUNT:
            del self.frames[0]

    def reset(self):
        self.frames = []

    def fps(self):
        if len(self.frames) < 2:
            return 0
        ms = self.frames[-1] - self.frames[0]
        frames = len(self.frames) - 1
        return frames * 1000.0 / ms


class HUD(object):

    def __init__(self, surface, world):
        self.surface = surface
        self.world = world
        self.update_time = -1
        self.draw_time = -1
        self.world_info = HUDWorldInfo(surface, world, 0.5, 0)
        self.drawables = [
            self.world_info,
            HUDDebugInfo(surface, self, 0.5, 1),
            HUDShipInfo(surface, world.ship, 1, 0),
            HUDShipInfo(surface, world.ship2, 0, 0,
                        HUDShipInfo.GREEN_COLORS),
            HUDCompass(surface, world, world.ship, 1, 1,
                       HUDCompass.BLUE_COLORS),
            HUDCompass(surface, world, world.ship2, 0, 1,
                       HUDCompass.GREEN_COLORS),
        ]

    def reset_fps(self):
        self.world_info.fps.reset()

    def resize_screen(self):
        for d in self.drawables:
            d.resize_screen()

    def draw(self):
        for d in self.drawables:
            d.draw()


class HUDInfoPanel(object):

    STD_COLORS = [(0xff, 0xff, 0xff), (0xcc, 0xff, 0xff)]
    GREEN_COLORS = [(0x7f, 0xff, 0x00), (0xcc, 0xff, 0xff)]

    def __init__(self, surface, nrows, xalign=0, yalign=0, colors=STD_COLORS):
        self.surface = surface
        self.font = pygame.font.Font(None, 14)
        self.width = 70
        self.row_height = 11
        self.height = nrows * self.row_height
        self.xalign = xalign
        self.yalign = yalign
        self.color1, self.color2 = colors
        self.resize_screen()

    def resize_screen(self):
        self.pos = (10 + self.xalign * (self.surface.get_width() - 20 - self.width),
                    10 + self.yalign * (self.surface.get_height() - 20 - self.height))

    def draw_rows(self, *rows):
        x, y = self.pos
        for a, b in rows:
            self.surface.blit(self.font.render(str(a), True, self.color1), (x, y))
            img = self.font.render(str(b), True, self.color2)
            self.surface.blit(img, (x + self.width - img.get_width(), y))
            y += self.row_height


class HUDShipInfo(HUDInfoPanel):

    def __init__(self, surface, ship, xalign=0, yalign=0,
                 colors=HUDInfoPanel.STD_COLORS):
        HUDInfoPanel.__init__(self, surface, 4.5, xalign, yalign, colors)
        self.ship = ship

    def draw(self):
        self.draw_rows(
                ('direction', '%d' % self.ship.direction),
                ('heading', '%d' % arg(self.ship.velocity)),
                ('speed', '%.1f' % length(self.ship.velocity)),
                ('frags', '%d' % self.ship.frags),)
        x, y = self.pos
        y += self.height - 2
        w = max(0, int((self.width - 2) * self.ship.health))
        pygame.draw.rect(self.surface, self.color2, (x, y, self.width, 4), 1)
        self.surface.fill(self.color1, (x+1, y+1, w, 2))


class HUDWorldInfo(HUDInfoPanel):

    def __init__(self, surface, world, xalign=0, yalign=0,
                 colors=HUDInfoPanel.STD_COLORS):
        HUDInfoPanel.__init__(self, surface, 3, xalign, yalign, colors)
        self.world = world
        self.fps = FPSCounter()

    def draw(self):
        self.fps.frame()
        self.draw_rows(
                ('objects', len(self.world.objects)),
                ('fps', '%.0f' % self.fps.fps()))


class HUDDebugInfo(HUDInfoPanel):

    def __init__(self, surface, hud, xalign=0, yalign=0,
                 colors=HUDInfoPanel.STD_COLORS):
        HUDInfoPanel.__init__(self, surface, 3, xalign, yalign, colors)
        self.hud = hud

    def draw(self):
        self.draw_rows(
                ('update_time', self.hud.update_time),
                ('draw_time', self.hud.draw_time))


class HUDCompass(object):

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
    radar_scale = 0.1
    velocity_scale = 50

    def __init__(self, surface, world, ship, xalign=0, yalign=1,
                 colors=BLUE_COLORS):
        self.real_surface = surface
        self.world = world
        self.ship = ship
        self.width = self.height = 2*self.radius
        self.surface = pygame.Surface((self.width, self.height)).convert_alpha()
        self.bgcolor, self.fgcolor1, self.fgcolor2, self.fgcolor3 = colors
        self.xalign = xalign
        self.yalign = yalign
        self.resize_screen()

    def resize_screen(self):
        self.pos = (10 + self.xalign * (self.real_surface.get_width() - 20 - self.width),
                    10 + self.yalign * (self.real_surface.get_height() - 20 - self.height))

    def draw(self):
        x = y = self.radius
        self.surface.fill((0, 0, 0, 0))

        pygame.draw.circle(self.surface, self.bgcolor, (x, y), self.radius)
        self.surface.set_at((x, y), self.fgcolor1)

        for body in self.world.massive_objects:
            pos = (body.position - self.ship.position) * self.radar_scale
            if length(pos) > self.radius:
                continue
            self.surface.set_at((x + int(pos.x), y - int(pos.y)), self.fgcolor3)

        d = self.ship.direction_vector
        d = d.scaled(self.radius * 0.9)
        x2 = x + int(d.x)
        y2 = y - int(d.y)
        pygame.draw.aaline(self.surface, self.fgcolor2, (x, y), (x2, y2))

        v = self.ship.velocity * self.velocity_scale
        if length(v) > self.radius * 0.9:
            v = v.scaled(self.radius * 0.9)
        x2 = x + int(v.x)
        y2 = y - int(v.y)
        pygame.draw.aaline(self.surface, self.fgcolor1, (x, y), (x2, y2))

        self.real_surface.blit(self.surface, self.pos)


def main():
    pygame.init()
    pygame.display.set_caption('Newtonian Gravity')
    pygame.mouse.set_visible(False)

    modes = pygame.display.list_modes()
    if modes and modes != -1:
        fullscreen_mode = modes[0]
    else:
        fullscreen_mode = (1024, 768) # shrug
    w, h = fullscreen_mode
    windowed_mode = (int(w * 0.8), int(h * 0.8))
    screen = pygame.display.set_mode(windowed_mode)
    in_fullscreen = False

    viewport = Viewport(screen)
    world = make_world()
    viewport.origin = (world.ship.position + world.ship2.position) * 0.5
    hud = HUD(screen, world)
    next_tick = pygame.time.get_ticks() + JIFFY_IN_MS
    while True:
        event = pygame.event.poll()
        if event.type == QUIT:
            break
        if event.type == KEYDOWN:
            if event.key == K_ESCAPE:
                break
            if event.key == K_q:
                break
            if event.key == K_p:
                while True:
                    event = pygame.event.wait()
                    if event.type in (KEYDOWN, QUIT, MOUSEBUTTONUP):
                        break
                next_tick = pygame.time.get_ticks() + JIFFY_IN_MS
                hud.reset_fps()
                continue
            if event.key == K_o:
                viewport.show_orbits = not viewport.show_orbits
            if event.key == K_f:
                in_fullscreen = not in_fullscreen
                if in_fullscreen:
                    pygame.display.set_mode(fullscreen_mode, FULLSCREEN)
                else:
                    pygame.display.set_mode(windowed_mode)
                viewport.resize_screen()
                hud.resize_screen()

            if event.key == K_RCTRL:
                world.add(world.ship.shoot(MISSILE_SPEED))
            if event.key == K_RALT:
                if length_sq(world.ship.velocity) < 1.0:
                    world.ship.velocity = Vector(0, 0)
                else:
                    world.ship.velocity *= 0.95

            if event.key == K_LCTRL:
                world.add(world.ship2.shoot(MISSILE_SPEED))
            if event.key == K_LALT:
                if length_sq(world.ship2.velocity) < 1.0:
                    world.ship2.velocity = Vector(0, 0)
                else:
                    world.ship2.velocity *= 0.95

            if event.key == K_6:
                for n in range(1, 50):
                    world.add(world.ship.shoot(n, 0))

        if pygame.key.get_pressed()[K_EQUALS]:
            viewport.scale *= SCALE_FACTOR
        if pygame.key.get_pressed()[K_MINUS]:
            viewport.scale /= SCALE_FACTOR

        if pygame.key.get_pressed()[K_LEFT]:
            world.ship.left_thrust = ROTATION_SPEED
        if pygame.key.get_pressed()[K_RIGHT]:
            world.ship.right_thrust = ROTATION_SPEED
        if pygame.key.get_pressed()[K_UP]:
            world.ship.forward_thrust = FRONT_THRUST
        if pygame.key.get_pressed()[K_DOWN]:
            world.ship.rear_thrust = REAR_THRUST

        if pygame.key.get_pressed()[K_a]:
            world.ship2.left_thrust = ROTATION_SPEED
        if pygame.key.get_pressed()[K_d]:
            world.ship2.right_thrust = ROTATION_SPEED
        if pygame.key.get_pressed()[K_w]:
            world.ship2.forward_thrust = FRONT_THRUST
        if pygame.key.get_pressed()[K_s]:
            world.ship2.rear_thrust = REAR_THRUST

        start = pygame.time.get_ticks()
        world.update(DELTA_TIME)
        hud.update_time = pygame.time.get_ticks() - start
        if (pygame.time.get_ticks() < next_tick + JIFFY_IN_MS
            or pygame.time.get_ticks() > last_frame_time + 500):
            start = pygame.time.get_ticks()
            screen.fill((0,0,0))
            viewport.keep_visible(world.ship.position, world.ship2.position)
            world.draw(viewport)
            hud.draw()
            hud.draw_time = pygame.time.get_ticks() - start
            pygame.display.flip()
            last_frame_time = pygame.time.get_ticks()
            delay = next_tick - last_frame_time
            if delay > 0:
                pygame.time.wait(delay)
        next_tick += JIFFY_IN_MS


def profile():
    import hotshot
    p = hotshot.Profile('newton.hotshot')
    p.runcall(main)
    print "Loading profiler results (takes a while)..."
    import hotshot.stats
    stats = hotshot.stats.load('newton.hotshot')
    stats.sort_stats('time')
    stats.print_stats(20)

if __name__ == '__main__':
    import sys
    if '-o' in sys.argv:
        import psyco
        psyco.full()
        main()
    elif '-p' in sys.argv:
        profile()
    else:
        main()
