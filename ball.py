import copy
from typing import Tuple

import pygame

from vec import Vec
from polynom import Polynom


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
        self.bahn = Vec(0.0, 0.0)
        self.start_t = 0

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

    def with_start_t(self, start_t: float):
        new = copy.copy(self)
        new.start_t = start_t
        return new