from __future__ import annotations
import math
from typing import Generic, Tuple, TypeVar

from polynom import Polynom

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
        if isinstance(self.x, float):
            return math.atan2(self.y, self.x)
        else:
            raise ValueError("can only get angle of float")

    @staticmethod
    def from_angle(angle: float) -> Vec:
        return Vec(math.cos(angle), math.sin(angle))

    def __mul__(self, other) -> Vec:
        return Vec(other*self.x, other*self.y)

    def apply(self, v: float) -> Vec:
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
        return Vec(-self.y, self.x)