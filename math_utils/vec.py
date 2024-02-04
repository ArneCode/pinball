from __future__ import annotations
import math
import numbers
from typing import Generic, Self, Tuple, TypeVar

from math_utils.polynom import Polynom
from math_utils.taylor import cos_taylor, sin_taylor

T = TypeVar("T")


class Vec(Generic[T]):
    """
    A 2D vector. The coordinates can be of any type, but it is assumed it has normal number operations defined.
    If T is a polynom, the vector can be thought of as a function of time.

    Attributes:
        - x (T): The x coordinate of the vector.
        - y (T): The y coordinate of the vector.

    Template Parameters:
        - T: The type of the coordinates of the vector.
    """
    x: T
    y: T

    def __init__(self, x: T, y: T) -> None:
        self.x = x
        self.y = y

    def __add__(self, other: Vec):
        x = self.x + other.x
        y = self.y + other.y
        return Vec(x, y)

    def __sub__(self, other: Vec):
        x = self.x - other.x
        y = self.y - other.y
        return Vec(x, y)

    # def __str__(self) -> str:
    #    return f"Vec({self.x}, {self.y})"

    def get_angle(self) -> float:
        """
        returns the angle of the vector in radians, between 0 and 2pi
        """
        if isinstance(self.x, float) and isinstance(self.y, float):
            angle = math.atan2(self.y, self.x)  # angle between -pi and pi
            if angle < 0:
                angle += 2*math.pi
            return angle  # angle between 0 and 2pi
        else:
            raise ValueError("can only get angle of float")

    @staticmethod
    def from_angle(angle: float) -> Vec:
        return Vec(math.cos(angle), math.sin(angle))

    def __mul__(self, other) -> Vec:
        """
        multiply the vector with a number. Don't do this with another vector, there is a seperate dot method for that
        """
        assert not isinstance(other, Vec)
        return Vec(other*self.x, other*self.y)

    def apply(self, v) -> Vec:
        """
        This can only be used if T is a polynom. It finds the vector at time v
        """
        if isinstance(self.x, Polynom) and isinstance(self.y, Polynom):
            return Vec(self.x.apply(v), self.y.apply(v))
        else:
            raise ValueError("can only apply to Polynom")

    def deriv(self) -> Vec[Polynom]:
        """
        This can only be used if T is a polynom. It finds the derivative of the vector, meaning the velocity vector over time
        """
        if isinstance(self.x, Polynom) and isinstance(self.y, Polynom):
            return Vec(self.x.deriv(), self.y.deriv())
        else:
            raise ValueError("can only derive polynom")

    def magnitude(self) -> float:
        """
        Only works if x and y are float or int. Returns the magnitude of the vector
        """
        # check if x and y are float or int
        assert (isinstance(self.x, float) or isinstance(self.x, int)) and (
            isinstance(self.y, float) or isinstance(self.y, int))
        return math.sqrt(self.x**2+self.y**2)

    def normalize(self) -> Vec[float]:
        """
        Only works if x and y are float or int. Returns the normalized vector
        """
        return self*(1/self.magnitude())

    def decompose(self, other: Vec) -> Tuple[Vec, Vec]:
        """
        Only works if T is Number. Decomposes self into the part that is parallel to other and the part that is perpendicular to other
        """
        proj = self.project(other)
        perp = self - proj
        return (proj, perp)

    def project(self, other: Vec) -> Vec:
        """
        project self onto other, meaning finding the part of self that is parallel to other
        """
        return other*(self.dot(other)/(other.magnitude()**2))

    def dot(self, other: Vec) -> float:
        """
        dot product of self and other
        """
        return self.x*other.x + self.y*other.y

    def orhtogonal(self) -> Vec:
        """
        returns the vector rotated by 90 degrees in mathematically positive direction
        """
        assert isinstance(self.x, float) and isinstance(self.y, float)
        return Vec(-self.y, self.x)

    def rotate(self, angle: float, center: Vec) -> Vec:
        """
        rotate self around center by angle "im Uhrzeigersinn"
        """
        this_offset = self-center
        this_offset_rot = Vec(this_offset.x*math.cos(angle) + this_offset.y*math.sin(angle),
                              -this_offset.x*math.sin(angle) + this_offset.y*math.cos(angle))
        return this_offset_rot + center

    def rotate_poly(self, angle: Polynom, center: Vec, taylor_approx: int) -> Vec:
        """
        rotate self around center by angle "im Uhrzeigersinn"
        """
        sin_poly = sin_taylor(taylor_approx)
        cos_poly = cos_taylor(taylor_approx)
        this_offset = self-center
        this_offset_rot = Vec(this_offset.x*cos_poly.apply(angle) + this_offset.y*sin_poly.apply(angle),
                              -this_offset.x*sin_poly.apply(angle) + this_offset.y*cos_poly.apply(angle))
        return this_offset_rot + center

    def __str__(self) -> str:
        return f"Vec({self.x}, {self.y})"

    def as_tuple(self) -> Tuple[T, T]:
        return (self.x, self.y)
