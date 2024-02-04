from __future__ import annotations
import math
from typing import List, Tuple

import pygame
from collision.coll_direction import CollDirection
from math_utils.angle import angle_distance
from objects.material import Material
from objects.form import Form
from objects.path import Path, CirclePath
from math_utils.vec import Vec

class CircleForm(Form):
    """
    A circle in the game.

    Attributes:
        - pos (Vec): The position of the circle.
        - radius (float): The radius of the circle.
        - min_angle (float): The minimum angle of the circle.
        - max_angle (float): The maximum angle of the circle.
        - name (str): The name of the circle.
        - material (Material): The material of the circle.
        - points (List[Tuple[float, float]]): The points of the circle. Used for drawing.
        - edges (List[Tuple[Vec, bool]]): The edges of the circle.
        - paths (List[Path]): The paths of the circle.
        - color (Tuple[float, float, float]): The color of the circle.
    """
    pos: Vec
    radius: float
    min_angle: float
    max_angle: float
    name: str
    material: Material

    points: List[Tuple[float, float]]
    edges: List[Tuple[Vec, bool]]
    paths: List[Path]
    color: Tuple[float, float, float]

    def __init__(self, pos: Vec, radius, material: Material, color: Tuple, min_angle: float = 0, max_angle: float = 2*math.pi, resolution=100, ball_radius=50, name="circle"):
        """
        Initialize the CircleForm.

        Args:
            - pos: The position of the circle.
            - radius: The radius of the circle.
            - min_angle: The minimum angle of the circle.
            - max_angle: The maximum angle of the circle.
            - name: The name of the circle.
            - material: The material of the circle.
            - color: The color of the circle.
            - resolution: The number of points to use for drawing the circle.
            - ball_radius: The radius of the ball.
        """
        self.pos = pos
        self.radius = radius
        self.min_angle = min_angle
        self.max_angle = max_angle
        self.points = []
        self.edges = []
        self.paths = []
        self.name = name
        self.material = material
        self.color = color
        # edge_angles = []

        # überprüfe, ob der kreis geschlossen ist
        closed = math.isclose(angle_distance(
            self.min_angle, self.max_angle), 0.0, abs_tol=0.001)
        if closed:
            outer_circle = CirclePath(
                pos, radius + ball_radius, self, min_angle, max_angle, CollDirection.ALLOW_FROM_OUTSIDE, "outer_circle")
            self.paths.append(outer_circle)
        else:
            outer_circle = CirclePath(
                pos, radius + ball_radius, self, min_angle, max_angle, CollDirection.ALLOW_FROM_OUTSIDE, "outer_circle")
            inner_circle = CirclePath(
                pos, radius - ball_radius, self, min_angle, max_angle, CollDirection.ALLOW_FROM_INSIDE, "inner_circle")
            self.paths.append(outer_circle)
            self.paths.append(inner_circle)

            # make caps to close the circle
            # min cap:
            cap_pos = Vec(math.cos(min_angle)*radius + pos.x,
                          math.sin(min_angle)*radius + pos.y)
            angle_a = min_angle - math.pi
            angle_b = min_angle
            cap = CirclePath(cap_pos, ball_radius, self, angle_a,
                             angle_b, CollDirection.ALLOW_FROM_OUTSIDE, "min_cap")
            self.paths.append(cap)
            # max cap:
            cap_pos = Vec(math.cos(max_angle)*radius + pos.x,
                          math.sin(max_angle)*radius + pos.y)
            angle_a = max_angle
            angle_b = max_angle + math.pi
            cap = CirclePath(cap_pos, ball_radius, self, angle_a,
                             angle_b, CollDirection.ALLOW_FROM_OUTSIDE, "max_cap")
            self.paths.append(cap)

        step_size = (self.max_angle - self.min_angle)/resolution
        for i in range(resolution):
            a_r = i*step_size + self.min_angle
            x = math.cos(a_r)*self.radius + self.pos.x
            y = math.sin(a_r)*self.radius + self.pos.y

            self.points.append((x, y))
        # giving the paths to the Form class so that it can handle collisions
        super().__init__(self.paths)

    def draw(self, screen, color, time: float):
        pygame.draw.lines(screen, color, False, self.points, width=3)
        for kante in self.paths:
            # pygame.draw.circle(screen, color, kante, 50)
            kante.draw(screen, color)

    def get_points(self, t):
        return map(lambda p: Vec(p[0], p[1]), self.points)
        # for kante in self.paths:
        # pygame.draw.circle(screen, color, kante, 50)
        #    kante.draw(screen, color)

    def get_name(self):
        return self.name

    def rotate(self, angle: float, center: Vec[float]) -> CircleForm:
        angle = -angle
        new_pos = self.pos.rotate(angle, center)
        return CircleForm(new_pos, self.radius, self.material, self.color, self.min_angle+angle, self.max_angle+angle, name=self.name)

    def get_material(self) -> Material:
        return self.material