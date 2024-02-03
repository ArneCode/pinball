from __future__ import annotations
import copy
import math
from typing import Dict, List, Optional, Tuple
import pygame
from math_utils.angle import angle_distance, calc_angle_between, normalize_angle
from objects.ball import Ball
from collision.coll_direction import CollDirection
from collision.collision import RotatedCollision, TimedCollision
from math_utils.interval import SimpleInterval
from objects.material import Material
from objects.path import CirclePath, LinePath, Path
from math_utils.polynom import Polynom
from math_utils.vec import Vec
from abc import ABC, abstractmethod


class Form(ABC):
    paths: List[Path]

    def __init__(self, paths: List[Path]):
        self.paths = paths

    @abstractmethod
    def draw(self, screen, color, time: float):
        pass

    @abstractmethod
    def get_name(self) -> str:
        pass

    def find_collision(self, ball: Ball):
        # print("finding collision for abstract form")
        first_coll = None
        for path in self.paths:
            # print(f"checking path: {path}")
            coll = path.find_collision(ball)
            if coll is None:
                # print("no collision")
                continue

            if first_coll is None or coll.time < first_coll.time:
                first_coll = coll
                # print(f"new first collision: {first_coll}")
        return first_coll

    @abstractmethod
    def get_material(self) -> Material:
        pass

    @abstractmethod
    def get_points(self, t: float) -> List[Vec[float]]:
        pass

    @abstractmethod
    def rotate(self, angle: float, center: Vec[float]) -> Form:
        pass







# class FormContainer(Form):
#     form: Form
#     name: str

#     def __init__(self, form: Form, name="formcontainer"):
#         self.form = form
#         self.name = name

#     def draw(self, screen, color, time: float):
#         self.form.draw(screen, color, time)

#     def find_collision(self, ball: Ball):
#         return self.form.find_collision(ball)

#     def get_name(self):
#         return self.name

#     def set(self, form: Form):
#         self.form = form


# class NoneForm(Form):
#     def __init__(self):
#         pass

#     def draw(self, screen, color, time: float):
#         pass

#     def find_collision(self, ball: Ball, ignore: List[Path] = []):
#         return None

#     def get_name(self):
#         return "noneform"

