"""
The world of PySpaceWar
"""

import math
import random
import time


class Vector(tuple):
    """A two-dimensional real vector.

        >>> v1 = Vector(3.5, -2.5)
        >>> v1.x, v1.y
        (3.5, -2.5)

    Vectors are immutable.

        >>> v1.x = 5
        Traceback (most recent call last):
          ...
        AttributeError: ...

    """

    __slots__ = ()

    # Nice accessories.  Sort of expensive, though: according to timeit,
    # v.x is 5 times slower than v[0].  It would be possible to shave off
    # 2.5 milliseconds off world update time by using [0], [1] instead of
    # .x, .y everywhere.  Time to rewrite in C?
    x = property(lambda self: self[0])
    y = property(lambda self: self[1])

    def __new__(cls, x, y):
        return tuple.__new__(cls, (x, y))

    def from_polar(direction, magnitude=1.0):
        """Create a new vector from polar coordinates.

        ``direction`` is the angle in degrees (0 points in the direction of the
        x axis, 90 points in the direction of the y axis).

            >>> print(Vector.from_polar(90, 3.5))
            (0.000, 3.500)

            >>> print(Vector.from_polar(135, 1))
            (-0.707, 0.707)

        """
        angle = direction * math.pi / 180
        return Vector(magnitude * math.cos(angle), magnitude * math.sin(angle))
    from_polar = staticmethod(from_polar)

    def __str__(self):
        """Return an (approximate) human-readable string representation.

            >>> print(Vector.from_polar(-90, 1))
            (0.000, -1.000)

        """
        return '(%.3f, %.3f)' % self

    def __repr__(self):
        """Return an accurate string representation.

            >>> Vector.from_polar(-90, 1)           # doctest:+ELLIPSIS
            Vector(6.123...e-17, -1.0)

        """
        return 'Vector(%r, %r)' % self

    def __mul__(self, factor):
        """Multiply the vector by a scalar.

            >>> Vector(1.5, 2.5) * 3
            Vector(4.5, 7.5)
            >>> 3 * Vector(1.5, 2.5)
            Vector(4.5, 7.5)

        """
        return Vector(self.x * factor, self.y * factor)

    __rmul__ = __mul__

    def dot_product(self, other):
        """Compute the dot product of two vectors.

            >>> Vector(3, 5).dot_product(Vector(-1, 2))
            7

        """
        return self.x * other.x + self.y * other.y

    def cross_product(self, other):
        """Compute the cross product of two vectors.

            >>> Vector(3, 5).cross_product(Vector(-1, 2))
            11

        """
        return self.x * other.y - self.y * other.x

    def __truediv__(self, divisor):
        """Divide the vector by a scalar.

            >>> Vector(1.5, 7.5) / 3
            Vector(0.5, 2.5)

            >>> print(Vector(1, 2) / 3)
            (0.333, 0.667)

        """
        return Vector(self.x / float(divisor), self.y / float(divisor))

    __div__ = __truediv__

    def __add__(self, other):
        """Add two vectors.

            >>> Vector(1.5, 2.5) + Vector(-0.5, 3)
            Vector(1.0, 5.5)

        """
        return Vector(self.x + other.x, self.y + other.y)

    def __sub__(self, other):
        """Subtract two vectors.

            >>> Vector(1.5, 2.5) - Vector(-0.5, 3)
            Vector(2.0, -0.5)

        """
        return Vector(self[0] - other[0], self[1] - other[1])

    def __neg__(self):
        """Multiply the vector by -1.

            >>> -Vector(1.5, 2.5)
            Vector(-1.5, -2.5)

        """
        return Vector(-self.x, -self.y)

    def length(self):
        """Compute the length of the vector.

            >>> Vector(3, 4).length()
            5.0

        """
        return math.hypot(self[0], self[1])

    def direction(self):
        """Compute the direction of the vector (in degrees).

            >>> Vector(1, 0).direction()
            0.0
            >>> Vector(0, 1).direction()
            90.0
            >>> Vector(-1, 0).direction()
            180.0
            >>> Vector(0, -1).direction()
            270.0
            >>> Vector(-1, 1).direction()
            135.0

        """
        angle = math.atan2(self.y, self.x) * 180 / math.pi
        if angle < 0:
            angle += 360
        return angle

    def perpendicular(self):
        """Compute a perpendicular vector of the same length.

        Returns the vector rotated clockwise by 90 degrees (assuming the usual
        mathematical direction of axes: x points right, y points up).

            >>> print(Vector(2, 1).perpendicular())
            (-1.000, 2.000)

        """
        return Vector(-self.y, self.x)

    def scaled(self, new_length=1.0):
        """Scale the vector to a given magnitude.

            >>> v = Vector(2, 1).scaled(5)
            >>> print(round(v.length(), 3))
            5.0
            >>> print(v)
            (4.472, 2.236)

        If you omit the magnitude, you get a normalized vector

            >>> print(round(v.scaled().length(), 3))
            1.0

        """
        return self * new_length / self.length()


class World(object):
    """The game universe.

    Example:

        w = World()
        w.add(planet)
        w.add(ship)
        while True:
            # Tell the ship what to do during the next update
            # Draw the state of the world
            w.update(0.1)
            time.sleep(0.1)

    """

    GRAVITY = 0.01              # constant of gravitation
    BOUNCE_SPEED_LOSS = 0.1     # lose 10% speed when bouncing off something

    # Some debug information
    time_for_gravitation = 0    # Time to calculate gravitation
    time_for_collisions = 0     # Time to detect collisions

    def __init__(self, rng=None):
        if rng is None:
            rng = random.Random()
        self.rng = rng
        self.time = 0.0
        self.objects = []
        self._objects_with_zero_radius = []
        self._objects_with_nonzero_radius = []
        self._in_update = False
        self._add_queue = []
        self._remove_queue = []

    def add(self, obj):
        """Add a new object to the universe.

        Objects living in the universe must have the following methods:

            gravitate(massive_object, delta_time)
                react to gravity from massive_object for a particular time
            move(delta_time)
                move for a particular time
            collission(other_object)
                handle a collision
            distance_to(other_object)
                calculate the distance to another object

        and a ``radius`` attribute, used for collision detection.

        Objects added to a universe will get a ``world`` attribute.
        """
        if self._in_update:
            if obj in self._remove_queue:
                self._remove_queue.remove(obj)
            else:
                self._add_queue.append(obj)
        else:
            self.objects.append(obj)
            obj.world = self
            if obj.radius:
                self._objects_with_nonzero_radius.append(obj)
            else:
                self._objects_with_zero_radius.append(obj)

    def remove(self, obj):
        """Remove an object from the universe."""
        if self._in_update:
            if obj in self._add_queue:
                self._add_queue.remove(obj)
            else:
                self._remove_queue.append(obj)
        else:
            self.objects.remove(obj)
            obj.world = None
            if obj.radius:
                self._objects_with_nonzero_radius.remove(obj)
            else:
                self._objects_with_zero_radius.remove(obj)

    def update(self, dt):
        """Make time happen (dt time units of it).

        Calculates gravity effects, moves the objects around, checks for
        collisions.
        """
        self._in_update = True
        self.time += dt
        # Gravity: affects velocities, but not positions
        start = time.time()
        for massive_obj in self.objects:
            if not massive_obj.mass:
                continue
            for obj in self.objects:
                if obj is not massive_obj:
                    obj.gravitate(massive_obj, dt)
        self.time_for_gravitation = time.time() - start
        # Movement: affects positions, may affect velocities
        for obj in self.objects:
            obj.move(dt)
        # Collision detection: may affect positions and velocities
        start = time.time()
        for n, obj1 in enumerate(self._objects_with_nonzero_radius):
            for obj2 in (self._objects_with_nonzero_radius[n+1:] +
                         self._objects_with_zero_radius):
                if self.collide(obj1, obj2):
                    obj1.collision(obj2)
                    obj2.collision(obj1)
        self.time_for_collisions = time.time() - start
        self._in_update = False
        if self._add_queue:
            for obj in self._add_queue:
                self.add(obj)
            self._add_queue = []
        if self._remove_queue:
            for obj in self._remove_queue:
                self.remove(obj)
            self._remove_queue = []

    def collide(self, obj1, obj2):
        """Check whether two objects collide."""
        collision_distance = obj1.radius + obj2.radius
        return obj1.distance_to(obj2) < collision_distance


class Object(object):
    """A material object in the game universe.

        >>> o = Object(Vector(45.0, 110.0), appearance=42)
        >>> o.position
        Vector(45.0, 110.0)
        >>> o.velocity
        Vector(0.0, 0.0)
        >>> o.mass
        0
        >>> o.radius
        0

    Appearance is an opaque field that user interface code can use to
    distinguish between different objects of the same kind.

        >>> o.appearance
        42

    """

    def __init__(self, position=Vector(0.0, 0.0), velocity=Vector(0.0, 0.0),
                 mass=0, radius=0, appearance=0):
        self.position = position
        self.mass = mass
        self.radius = radius
        self.velocity = velocity
        self.appearance = appearance
        self.world = None
        self.bounce_effect = None

    def distance_to(self, other):
        """Calculate the distance to another object.

            >>> sun = Object(Vector(30, 40))
            >>> tincan = Object(Vector(0, 0))
            >>> tincan.distance_to(sun)
            50.0
            >>> sun.distance_to(tincan)
            50.0

        """
        sp = self.position
        op = other.position
        return math.hypot(sp[0] - op[0], sp[1] - op[1])

    def gravitate(self, massive_object, dt):
        """React to gravity from massive_object for a particular time.

            >>> sun = Object(Vector(0, 10), mass=200)
            >>> tincan = Object(Vector(0, 0))
            >>> tincan.world = World()
            >>> tincan.gravitate(sun, 1.0)
            >>> print(tincan.velocity)
            (0.000, 0.020)

            >>> tincan.gravitate(sun, 1.0)
            >>> print(tincan.velocity)
            (0.000, 0.040)

            >>> tincan.gravitate(sun, .5)
            >>> print(tincan.velocity)
            (0.000, 0.050)

        """
        # Newton's laws of motion:
        #   F = G * m1 * m2 / r**2
        #   a = F / m1 = G * m2 / r ** 2
        # where
        #   F is force of attraction
        #   G is the constant of gravitation
        #   m1 and m2 are the masses of interacting bodies
        #   r is the distance between interacting bodies
        #   a is the acceleration of the body with mass m1
        # We consider time t from t0 to t1 where t1 = t0 + dt
        #   v(t1) = v(t0) + integral(t=t0..t1, a(t)dt)
        #   a(t) = G * m2 / r(t) ** 2
        # For simplicity's sake let's assume r(t) is constant.  Then a(t) is
        # also constant, and
        #   v(t1) = v(t0) + a * dt

        # Nice code:
        #   vector = massive_object.position - self.position
        #   distance = vector.length()
        #   magnitude = self.world.GRAVITY * massive_object.mass / distance**2
        #   acceleration = vector * (magnitude * dt / distance)
        #   self.velocity += acceleration
        # The equivalent fast code:
        dx = massive_object.position[0] - self.position[0]
        dy = massive_object.position[1] - self.position[1]
        distance = math.hypot(dx, dy)
        f = self.world.GRAVITY * massive_object.mass * dt / distance ** 3
        self.velocity = Vector(self.velocity[0] + dx * f,
                               self.velocity[1] + dy * f)

    def move(self, dt):
        """Move for a particular time.

            >>> tincan = Object(Vector(0, 0), velocity=Vector(0.5, 1.0))
            >>> tincan.move(1.0)
            >>> tincan.position
            Vector(0.5, 1.0)

            >>> tincan.move(1.0)
            >>> tincan.position
            Vector(1.0, 2.0)

            >>> tincan.move(2.0)
            >>> tincan.position
            Vector(2.0, 4.0)

        """
        self.position += self.velocity * dt

    def collision(self, other):
        """Handle a collision with another object.

        The default implementation is bouncing off things.
        """
        self.bounce(other)

    def bounce(self, other):
        """Bounce from another object.

            >>> asteroid = Object(Vector(3, 4), velocity=Vector(0.1, 0.2),
            ...                   mass=14, radius=2)
            >>> tincan = Object(Vector(0.5, 4), velocity=Vector(1.5, -0.3),
            ...                 mass=1, radius=1)
            >>> tincan.world = World()

            >>> tincan.bounce(asteroid)
            >>> print(tincan.velocity)
            (-1.350, -0.270)
            >>> print(tincan.position)
            (0.000, 4.000)

        The bounce is not physically realistic (e.g. total energy/momentum
        is not preserved).
        """
        normal = (self.position - other.position).scaled()
        delta = normal.x * self.velocity.x + normal.y * self.velocity.y
        self.velocity -= normal.scaled(2 * delta)
        # Let's lose some speed
        self.velocity *= 1 - self.world.BOUNCE_SPEED_LOSS
        # Let's also make sure the objects do not overlap
        collision_distance = other.radius + self.radius
        self.position = other.position + normal.scaled(collision_distance)
        if self.bounce_effect:
            self.bounce_effect(self, other)

    def add_debris(self, howmany=None, maxdistance=1.0, time=5.0):
        """Add some debris."""
        rng = self.world.rng
        if not howmany:
            howmany = rng.randrange(3, 6)
        for n in range(howmany):
            color = (rng.randrange(0xf0, 0xff),
                     rng.randrange(0x70, 0x90),
                     rng.randrange(0, 0x20))
            velocity = self.velocity * 0.3
            velocity += Vector.from_polar(rng.uniform(0, 360),
                                          rng.uniform(0, maxdistance))
            debris = Debris(self.position, velocity, appearance=color,
                            time_limit=time)
            self.world.add(debris)


class Planet(Object):
    """A planet in the game universe.

    Planets have mass and attract other things.  Planets themselves are not
    affected by gravity (computing stable orbits for N planets is too
    difficult, especially with the numeric approximations I take).
    """

    def gravitate(self, massive_object, dt):
        """Don't react to gravity."""
        pass

    def collision(self, other):
        """Handle a collision: nothing happens to a planet."""
        pass


class Ship(Object):
    """A powered ship.

        >>> ship = Ship(Vector(0, 0), size=10, direction=45)
        >>> ship.size
        10
        >>> ship.radius
        6.0

        >>> ship.health
        1.0

    You tell the ship what to do, and the ship does it

        >>> ship.turn_left()
        >>> ship.accelerate()
        >>> ship.move(1.0)
        >>> ship.direction
        50.0
        >>> print(ship.velocity.length())
        0.1

    """

    SIZE_TO_RADIUS = 0.6        # Ships aren't circular.  To simulate more or
                                # less convincing collisions we need to have a
                                # collision radius smaller than ship size.

    forward_power = 0.1         # Default engine power for forward thrust
    backward_power = 0.05       # Default engine power for backward thrust
    brake_factor = 0.95         # Default brake effectiveness (lose 5% speed)
    brake_threshold = 0.5       # Speed below which brakes are 100% efficient
    rotation_speed = 5          # Lateral thruster power (angles per time unit)
    launch_speed = 3.0          # Missile launch speed
    missile_recoil = 0.01       # Missile recoil factor
    missile_damage = 0.6        # Damage done by the missile
    collision_damage = 0.05     # Damage done by a collision
    missile_time_limit = (1200, 1300)  # Range for missile self-destruct timer

    def __init__(self, position=Vector(0, 0), velocity=Vector(0, 0), size=10,
                 direction=0, appearance=0):
        Object.__init__(self, position, velocity=velocity,
                        radius=size * self.SIZE_TO_RADIUS,
                        appearance=appearance)
        self.size = size
        self.direction = direction
        self.forward_thrust = 0
        self.rear_thrust = 0
        self.left_thrust = 0
        self.right_thrust = 0
        self.engage_brakes = False
        self.health = 1.0
        self.frags = 0
        self.dead = False
        self.spawn_time = 0  # the value of world.time when last respawned
        self.launch_effect = None
        self.hit_effect = None
        self.explode_effect = None
        self.respawn_effect = None

    def _set_direction(self, direction):
        """Set the direction of the ship.

        The direction is given in angles.  It will be normalized so that
        0 <= direction < 360.

        The direction_vector attribute is also set.
        """
        direction = direction % 360
        self._direction = direction
        self.direction_vector = Vector.from_polar(direction)

    direction = property(lambda self: self._direction, _set_direction)

    def turn_left(self):
        """Tell the ship to turn left."""
        if self.dead:
            return
        self.left_thrust = self.rotation_speed

    def turn_right(self):
        """Tell the ship to turn right."""
        if self.dead:
            return
        self.right_thrust = self.rotation_speed

    def accelerate(self):
        """Tell the ship to accelerate in the direction of the ship."""
        if self.dead:
            return
        self.forward_thrust = self.forward_power

    def backwards(self):
        """Tell the ship to accelerate in the opposite direction."""
        if self.dead:
            return
        self.rear_thrust = self.backward_power

    def brake(self):
        """Tell the ship to brake."""
        if self.dead:
            return
        if self.velocity != (0, 0):
            self.engage_brakes = True

    def gravitate(self, massive_object, dt):
        """Don't react to gravity.  Because of, um, anti-gravity engines."""
        if not self.dead:
            return
        Object.gravitate(self, massive_object, dt)

    def move(self, dt):
        """Apply thrusters and move in the universe."""
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
        if self.engage_brakes:
            if self.velocity.length() <= self.brake_threshold:
                self.velocity = Vector(0.0, 0.0)
            else:
                self.velocity *= self.brake_factor
            self.engage_brakes = False
        Object.move(self, dt)

    def collision(self, other):
        """Handle a collision."""
        killed_by = None
        if isinstance(other, Debris):
            return
        elif isinstance(other, Missile):
            self.health -= self.missile_damage
            killed_by = other.launched_by
            self.velocity += other.velocity * self.missile_recoil
            if self.hit_effect:
                self.hit_effect(self, other)
        else:
            self.health -= self.collision_damage
            self.bounce(other)
        if self.health < 0 and not self.dead:
            self.die(killed_by)

    def die(self, killed_by=None):
        """The ship has received terminal damage."""
        self.dead = True
        self.forward_thrust = 0
        self.rear_thrust = 0
        self.left_thrust = 0
        self.right_thrust = 0
        if killed_by is None or killed_by is self:
            self.frags -= 1
        else:
            killed_by.frags += 1
        self.add_debris(time=50, maxdistance=self.size * 0.5,
                        howmany=self.world.rng.randrange(9, 21))
        if self.explode_effect:
            self.explode_effect(self, killed_by)

    def respawn(self):
        """Respawn back into the world."""
        self.dead = False
        self.health = 1.0
        if self.world:
            self.spawn_time = self.world.time
        if self.respawn_effect:
            self.respawn_effect(self)

    def launch(self):
        """Launch a missile."""
        if self.dead:
            return
        direction_vector = self.direction_vector
        time_limit = self.world.rng.uniform(*self.missile_time_limit)
        missile = Missile(self.position + direction_vector * self.size,
                          self.velocity + direction_vector * self.launch_speed,
                          self.appearance, launched_by=self,
                          time_limit=time_limit)
        recoil = direction_vector * self.launch_speed * self.missile_recoil
        self.velocity -= recoil
        self.world.add(missile)
        if self.launch_effect:
            self.launch_effect(self, missile)


class Missile(Object):
    """A missile.

    Ships fire missiles.  Missiles are unpowered and cannot manoeuvre.
    Missiles explode on contact and self-destruct after a set time limit.
    """

    def __init__(self, position=Vector(0, 0), velocity=Vector(0, 0),
                 appearance=0, launched_by=None, time_limit=1e1000):
        Object.__init__(self, position=position, velocity=velocity,
                        appearance=appearance)
        self.launched_by = launched_by
        self.time_limit = time_limit
        self.dead = False

    def move(self, dt):
        """Move in the universe.  Check the self-destruct timer."""
        Object.move(self, dt)
        self.time_limit -= dt
        if self.time_limit < 0:
            self.explode()

    def explode(self):
        """Self-destruct."""
        if not self.dead:
            self.dead = True
            self.add_debris()
            self.world.remove(self)

    def collision(self, other):
        """Explode on collision."""
        self.explode()


class Debris(Object):
    """Debris is what remains when something explodes."""

    def __init__(self, position=Vector(0, 0), velocity=Vector(0, 0),
                 appearance=0, time_limit=10):
        Object.__init__(self, position, velocity=velocity,
                        appearance=appearance)
        self.time_limit = time_limit

    def move(self, dt):
        """Move in the universe.  Check the time left to live."""
        Object.move(self, dt)
        self.time_limit -= dt
        if self.time_limit < 0:
            self.world.remove(self)
