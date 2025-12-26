import math
from typing import List, Tuple
import pygame
from objects.ball import Ball
from collision.coll_direction import CollDirection
from collision.collision import Collision, SimpleCollision
from math_utils.interval import Interval, SimpleInterval
from objects.material import Material

from math_utils.polynom import Polynom
from math_utils.vec import Vec
from abc import ABC, abstractmethod

from math_utils.angle import check_angle_between


class Path(ABC):
    @abstractmethod
    def get_normal(self, pos: Vec) -> Vec:
        """
        Returns the normal vector at the given position on the path.

        Parameters:
        - pos: A Vec object representing the position on the path.

        Returns:
        - The normal vector at the given position.
        """
        pass

    @abstractmethod
    def find_collision(self, ball: Ball) -> Collision | None:
        """
        Returns the collision with the ball or None if there is no collision
        """
        pass

    @abstractmethod
    def find_all_collision_times(self, bahn: Vec[Polynom]) -> List[float]:
        """
        Returns all collisions with the ball or an empty list if there is no collision
        """
        pass

    @abstractmethod
    def get_rotated(self, angle: float, center: Vec):
        pass

    @abstractmethod
    def draw(self, screen, color):
        pass

    @abstractmethod
    def get_form(self) -> "StaticForm":
        pass
    # @abstractmethod

    def get_material(self) -> Material:
        return self.get_form().get_material()


class CirclePath(Path):
    """
    Represents a circle the center of the ball can collide with
    
    Attributes:
        pos (Vec): the center of the circle
        radius (float): the radius of the circle
        points (List[Tuple[float, float]]): the points of the circle
        name (str): the name of the circle
        bound (BoundingBox): the bounding box of the circle
        min_angle (float): the minimum angle of the circle
        max_angle (float): the maximum angle of the circle
        """
    pos: Vec
    radius: float
    points: List[Tuple[float, float]]
    name: str
    # bound: BoundingBox
    min_angle: float
    max_angle: float

    collision_direction: CollDirection

    def __init__(self, pos: Vec, radius, form, min_angle: float = 0, max_angle: float = 2*math.pi, coll_direction: CollDirection = CollDirection.ALLOW_ALL, name=""):
        """
        Constructor for CirclePath
        
        Args:
            pos (Vec): the center of the circle
            radius (float): the radius of the circle
            min_angle (float): the minimum angle of the circle
            max_angle (float): the maximum angle of the circle"""
        while max_angle <= min_angle:
            max_angle += 2*math.pi
        self.pos = pos
        self.radius = radius
        self.points = []
        self.name = name
        self.min_angle = min_angle
        self.max_angle = max_angle
        self.form = form
        self.collision_direction = coll_direction

        # if x_range is None:
        #    x_range = SimpleInterval(pos.x-radius, pos.x+radius)
        # if y_range is None:
        #    y_range = SimpleInterval(pos.y-radius, pos.y+radius)
        # self.bound = BoundingBox(x_range, y_range)

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

    def check_coll_angle(self, pos: Vec) -> bool:
        """
        Check wether the given position is inside the angle range of the circle
        """
        angle = (pos-self.pos).get_angle()

        return check_angle_between(angle, self.min_angle, self.max_angle)

    def check_coll_direction(self, coll_pos: Vec, in_vec: Vec) -> bool:
        """
        Check wether the given direction is allowed for a collision at the given position
        """
        vec_from_center = coll_pos - self.pos
        dot = vec_from_center.dot(in_vec)
        if self.collision_direction == CollDirection.ALLOW_ALL:
            return True
        elif self.collision_direction == CollDirection.ALLOW_FROM_INSIDE:
            return dot > 0
        elif self.collision_direction == CollDirection.ALLOW_FROM_OUTSIDE:
            return dot < 0

    def check_coll(self, coll_t: float, bahn: Vec) -> bool:
        """
        Check wether a collision at the given time is valid
        """
        coll_pos = bahn.apply(coll_t)
        ball_vel = bahn.deriv().apply(coll_t)
        return self.check_coll_angle(coll_pos) and self.check_coll_direction(coll_pos, ball_vel)

    def find_collision(self, ball: Ball) -> Collision | None:
        """
        Returns the collision with the center of the ball or None if there is no collision
        """
        # TODO: restrict searched t by already found!
        # t_range: Interval | None = self.bound.times_inside(ball)
        check_eq: Polynom = ((ball.bahn.x-self.pos.x)**2 +
                             (ball.bahn.y-self.pos.y)**2 - (self.radius)**2)
        coll = check_eq.find_roots(
            filter_fn=lambda t: self.check_coll(t, ball.bahn))
        if len(coll) > 0:
            return SimpleCollision(coll[0], ball.bahn, self)
        return None

    def find_all_collision_times(self, bahn: Vec[Polynom]) -> List[float]:
        """
        Returns all collisions with the center of the ball or an empty list if there is no collision
        """
        check_eq: Polynom = ((bahn.x-self.pos.x)**2 +
                             (bahn.y-self.pos.y)**2 - (self.radius)**2)
        colls = check_eq.find_roots(
            filter_fn=lambda t: self.check_coll(t, bahn))
        return colls

    def get_rotated(self, angle: float, center: Vec):
        new_pos = self.pos.rotate(angle, center)
        return CirclePath(new_pos, self.radius, self.form, self.min_angle+angle, self.max_angle+angle, self.collision_direction, self.name)

    def __str__(self):
        return f"CirclePath(name: {self.name})"

    def get_form(self):
        return self.form


class LinePath(Path):
    """
    Represents a line the center of the ball can collide with

    Attributes:
        pos1 (Vec): the first point of the line
        pos2 (Vec): the second point of the line
        tangent (Vec): the tangent of the line
        eq_x (Polynom): the equation of the line in x
        eq_y (Polynom): the equation of the line in y
        x_range (Interval): the range of x values in which the line is defined
        y_range (Interval): the range of y values in which the line is defined
    """
    pos1: Vec
    pos2: Vec
    normal: Vec
    eq_x: Polynom
    eq_y: Polynom
    x_range: Interval
    y_range: Interval

    collision_direction: CollDirection

    def __init__(self, pos1: Vec, pos2: Vec, form, normal: Vec, collision_direction: CollDirection = CollDirection.ALLOW_ALL):
        """
        Constructor for LinePath
        Args:
            pos1 (Vec): the first point of the line
            pos2 (Vec): the second point of the line
        """
        self.pos1 = pos1
        self.pos2 = pos2
        self.form = form
        self.collision_direction = collision_direction
        self.normal = normal
        self.tangent = (pos2-pos1).normalize()
        self.x_range = SimpleInterval(min(pos1.x, pos2.x), max(pos1.x, pos2.x))
        self.y_range = SimpleInterval(min(pos1.y, pos2.y), max(pos1.y, pos2.y))
        if math.isclose(self.tangent.y, 0.0, rel_tol=1e-5):
            self.y_range = SimpleInterval(pos1.y - 5, pos1.y + 5)
        if math.isclose(self.tangent.x, 0.0, rel_tol=1e-5):
            self.x_range = SimpleInterval(pos1.x - 5, pos1.x + 5)
            y = Polynom([0, 1])
            self.eq_x = y*0 + pos1.x
            self.eq_y = y
        else:
            x = Polynom([0, 1])
            self.eq_x = x
            steep = self.tangent.y/self.tangent.x
            self.eq_y = (x-pos1.x)*steep+pos1.y

    def get_normal(self, pos: Vec) -> Vec:
        """
        Returns the normal vector of the line at the given position

        Args:
            pos (Vec): the position, unused because the normal of a line is always the same
        """
        return self.tangent.orhtogonal().normalize()

    def draw(self, screen, color):
        """
        Draws the line on the screen, used for debugging
        """
        pygame.draw.line(screen, color, (self.pos1.x, self.pos1.y),
                         (self.pos2.x, self.pos2.y), width=1)

    def check_coll_direction(self, coll_pos: Vec, in_vec: Vec) -> bool:
        dot = self.normal.dot(in_vec)
        if self.collision_direction == CollDirection.ALLOW_ALL:
            return True
        elif self.collision_direction == CollDirection.ALLOW_FROM_INSIDE:
            return dot > 0
        elif self.collision_direction == CollDirection.ALLOW_FROM_OUTSIDE:
            return dot < 0

    def check_coll_pos(self, coll_pos: Vec) -> bool:
        return self.x_range.check(coll_pos.x) and self.y_range.check(coll_pos.y)

    def check_coll(self, coll_t: float, bahn: Vec) -> bool:
        coll_pos = bahn.apply(coll_t)
        ball_vel = bahn.deriv().apply(coll_t)
        return self.check_coll_direction(coll_pos, ball_vel) and self.check_coll_pos(coll_pos)

    def find_collision(self, ball: Ball) -> Collision | None:
        """
        Returns the collision with the center of the ball or None if there is no collision

        Args:
            ball (Ball): the ball to check for collision

        Returns:
            Collision | None: the collision or None if there is no collision
        """

        coll_eq: Polynom = self.eq_x.apply(
            ball.bahn.y) - self.eq_y.apply(ball.bahn.x)
        colls = coll_eq.find_roots(
            filter_fn=lambda t: self.check_coll(t, ball.bahn))

        if len(colls) > 0:
            return SimpleCollision(colls[0], ball.bahn, self)
        return None

    def find_all_collision_times(self, bahn: Vec[Polynom]) -> List[float]:
        """
        Returns all collisions with the center of the ball or an empty list if there is no collision

        Args:
            ball (Ball): the ball to check for collision

        Returns:
            List[Collision]: the collisions or an empty list if there is no collision
        """

        coll_eq: Polynom = self.eq_x.apply(bahn.y) - self.eq_y.apply(bahn.x)
        colls = coll_eq.find_roots(
            filter_fn=lambda t: self.check_coll(t, bahn))

        return colls

    def get_rotated(self, angle: float, center: Vec):
        """
        Returns a rotated version of this line

        Args:
            angle (float): the angle to rotate
            center (Vec): the center of rotation
        """
        return LinePath(self.pos1.rotate(angle, center), self.pos2.rotate(angle, center), self.form, self.normal.rotate(angle, center), self.collision_direction)

    def get_form(self):
        return self.form
