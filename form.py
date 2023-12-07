import math
from typing import List
import pygame
from ball import Ball
from interval import SimpleInterval
from path import CirclePath, LinePath, Path
from vec import Vec
from abc import ABC, abstractmethod

class Form(ABC):
    paths: List[Path]
    def __init__(self, paths: List[Path]):
        self.paths = paths
    @abstractmethod
    def draw(self, screen, color):
        pass
    def find_collision(self, ball: Ball):
        first_coll = None
        for path in self.paths:
            coll = path.find_collision(ball)
            if coll is None:
                continue
            if first_coll is None or coll.time < first_coll.time:
                first_coll = coll
        return first_coll


class CircleForm(Form):
    def __init__(self, pos: Vec, radius, x_range: SimpleInterval, y_range: SimpleInterval, resolution=100, ball_radius=50):
        self.pos = pos
        self.radius = radius
        self.x_range = x_range
        self.y_range = y_range
        self.points = []
        self.edges = []
        edge_angles = []
        prev_included = False
        step_size = 2*math.pi/resolution
        for i in range(resolution):
            # print(f"i: {i}")
            a_r = i*step_size
            x = math.cos(a_r)*self.radius + self.pos.x
            y = math.sin(a_r)*self.radius + self.pos.y
            if x_range.check(x) and y_range.check(y):
                self.points.append((x, y))
                if not prev_included:
                    self.edges.append(Vec(x, y))
                    edge_angles.append(a_r)
                    prev_included = True
            elif prev_included:
                prev_point = self.points[-1]
                self.edges.append(Vec(prev_point[0], prev_point[1]))
                edge_angles.append(a_r - step_size)
                prev_included = False
        if len(edge_angles) % 2 == 1:
            raise ValueError("Weird number of kanten")
        self.paths = []
        for i in range(len(edge_angles)//2):
            a_1 = edge_angles[i*2]
            a_2 = edge_angles[i*2+1]
            rsmall = self.radius - ball_radius
            rlarge = self.radius + ball_radius
            x_range_small = SimpleInterval(math.cos(a_1)*rsmall +
                                           self.pos.x, math.cos(a_2)*rsmall+self.pos.x)
            x_range_large = SimpleInterval(math.cos(a_1)*rlarge +
                                           self.pos.x, math.cos(a_2)*rlarge+self.pos.x)
            self.paths.append(CirclePath(self.pos, rsmall,
                              x_range_small, self.y_range, "large_inner"))
            self.paths.append(CirclePath(self.pos, rlarge,
                              x_range_large, self.y_range, "large_outer"))
        for edge in self.edges:
            kante_x_range = SimpleInterval(
                edge.x-ball_radius, edge.x+ball_radius)
            kante_y_range = SimpleInterval(
                edge.y-ball_radius, edge.y+ball_radius)
            self.paths.append(CirclePath(
                edge, ball_radius, kante_x_range, kante_y_range, "kant"))
            super().__init__(self.paths)

    def draw(self, screen, color):
        pygame.draw.lines(screen, color, False, self.points, width=3)
        #for kante in self.paths:
            # pygame.draw.circle(screen, color, kante, 50)
        #    kante.draw(screen, color)

class LineForm(Form):
    pos1: Vec[float]
    pos2: Vec[float]
    paths: List[LinePath]
    def __init__(self, pos1: Vec[float], pos2: Vec[float], ball_radius: float):
        self.pos1 = pos1
        self.pos2 = pos2
        self.paths = []
        this_path = LinePath(pos1, pos2)
        # create two paths, one for each side of the line, parrallel to the line
        # with a distance of ball_radius
        normal = this_path.get_normal(pos1)*ball_radius
        self.paths.append(LinePath(pos1+normal, pos2+normal))
        self.paths.append(LinePath(pos1-normal, pos2-normal))
        # append circles at the ends of the line
        self.paths.append(CirclePath(pos1, ball_radius))
        self.paths.append(CirclePath(pos2, ball_radius))
        super().__init__(self.paths)
    def draw(self, screen, color):
        pygame.draw.line(screen, color, (self.pos1.x, self.pos1.y), (self.pos2.x, self.pos2.y), width=3)
        #for path in self.paths:
            #path.draw(screen, color)
class FormHandler:
    forms: List[Form]
    def __init__(self):
        self.forms = []
    def add_form(self, form: Form):
        self.forms.append(form)
    def draw(self, screen, color):
        for form in self.forms:
            form.draw(screen, color)
    def find_collision(self, ball: Ball):
        first_coll = None
        for form in self.forms:
            coll = form.find_collision(ball)
            if coll is None:
                continue
            if first_coll is None or coll.time < first_coll.time:
                first_coll = coll
        return first_coll