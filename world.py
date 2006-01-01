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
            w.update(0.1)
            time.sleep(0.1)

    """

    def __init__(self):
        self.time = 0.0
        self.objects = []

    def add(self, obj):
        """Add a new object to the universe."""
        self.objects.append(obj)

    def remove(self, obj):
        """Remove an object from the universe."""
        self.objects.remove(obj)

    def update(self, dt):
        """Make time happen."""
        # Gravity: affects velocities, but not positions
        for massive_obj in self.objects:
            if not massive_obj.mass:
                continue
            for obj in self.objects:
                if obj is not massive_obj:
                    obj.gravitate(massive_obj, dt)
        # Movement: affects positions
        for obj in self.objects:
            obj.move(dt)
        # Collision detection
        for n, obj1 in enumerate(self.objects):
            for obj2 in self.objects[n+1:]:
                if self.collide(obj1, obj2):
                    obj1.collision(obj1)
                    obj2.collision(obj2)
        self.time += dt

    def collide(self, obj1, obj2):
        """Check whether two objects collide."""
        return False

