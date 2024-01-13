import math
from typing import List, Optional
import pygame
from ball import Ball
from collision import RotatedCollision
from interval import SimpleInterval
from path import CirclePath, LinePath, Path
from polynom import Polynom
from vec import Vec
from abc import ABC, abstractmethod

class Form(ABC):
    paths: List[Path]
    def __init__(self, paths: List[Path]):
        self.paths = paths
    @abstractmethod
    def draw(self, screen, color, time: float):
        pass
    @abstractmethod
    def get_points(self) -> List[Vec[float]]:
        pass
    def find_collision(self, ball: Ball, ignore: List[Path] = []):
        first_coll = None
        for path in self.paths:
            if path in ignore:
                continue
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

    def draw(self, screen, color, time: float):
        pygame.draw.lines(screen, color, False, self.points, width=3)
        for kante in self.paths:
            # pygame.draw.circle(screen, color, kante, 50)
            kante.draw(screen, color)
    def get_points(self):
        return map(lambda p: Vec(p[0], p[1]),self.points)
        #for kante in self.paths:
            # pygame.draw.circle(screen, color, kante, 50)
        #    kante.draw(screen, color)

class LineForm(Form):
    pos1: Vec[float]
    pos2: Vec[float]
    paths: List[Path]
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
    def draw(self, screen, color, time: float):
        pygame.draw.line(screen, color, (self.pos1.x, self.pos1.y), (self.pos2.x, self.pos2.y), width=3)
    def get_points(self):
        return [self.pos1, self.pos2]
        #for path in self.paths:
            #path.draw(screen, color)
class RotateForm(Form):
    """
    Rotate a form around a point
    This is done by rotating the ball trajectory
    """
    form: Form
    center: Vec[float]
    start_angle: float # the point which the form is rotated around
    angle_speed: float
    time_interval: SimpleInterval
    def __init__(self, form: Form, center: Vec[float], start_angle: float, angle_speed: float, time_interval: SimpleInterval):
        self.form = form
        self.center = center
        self.start_angle = start_angle
        self.angle_speed = angle_speed
        self.time_interval = time_interval
    def draw(self, screen: pygame.Surface, color, time: Optional[float] = None):
        if time is None:
            return
        angle = self.start_angle + self.angle_speed*time
        
        pts = self.form.get_points()
        new_pts = map(lambda pt: pt.rotate(angle, self.center), pts)
        new_pts_tuple = list(map(lambda pt: (pt.x, pt.y), new_pts))
        pygame.draw.lines(screen, color, False, new_pts_tuple, width=3)
    def find_collision(self, ball: Ball, ignore: List[Path] = []):
        #print(f"finding collision for rotateform, ball: {ball}")
        # rotate the ball trajectory
        t = Polynom([0,1])
        # rotate the ball trajectory
        angle = (t+ball.start_t)*(-self.angle_speed)-self.start_angle
        bahn = ball.bahn.rotate_poly(angle, self.center, 6)
        #print(f"bahn: {bahn}")
        # calculate the collision
        coll = self.form.find_collision(ball.with_bahn(bahn), ignore)
        #print(f"found coll: {coll}")
        if coll is None:
            return None
        # calculate the objects angle at the time of collision
        angle = self.start_angle + self.angle_speed*coll.time
        return RotatedCollision(coll, -angle)#, self.center)
    def get_points(self):
        raise NotImplementedError("get_points not implemented for RotateForm")

# A form that is a certain Form for a period of time and becomes another form afterwards
class TempForm(Form):
    start_form: Form
    form_duration: float
    end_form: Form
    is_end: bool

    def __init__(self, start_form: Form, form_duration: float, end_form: Form):
        self. start_form = start_form
        self.form_duration = form_duration
        self.end_form = end_form
        self.is_end = False
    def draw(self, screen, color, time: float):
        if time is None:
            return
        if time < self.form_duration:
            print("a")
            self.start_form.draw(screen, color, time)
        else:
            #print("b")
            self.end_form.draw(screen, color, time)
    def find_collision(self, ball: Ball, ignore: List[Path] = []):
        if self.is_end:
            return self.end_form.find_collision(ball, ignore)
        
        
        coll = self.start_form.find_collision(ball, ignore)
        if coll is not None and coll.time + ball.start_t < self.form_duration:
            return coll
        
        coll = self.end_form.find_collision(ball, ignore)
        if coll is not None and coll.time + ball.start_t >= self.form_duration:
            self.is_end = True
            return coll
        return None
    
    def get_points(self):
        raise NotImplementedError("get_points not implemented for TempForm")

        
class FormHandler:
    forms: List[Form]
    def __init__(self):
        self.forms = []
    def add_form(self, form: Form):
        self.forms.append(form)
    def draw(self, screen, color, time: float):
        for form in self.forms:
            form.draw(screen, color, time)
    def find_collision(self, ball: Ball, ignore: List[Path] = []):
        first_coll = None
        for form in self.forms:
            coll = form.find_collision(ball, ignore)
            if coll is None:
                continue
            if first_coll is None or coll.time < first_coll.time:
                first_coll = coll
        return first_coll