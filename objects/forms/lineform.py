from __future__ import annotations
import math
from typing import List

import pygame
from collision.coll_direction import CollDirection
from objects.form import Form
from objects.material import Material
from objects.path import Path, CirclePath, LinePath
from math_utils.vec import Vec


class LineForm(Form):
    pos1: Vec[float]
    pos2: Vec[float]
    ball_radius: float
    material: Material
    name: str
    paths: List[Path]

    def __init__(self, pos1: Vec[float], pos2: Vec[float], ball_radius: float, material: Material, name="line"):
        self.pos1 = pos1
        self.pos2 = pos2
        self.paths = []
#        this_path = LinePath(pos1, pos2, self, Vec(0,0))
        self.name = name
        self.ball_radius = ball_radius
        self.material = material
        # create two paths, one for each side of the line, parrallel to the line
        # with a distance of ball_radius
        normal = (pos2-pos1).normalize().orhtogonal()*ball_radius
        self.paths.append(LinePath(pos1+normal, pos2+normal,
                          self, normal, CollDirection.ALLOW_FROM_OUTSIDE))
        self.paths.append(LinePath(pos1-normal, pos2-normal,
                          self, normal*(-1), CollDirection.ALLOW_FROM_OUTSIDE))
        # calculate angle of line
        angle = math.atan2(pos2.y-pos1.y, pos2.x-pos1.x)
        # append circles at the ends of the line
        self.paths.append(CirclePath(pos1, ball_radius, self,
                          angle+math.pi/2, angle-math.pi/2, CollDirection.ALLOW_FROM_OUTSIDE))
        self.paths.append(CirclePath(pos2, ball_radius, self,
                          angle-math.pi/2, angle+math.pi/2, CollDirection.ALLOW_FROM_OUTSIDE))
        super().__init__(self.paths)

    def draw(self, screen, color, time: float):
        pygame.draw.line(screen, color, (self.pos1.x, self.pos1.y),
                         (self.pos2.x, self.pos2.y), width=3)
        for path in self.paths:
            path.draw(screen, color)

    def get_points(self, t):
        return [self.pos1, self.pos2]

    def get_name(self):
        return self.name

    def rotate(self, angle: float, center: Vec[float]) -> LineForm:
        new_pos1 = self.pos1.rotate(angle, center)
        new_pos2 = self.pos2.rotate(angle, center)
        return LineForm(new_pos1, new_pos2, self.ball_radius, self.material, self.name)

    # def transform(self, transform: Vec[float]) -> StaticForm:
    #     new_pos1 = self.pos1 + transform
    #     new_pos2 = self.pos2 + transform
    #     return LineForm(new_pos1, new_pos2, self.ball_radius, self.material, self.name)

    def get_material(self) -> Material:
        return self.material