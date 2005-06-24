#!/usr/bin/python
import math
import pygame
import pygame.draw
from pygame.locals import *


GRAVITY = 2.0 # constant of gravitation

FPS = 20
JIFFY_IN_MS = 1000 / FPS    # 1 jiffy in ms
DELTA_TIME = 2.0            # world time units in one jiffy
SCALE_FACTOR = 1.25         # scale factor per jiffy for +/-
ROTATION_SPEED = 10         # angles per jiffy for left/right
FRONT_THRUST = 0.2          # forward acceleration
REAR_THRUST = 0.1           # backward acceleration
MISSILE_SPEED = 3           # missile speed


class Vector(tuple):

    x = property(lambda self: self[0])
    y = property(lambda self: self[1])

    def __new__(cls, *args):
        if len(args) == 2:
            return tuple.__new__(cls, args)
        else:
            return tuple.__new__(cls, *args)

    def __mul__(self, factor):
        return Vector(self[0] * factor, self[1] * factor)

    def __div__(self, divisor):
        return Vector(self[0] / float(divisor), self[1] / float(divisor))

    def __add__(self, other):
        return Vector(self[0] + other[0], self[1] + other[1])

    def __sub__(self, other):
        return Vector(self[0] - other[0], self[1] - other[1])

    def perpendicular(self):
        return Vector(-self.y, self.x)

    def scaled(self, new_length=1.0):
        return self * new_length / length(self)


def length_sq(vector):
    return vector.x ** 2 + vector.y ** 2


def length(vector):
    return math.sqrt(length_sq(vector))


def arg(vector):
    angle = math.atan2(vector.y, vector.x) * 180 / math.pi
    if angle < 0:
        angle += 360
    return round(angle)


class Viewport(object):

    def __init__(self, surface):
        self.surface = surface
        self.scale = 1.0
        self.origin = Vector(0, 0)

    def screen_len(self, world_len):
        return int(world_len * self.scale)

    def screen_pos(self, world_pos):
        surface_w, surface_h = self.surface.get_size()
        # screen_pos((0, 0)) == (surface_w/2, surface_h/2)
        # screen_pos((1, 2)) == (surface_w/2 + scale, surface_h/2 + 2*scale)
        world_x, world_y = world_pos - self.origin
        x = surface_w * 0.5 + world_x * self.scale
        y = surface_h * 0.5 - world_y * self.scale
        return (int(x), int(y))


class World(object):

    def __init__(self):
        self.objects = []

    def add(self, obj):
        self.objects.append(obj)

    def update(self, dt):
        for obj in self.objects:
            for other in self.objects:
                if other is not obj:
                    obj.gravitate(other, dt)
        for obj in self.objects:
            obj.move(dt)

    def draw(self, viewport):
        for obj in self.objects:
            obj.draw(viewport)


class Body(object):

    def __init__(self, position, mass=0, velocity=Vector(0, 0)):
        self.position = Vector(position)
        self.mass = mass
        self.velocity = velocity
        self.pinned = False

    def pin(self):
        self.pinned = True

    def gravitate(self, other, dt=1.0):
        # F = m1 * a = G*m1*m2/r**2
        # a = G * m2 / r**2
        if other.mass == 0 or self.pinned:
            return
        vector = other.position - self.position
        sq_of_distance = length_sq(vector)
        distance = math.sqrt(sq_of_distance)
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


class Planet(Body):

    def __init__(self, position, radius, mass, color):
        Body.__init__(self, position, mass)
        self.radius = radius
        self.color = color

    def draw(self, viewport):
        pos = viewport.screen_pos(self.position)
        radius = viewport.screen_len(self.radius)
        pygame.draw.circle(viewport.surface, self.color, pos, radius)


class Ship(Body):

    def __init__(self, position, size=10, color=(255, 255, 255)):
        Body.__init__(self, position, 0)
        self.size = size
        self.direction = 0
        self.color = color

    def set_direction(self, direction):
        direction = direction % 360
        if direction < 0: direction += 360
        self._direction = direction
        angle = direction * math.pi / 180
        self.direction_vector = Vector(math.cos(angle), math.sin(angle))

    direction = property(lambda self: self._direction, set_direction)

    def draw(self, viewport):
        direction_vector = self.direction_vector * self.size
        side_vector = direction_vector.perpendicular()
        pt1 = self.position - direction_vector + side_vector * 0.5
        pt2 = self.position + direction_vector
        pt3 = self.position - direction_vector - side_vector * 0.5
        points = map(viewport.screen_pos, [pt1, pt2, pt3])
        pygame.draw.lines(viewport.surface, self.color, False, points)

    def shoot(self, extra_speed):
        missile = Missile(self.position + self.direction_vector * self.size,
                          self.velocity + self.direction_vector * extra_speed,
                          self.color)
        return missile


class Missile(Body):

    def __init__(self, position, velocity, color):
        Body.__init__(self, position, velocity=velocity)
        self.color = color
        self.orbit = []

    def move(self, dt):
        self.orbit.append(self.position)
        if len(self.orbit) > 100:
            del self.orbit[0]
        Body.move(self, dt)

    def draw(self, viewport):
        if self.orbit:
            red, green, blue = self.color
            a = 0.1
            b = 0.7 / len(self.orbit)
            for n, pt in enumerate(self.orbit):
                f = a+n*b
                color = (red*f, green*f, blue*f)
                viewport.surface.set_at(viewport.screen_pos(pt), color)
        viewport.surface.set_at(viewport.screen_pos(self.position), self.color)


def make_world():
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


class HUD(object):

    def __init__(self, surface, world):
        self.world = world
        self.surface = surface
        self.font = pygame.font.Font(None, 14)

    def draw(self):
        x0, y0 = 5, 5
        w1, h1 = 60, 10
        x1 = x0 + w1
        y1 = y0 + h1
        y2 = y1 + h1
        y3 = y2 + h1

        def say(x, y, text, color):
            self.surface.blit(self.font.render(text, True, color), (x, y))

        say(x0, y0, "direction", (255, 255, 255))
        say(x1, y0, "%3d" % self.world.ship.direction, (200, 255, 225))
        say(x0, y1, "heading", (255, 255, 255))
        say(x1, y1, "%3d" % arg(self.world.ship.velocity), (200, 255, 225))
        say(x0, y2, "speed", (255, 255, 255))
        say(x1, y2, "%3.1f" % length(self.world.ship.velocity), (200, 255, 225))
        say(x0, y3, "objects", (255, 255, 255))
        say(x1, y3, "%d" % len(self.world.objects), (200, 255, 225))


def main():
    pygame.init()
    screen = pygame.display.set_mode((800, 600))
    viewport = Viewport(screen)
    world = make_world()
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
            if event.key in (K_LCTRL, K_RCTRL):
                world.add(world.ship.shoot(MISSILE_SPEED))
        if pygame.key.get_pressed()[K_EQUALS]:
            viewport.scale *= SCALE_FACTOR
        if pygame.key.get_pressed()[K_MINUS]:
            viewport.scale /= SCALE_FACTOR
        if pygame.key.get_pressed()[K_LEFT]:
            world.ship.direction += ROTATION_SPEED
        if pygame.key.get_pressed()[K_RIGHT]:
            world.ship.direction -= ROTATION_SPEED
        if pygame.key.get_pressed()[K_UP]:
            world.ship.velocity += world.ship.direction_vector * FRONT_THRUST
        if pygame.key.get_pressed()[K_DOWN]:
            world.ship.velocity -= world.ship.direction_vector * REAR_THRUST
        world.update(DELTA_TIME)
        screen.fill((0,0,0))
        viewport.origin = world.ship.position
        world.draw(viewport)
        hud.draw()
        pygame.display.flip()
        delay = next_tick - pygame.time.get_ticks()
        if delay > 0:
            pygame.time.wait(delay)
        next_tick += JIFFY_IN_MS


if __name__ == '__main__':
    main()
