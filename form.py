from __future__ import annotations
import math
from typing import List, Optional, Tuple
import pygame
from angle import angle_distance, normalize_angle
from ball import Ball
from coll_direction import CollDirection
from collision import RotatedCollision
from interval import SimpleInterval
from material import Material
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
    def get_name(self) -> str:
        pass

    def find_collision(self, ball: Ball):
        #print("finding collision for abstract form")
        first_coll = None
        for path in self.paths:
            #print(f"checking path: {path}")
            coll = path.find_collision(ball)
            if coll is None:
                #print("no collision")
                continue

            if first_coll is None or coll.time < first_coll.time:
                first_coll = coll
                #print(f"new first collision: {first_coll}")
        return first_coll
    @abstractmethod
    def get_material(self) -> Material:
        pass

class StaticForm(Form):
    @abstractmethod
    def get_points(self) -> List[Vec[float]]:
        pass

    @abstractmethod
    def rotate(self, angle: float, center: Vec[float]) -> StaticForm:
        pass

    @abstractmethod
    def transform(self, transform: Vec[float]) -> StaticForm:
        pass


class CircleForm(StaticForm):
    pos: Vec
    radius: float
    min_angle: float
    max_angle: float
    name: str
    material: Material

    points: List[Tuple[float, float]]
    edges: List[Tuple[Vec, bool]]
    paths: List[Path]

    def __init__(self, pos: Vec, radius, material: Material, min_angle: float = 0, max_angle: float = 2*math.pi, resolution=100, ball_radius=50, name="circle"):

        self.pos = pos
        self.radius = radius
        self.min_angle = min_angle
        self.max_angle = max_angle
        self.points = []
        self.edges = []
        self.paths = []
        self.name = name
        self.material = material
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
            cap = CirclePath(cap_pos, ball_radius,self, angle_a, angle_b, CollDirection.ALLOW_FROM_OUTSIDE, "min_cap")
            self.paths.append(cap)
            # max cap:
            cap_pos = Vec(math.cos(max_angle)*radius + pos.x,
                          math.sin(max_angle)*radius + pos.y)
            angle_a = max_angle
            angle_b = max_angle + math.pi
            cap = CirclePath(cap_pos, ball_radius, self, angle_a, angle_b, CollDirection.ALLOW_FROM_OUTSIDE, "max_cap")
            self.paths.append(cap)

        step_size = (self.max_angle - self.min_angle)/resolution
        prev_x = None
        for i in range(resolution):
            # print(f"i: {i}")
            a_r = i*step_size + self.min_angle
            x = math.cos(a_r)*self.radius + self.pos.x
            y = math.sin(a_r)*self.radius + self.pos.y

            self.points.append((x, y))
        super().__init__(self.paths)

    def draw(self, screen, color, time: float):
        pygame.draw.lines(screen, color, False, self.points, width=3)
        for kante in self.paths:
            # pygame.draw.circle(screen, color, kante, 50)
            kante.draw(screen, color)

    def get_points(self):
        return map(lambda p: Vec(p[0], p[1]), self.points)
        # for kante in self.paths:
        # pygame.draw.circle(screen, color, kante, 50)
        #    kante.draw(screen, color)

    def get_name(self):
        return self.name

    def rotate(self, angle: float, center: Vec[float]) -> StaticForm:
        new_pos = self.pos.rotate(angle, center)
        return CircleForm(new_pos, self.radius, self.material, self.min_angle+angle, self.max_angle+angle, name=self.name)
    
    def transform(self, transform: Vec[float]) -> StaticForm:
        new_pos = self.pos + transform
        return CircleForm(new_pos, self.radius, self.material, self.min_angle, self.max_angle, name=self.name)
    def get_material(self) -> Material:
        return self.material


class LineForm(StaticForm):
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
        self.paths.append(LinePath(pos1+normal, pos2+normal, self, normal, CollDirection.ALLOW_FROM_OUTSIDE))
        self.paths.append(LinePath(pos1-normal, pos2-normal, self, normal*(-1), CollDirection.ALLOW_FROM_OUTSIDE))
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

    def get_points(self):
        return [self.pos1, self.pos2]

    def get_name(self):
        return self.name

    def rotate(self, angle: float, center: Vec[float]) -> StaticForm:
        new_pos1 = self.pos1.rotate(angle, center)
        new_pos2 = self.pos2.rotate(angle, center)
        return LineForm(new_pos1, new_pos2, self.ball_radius, self.material, self.name)
    def transform(self, transform: Vec[float]) -> StaticForm:
        new_pos1 = self.pos1 + transform
        new_pos2 = self.pos2 + transform
        return LineForm(new_pos1, new_pos2, self.ball_radius, self.material, self.name)
    def get_material(self) -> Material:
        return self.material


class RotateForm(Form):
    """
    Rotate a form around a point
    This is done by rotating the ball trajectory
    """
    form: StaticForm
    center: Vec[float]
    start_angle: float  # the point which the form is rotated around
    angle_speed: float
    start_time: float
    name: str

    def __init__(self, form: StaticForm, center: Vec[float], start_angle: float, angle_speed: float, start_time: float, name="rotateform"):
        self.form = form
        self.center = center
        self.start_angle = start_angle
        self.angle_speed = angle_speed
        self.start_time = start_time
        self.name = name

    def draw(self, screen: pygame.Surface, color, time: Optional[float] = None):
        if time is None:
            return
        angle = self.start_angle + self.angle_speed*(time-self.start_time)
        form_rotated = self.form.rotate(angle, self.center)
        form_rotated.draw(screen, color, time)
        return

    def find_collision(self, ball: Ball):
        # print(f"finding collision for rotateform, ball: {ball}")
        # rotate the ball trajectory
        t = Polynom([0, 1])
        # rotate the ball trajectory
        angle = (t-self.start_time+ball.start_t) * \
            (-self.angle_speed)-self.start_angle
        bahn = ball.bahn.rotate_poly(angle, self.center, 6)
        # calculate the collision
        coll = self.form.find_collision(ball.with_bahn(bahn))
        # print(f"found coll: {coll}")
        if coll is None:
            return None
        # calculate the objects angle at the time of collision
        angle = self.start_angle + self.angle_speed*coll.time
        return RotatedCollision(coll, -angle)  # , self.center)

    def get_name(self):
        return self.name
    def get_material(self) -> Material:
        return self.form.get_material()
class TransformForm(Form):
    """
    Transform a form by a function
    """
    form: StaticForm
    transform: Vec[Polynom]
    name: str

    def __init__(self, form: StaticForm, transform: Vec[Polynom], name="transformform"):
        self.form = form
        self.transform = transform
        self.name = name

    def draw(self, screen: pygame.Surface, color, time: Optional[float] = None):
        if time is None:
            return
        form_transformed = self.form.transform(self.transform.apply(time))
        form_transformed.draw(screen, color, time)
        return

    def find_collision(self, ball: Ball):
        # print(f"finding collision for rotateform, ball: {ball}")
        # rotate the ball trajectory
        t = Polynom([0, 1])
        # rotate the ball trajectory
        bahn = ball.bahn - self.transform.apply(t+ball.start_t)
        #print(f"bahn transformed: {bahn}, ball bahn: {ball.bahn}")
        # calculate the collision
        coll = self.form.find_collision(ball.with_bahn(bahn))
        # print(f"found coll: {coll}")
        if coll is None:
            return None
        # calculate the objects angle at the time of collision
        return coll

    def get_name(self):
        return self.name
    def get_material(self) -> Material:
        return self.form.get_material()


# A form that is a certain Form for a period of time and becomes another form afterwards
class TempForm(Form):
    start_form: Form
    form_duration: float
    end_form: Form
    name: str
    i = 0

    def __init__(self, start_form: Form, form_duration: float, end_form: Form, name="tempform"):
        self. start_form = start_form
        self.form_duration = form_duration
        self.end_form = end_form

    def draw(self, screen, color, time: float):
        if time is None:
            return
        if time < self.form_duration:
            # print("a")
            self.start_form.draw(screen, color, time)
        else:
            # print("b")
            self.end_form.draw(screen, color, time)

    def find_collision(self, ball: Ball, ignore: List[Path] = []):
        # if self.i > 3:
        #    return None
        self.i += 1
        # print(f"collision nr {self.i}, ball_start_t: {ball.start_t}:")
        if ball.start_t >= self.form_duration:
            # print("is already end")
            return self.end_form.find_collision(ball)

        coll_start = self.start_form.find_collision(ball)
        if coll_start is not None and coll_start.time + ball.start_t < self.form_duration:
            # print("collision in start form")
            return coll_start

        coll_end = self.end_form.find_collision(ball)
        if coll_end is None:
            pass
            # print("coll in end form is none")
        elif coll_end.time + ball.start_t >= self.form_duration:
            # print(f"collision in end form {coll_end.time + ball.start_t} >= {self.form_duration}")
            # raise ValueError("test")
            print("is end")
            return coll_end
        # else:
            # print(f"no collision in end form {coll_end.time + ball.start_t} < {self.form_duration}, coll: {coll_end.time}")
            # return coll_end
        # print("no collision")
        return None

    def get_name(self):
        return self.name
    def get_material(self) -> Material:
        return self.start_form.get_material()


class FormContainer(Form):
    form: Form
    name: str

    def __init__(self, form: Form, name="formcontainer"):
        self.form = form
        self.name = name

    def draw(self, screen, color, time: float):
        self.form.draw(screen, color, time)

    def find_collision(self, ball: Ball):
        return self.form.find_collision(ball)

    def get_name(self):
        return self.name

    def set(self, form: Form):
        self.form = form

class NoneForm(Form):
    def __init__(self):
        pass
    def draw(self, screen, color, time: float):
        pass
    def find_collision(self, ball: Ball, ignore: List[Path] = []):
        return None
    def get_name(self):
        return "noneform"

