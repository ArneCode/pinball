import math
from typing import List, Tuple
import pygame
from ball import Ball
from bounding_box import BoundingBox
from collision import Collision
from interval import Interval, SimpleInterval

from polynom import Polynom
from vec import Vec
from abc import ABC, abstractmethod

from angle import angle_between

class Path(ABC):
    @abstractmethod
    def get_normal(self, pos: Vec) -> Vec:
        pass
    @abstractmethod
    def find_collision(self, ball: Ball) -> Collision | None:
        pass
    @abstractmethod
    def get_rotated(self, angle: float, center: Vec):
        pass
    @abstractmethod
    def draw(self, screen, color):
        pass

class CirclePath(Path):
    pos: Vec
    radius: float
    points: List[Tuple[float, float]]
    name: str
    #bound: BoundingBox
    min_angle: float
    max_angle: float

    def __init__(self, pos: Vec, radius, min_angle: float = 0, max_angle: float = 2*math.pi, name=""):
        while max_angle <= min_angle:
            max_angle += 2*math.pi
        self.pos = pos
        self.radius = radius
        self.points = []
        self.name = name
        self.min_angle = min_angle
        self.max_angle = max_angle

        #if x_range is None:
        #    x_range = SimpleInterval(pos.x-radius, pos.x+radius)
        #if y_range is None:
        #    y_range = SimpleInterval(pos.y-radius, pos.y+radius)
        #self.bound = BoundingBox(x_range, y_range)

        resolution = 1000
        step_size = (self.max_angle - self.min_angle)/resolution

        for i in range(resolution):
            a_r = i*step_size + self.min_angle
            x = math.cos(a_r)*radius + pos.x
            y = math.sin(a_r)*radius + pos.y
            self.points.append((x, y))

    def get_normal(self, pos: Vec) -> Vec:
        steep = -(pos.x - self.pos.x)/(pos.y-self.pos.y)
        m = -1/steep
        return Vec(1, m).normalize()
    def get_tangent(self, pos: Vec) -> Vec:
        steep = -(pos.x - self.pos.x)/(pos.y-self.pos.y)
        return Vec(1, steep).normalize()

    def draw(self, screen, color):
        pygame.draw.lines(screen, color, False, self.points, width=1)
        if False:
            self.bound.draw(screen, color)
    def check_vec_angle(self, pos: Vec) -> bool:
        angle = (pos-self.pos).get_angle()
        return angle_between(angle, self.min_angle, self.max_angle)
    def find_collision(self, ball: Ball) -> Collision | None:
        # TODO: restrict searched t by already found!
        #t_range: Interval | None = self.bound.times_inside(ball)
        check_eq: Polynom = ((ball.bahn.x-self.pos.x)**2 +
                    (ball.bahn.y-self.pos.y)**2 - (self.radius)**2)
        t_range = SimpleInterval(0, 100)
        coll = check_eq.find_roots(
            t_range, return_smallest=True, do_numeric=True, filter_fn=lambda t: self.check_vec_angle(ball.bahn.apply(t)))
        if len(coll) > 0:
            return Collision(coll[0], ball.bahn, self)
        return None
    def get_rotated(self, angle: float, center: Vec):
        return CirclePath(self.pos.rotate(angle, center), self.radius, name=self.name)
    def __str__(self):
        return f"CirclePath(name: {self.name})"
class LinePath(Path):
    pos1: Vec
    pos2: Vec

    def __init__(self, pos1: Vec, pos2: Vec):
        self.pos1 = pos1
        self.pos2 = pos2
        self.tangent = (pos2-pos1).normalize()
        self.x_range = SimpleInterval(min(pos1.x, pos2.x), max(pos1.x, pos2.x))
        self.y_range = SimpleInterval(min(pos1.y, pos2.y), max(pos1.y, pos2.y))
        if math.isclose(self.tangent.y, 0.0, rel_tol=1e-5):
            self.y_range = SimpleInterval(pos1.y - 5, pos1.y + 5)
        if math.isclose(self.tangent.x, 0.0, rel_tol=1e-5):
            self.x_range = SimpleInterval(pos1.x - 5, pos1.x + 5)
            y = Polynom([0,1])
            self.eq_x = y*0 + pos1.x
            self.eq_y = y
        else:
            x = Polynom([0,1])
            self.eq_x = x
            steep = self.tangent.y/self.tangent.x
            self.eq_y = (x-pos1.x)*steep+pos1.y
    def get_normal(self, pos: Vec) -> Vec:
        return self.tangent.orhtogonal().normalize()
    def draw(self, screen, color):
        pygame.draw.line(screen, color, (self.pos1.x, self.pos1.y), (self.pos2.x, self.pos2.y), width=1)

    def find_collision(self, ball: Ball, interval: Interval = SimpleInterval(0.0, 100)) -> Collision | None:
        coll_eq: Polynom = self.eq_x.apply(ball.bahn.y) - self.eq_y.apply(ball.bahn.x)
        colls = coll_eq.find_roots(interval,return_smallest=False, do_numeric=True)
        
        min_t = float("inf")
        for coll in colls:
            if self.x_range.check(ball.bahn.x.apply(coll)) and self.y_range.check(ball.bahn.y.apply(coll)):
                min_t = min(min_t, coll)
            else:
                pass
                #print(f"not in range: {ball.bahn.apply(coll)}")
        if min_t == float("inf"):
            return None
        return Collision(min_t, ball.bahn, self)
    def get_rotated(self, angle: float, center: Vec):
        return LinePath(self.pos1.rotate(angle, center), self.pos2.rotate(angle, center))