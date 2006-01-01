"""
The world of PySpaceWar
"""

import math


class Vector(tuple):
    """A two-dimensional real vector.

        >>> v1 = Vector(3.5, -2.5)
        >>> v1.x, v1.y
        (3.5, -2.5)

    Vectors are immutable.

        >>> v1.x = 5
        Traceback (most recent call last):
          ...
        AttributeError: can't set attribute

    """

    x = property(lambda self: self[0])
    y = property(lambda self: self[1])

    def __new__(cls, *args):
        """Create a new vector.

        You can use Vector(x, y) as well as Vector((x, y)).  In particular, if
        ``v`` is a Vector, you can write Vector(v).

            >>> v1 = Vector(3.5, -2.5)
            >>> v2 = Vector(v1)
            >>> v1 == v2
            True

        """
        if len(args) == 2:
            return tuple.__new__(cls, args)
        else:
            return tuple.__new__(cls, *args)

    def from_polar(direction, magnitude=1.0):
        """Create a new vector from polar coordinates.

        ``direction`` is the angle in degrees (0 points in the direction of the
        x axis, 90 points in the direction of the y axis).

            >>> print Vector.from_polar(90, 3.5)
            (0.000, 3.500)

            >>> print Vector.from_polar(135, 1)
            (-0.707, 0.707)

        """
        angle = direction * math.pi / 180
        return Vector(magnitude * math.cos(angle), magnitude * math.sin(angle))
    from_polar = staticmethod(from_polar)

    def __str__(self):
        """Return an (approximate) human-readable string representation.

            >>> print Vector.from_polar(-90, 1)
            (0.000, -1.000)

        """
        return '(%.3f, %.3f)' % self

    def __repr__(self):
        """Return an accurate string representation.

            >>> Vector.from_polar(-90, 1)
            Vector(6.1230317691118863e-17, -1.0)

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

    def __div__(self, divisor):
        """Divide the vector by a scalar.

            >>> Vector(1.5, 7.5) / 3
            Vector(0.5, 2.5)

            >>> print Vector(1, 2) / 3
            (0.333, 0.667)

        """
        return Vector(self.x / float(divisor), self.y / float(divisor))

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
        return Vector(self.x - other.x, self.y - other.y)

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
        return math.hypot(*self)

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

            >>> print Vector(2, 1).perpendicular()
            (-1.000, 2.000)

        """
        return Vector(-self.y, self.x)

    def scaled(self, new_length=1.0):
        """Scale the vector to a given magnitude.

            >>> v = Vector(2, 1).scaled(5)
            >>> v.length()
            5.0
            >>> print v
            (4.472, 2.236)

        If you omit the magnitude, you get a normalized vector

            >>> v.scaled().length()
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

    GRAVITY = 0.01          # constant of gravitation
    BOUNCE_SPEED_LOSS = 0.1 # lose 10% speed when bouncing off something

    def __init__(self):
        self.time = 0.0
        self.objects = []
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
            distanceTo(other_object)
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

    def update(self, dt):
        """Make time happen (dt time units of it).

        Calculates gravity effects, moves the objects around, checks for
        collisions.
        """
        self._in_update = True
        self.time += dt
        # Gravity: affects velocities, but not positions
        for massive_obj in self.objects:
            if not massive_obj.mass:
                continue
            for obj in self.objects:
                if obj is not massive_obj:
                    obj.gravitate(massive_obj, dt)
        # Movement: affects positions, may affect velocities
        for obj in self.objects:
            obj.move(dt)
        # Collision detection: may affect positions and velocities
        for n, obj1 in enumerate(self.objects):
            for obj2 in self.objects[n+1:]:
                if self.collide(obj1, obj2):
                    obj1.collision(obj2)
                    obj2.collision(obj1)
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
        return obj1.distanceTo(obj2) < collision_distance


class Object(object):
    """A material object in the game universe.

        >>> o = Object(Vector(45.0, 110.0))
        >>> o.position
        Vector(45.0, 110.0)
        >>> o.velocity
        Vector(0.0, 0.0)
        >>> o.mass
        0
        >>> o.radius
        0

    """

    def __init__(self, position, velocity=Vector(0.0, 0.0), mass=0, radius=0):
        self.position = position
        self.mass = mass
        self.radius = radius
        self.velocity = velocity

    def distanceTo(self, other):
        """Calculate the distance to another object.

            >>> sun = Object(Vector(30, 40))
            >>> tincan = Object(Vector(0, 0))
            >>> tincan.distanceTo(sun)
            50.0
            >>> sun.distanceTo(tincan)
            50.0

        """
        return (self.position - other.position).length()

    def gravitate(self, massive_object, dt):
        """React to gravity from massive_object for a particular time.

            >>> sun = Object(Vector(0, 10), mass=200)
            >>> tincan = Object(Vector(0, 0))
            >>> tincan.world = World()
            >>> tincan.gravitate(sun, 1.0)
            >>> print tincan.velocity
            (0.000, 0.020)

            >>> tincan.gravitate(sun, 1.0)
            >>> print tincan.velocity
            (0.000, 0.040)

            >>> tincan.gravitate(sun, .5)
            >>> print tincan.velocity
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
        vector = massive_object.position - self.position
        sq_of_distance = vector.length() ** 2
        magnitude = self.world.GRAVITY * massive_object.mass / sq_of_distance
        acceleration = vector.scaled(magnitude * dt)
        self.velocity += acceleration

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
            >>> print tincan.velocity
            (-1.350, -0.270)
            >>> print tincan.position
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

        >>> ship.turn_left(15)
        >>> ship.accelerate(10)
        >>> ship.move(1.0)
        >>> ship.direction
        60.0
        >>> ship.velocity.length()
        10.0

    """

    SIZE_TO_RADIUS = 0.6    # Ships aren't circular.  To simulate more or
                            # less convincing collisions we need to have a
                            # collision radius smaller than ship size.

    def __init__(self, position, size, direction=0):
        Object.__init__(self, position, radius=size * self.SIZE_TO_RADIUS)
        self.size = size
        self.direction = direction
        self.forward_thrust = 0
        self.rear_thrust = 0
        self.left_thrust = 0
        self.right_thrust = 0
        self.health = 1.0

    def _set_direction(self, direction):
        """Set the direction of the ship.

        The direction is given in angles.  It will be normalized so that
        0 <= direction < 360.

        The direction_vector attribute is also set.
        """
        direction = direction % 360
        if direction < 0: direction += 360
        self._direction = direction
        self.direction_vector = Vector.from_polar(direction)

    direction = property(lambda self: self._direction, _set_direction)

    def turn_left(self, how_much):
        """Tell the ship to turn left."""
        self.left_thrust += how_much

    def turn_right(self, how_much):
        """Tell the ship to turn right."""
        self.right_thrust += how_much

    def accelerate(self, how_much):
        """Tell the ship to accelerate in the direction of the ship."""
        self.forward_thrust += how_much

    def backwards(self, how_much):
        """Tell the ship to accelerate in the opposite direction."""
        self.rear_thrust += how_much

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
        Object.move(self, dt)
