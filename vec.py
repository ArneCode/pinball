from __future__ import annotations
import math
import numbers
from typing import Generic, Self, Tuple, TypeVar

from polynom import Polynom
from taylor import cos_taylor, sin_taylor

T = TypeVar("T")


class Vec(Generic[T]):
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

    def __str__(self) -> str:
        return f"Vec({self.x}, {self.y})"

    def get_angle(self) -> float:
        """
        returns the angle of the vector in radians, between 0 and 2pi
        """
        if isinstance(self.x, float) and isinstance(self.y, float):
            angle =  math.atan2(self.y, self.x) # angle between -pi and pi
            if angle < 0:
                angle += 2*math.pi
            return angle # angle between 0 and 2pi
        else:
            raise ValueError("can only get angle of float")

    @staticmethod
    def from_angle(angle: float) -> Vec:
        return Vec(math.cos(angle), math.sin(angle))

    def __mul__(self, other) -> Vec:
        # if the other is number:
        #if isinstance(other, numbers.Number):
        #    return Vec(self.x*other, self.y*other)
        return Vec(other*self.x, other*self.y)

    def apply(self, v) -> Vec:
        if isinstance(self.x, Polynom) and isinstance(self.y, Polynom):
            return Vec(self.x.apply(v), self.y.apply(v))
        else:
            raise ValueError("can only apply to Polynom")

    def deriv(self) -> Vec:
        if isinstance(self.x, Polynom) and isinstance(self.y, Polynom):
            return Vec(self.x.deriv(), self.y.deriv())
        else:
            raise ValueError("can only derive polynom")

    def magnitude(self) -> float:
        # check if x and y are float or int
        assert (isinstance(self.x, float) or isinstance(self.x, int)) and (
            isinstance(self.y, float) or isinstance(self.y, int))
        return math.sqrt(self.x**2+self.y**2)

    def normalize(self) -> Vec:
        return self*(1/self.magnitude())
    def decompose(self, other: Vec) -> Tuple[Vec, Vec]:
        """
        decompose self into the part that is parallel to other and the part that is perpendicular to other
        """
        proj = self.project(other)
        perp = self - proj
        return (proj, perp)
    def project(self, other: Vec) -> Vec:
        """
        project self onto other
        """
        return other*(self.dot(other)/(other.magnitude()**2))
    def dot(self, other: Vec) -> float:
        return self.x*other.x + self.y*other.y
    def orhtogonal(self) -> Vec:
        assert isinstance(self.x, float) and isinstance(self.y, float)
        return Vec(-self.y, self.x)
    def rotate(self, angle: float, center: Vec) -> Vec:
        """
        rotate self around center by angle
        """
        this_offset = self-center
        this_offset_rot = Vec(this_offset.x*math.cos(angle) + this_offset.y*math.sin(angle), -this_offset.x*math.sin(angle) + this_offset.y*math.cos(angle))
        return this_offset_rot + center
    def rotate_poly(self, angle: Polynom, center: Vec, taylor_approx: int) -> Vec:
        """
        rotate self around center by angle
        """
        sin_poly = sin_taylor(taylor_approx)
        cos_poly = cos_taylor(taylor_approx)
        this_offset = self-center
        this_offset_rot = Vec(this_offset.x*cos_poly.apply(angle) + this_offset.y*sin_poly.apply(angle), 
                              -this_offset.x*sin_poly.apply(angle) + this_offset.y*cos_poly.apply(angle))
        return this_offset_rot + center