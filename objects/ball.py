import copy
from typing import Tuple

import pygame
# from form import CircleForm#, TransformForm

from math_utils.vec import Vec
from math_utils.polynom import Polynom


class Ball:
    pos_0: Vec[float]
    bahn: Vec[Polynom]
    radius: float
    color: Tuple[int]
    start_t: float

    def __init__(self, pos, radius, color):
        self.pos_0 = pos
        self.radius = radius
        self.color = color
        self.vel_0 = Vec(0.0, 0.0)
        self.acc = Vec(0.0, 0.0)
        self.start_t = 0
        self.update_bahn()

    def get_pos(self, t: float) -> Vec:
        return self.bahn.apply(t-self.start_t)

    def draw(self, t, screen):
        pos = self.get_pos(t)
        pygame.draw.circle(screen, self.color,
                           (pos.x, pos.y), self.radius)

    def update_bahn(self):
        t = Polynom([0, 1])
        self.bahn = self.acc*0.5*(t**2)+self.vel_0*t+self.pos_0

    def with_acc(self, acc: Vec):
        new = copy.copy(self)
        new.acc = acc
        new.update_bahn()
        return new

    def with_vel(self, vel: Vec):
        new = copy.copy(self)
        new.vel_0 = vel
        new.update_bahn()
        return new

    def with_start_pos(self, pos: Vec):
        new = copy.copy(self)
        new.pos_0 = pos
        new.update_bahn()
        return new

    def with_bahn(self, bahn: Vec[Polynom]):
        new = copy.copy(self)
        new.bahn = bahn
        return new

    def with_start_t(self, start_t: float):
        new = copy.copy(self)
        new.start_t = start_t
        return new

    def from_time(self, t: float):
        rel_t = t-self.start_t
        new_pos = self.get_pos(t)
        new_vel = self.bahn.deriv().apply(rel_t)
        print(f"new_pos: {new_pos}, new_vel: {new_vel}, rel_t: {rel_t}")
        return self.with_start_t(t).with_start_pos(new_pos).with_vel(new_vel)

    def get_form(self):
        from objects.material import Material
        from objects.forms.circleform import CircleForm
        from objects.forms.transformform import TransformForm
        
        circle = CircleForm(Vec(0, 0), self.radius, material=Material(
            0.8, 0.95, 20, 1), color=self.color)
        t = Polynom([0, 1])
        x = self.bahn.x.apply(t-self.start_t)
        y = self.bahn.y.apply(t-self.start_t)
        bahn = Vec(x, y)
        moving_circle = TransformForm(circle, bahn)
        return moving_circle

    def __str__(self) -> str:
        return f"Ball(pos_0={self.pos_0}, bahn={self.bahn}, radius={self.radius}, color={self.color}, start_t={self.start_t})"
