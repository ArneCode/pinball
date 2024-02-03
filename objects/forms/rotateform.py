from __future__ import annotations
import math
from typing import List, Optional
import pygame
from collision.collision import RotatedCollision
from math_utils.polynom import Polynom
from objects.ball import Ball
from objects.form import Form
from objects.material import Material
from math_utils.vec import Vec

class RotateForm(Form):
    """
    Rotate a form around a point
    This is done by rotating the ball trajectory
    """
    form: Form
    center: Vec[float]
    start_angle: float  # the point which the form is rotated around
    angle_speed: float
    start_time: float
    name: str

    def __init__(self, form: Form, center: Vec[float], start_angle: float, angle_speed: float, start_time: float, name="rotateform"):
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
        pts = self.form.get_points(time)
        pts_rotated = list(map(lambda p: p.rotate(
            angle, self.center).as_tuple(), pts))
        pygame.draw.lines(screen, color, False, pts_rotated, width=3)
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

    def get_points(self, t: float) -> List[Vec[float]]:
        angle = self.start_angle + self.angle_speed*(t-self.start_time)
        return list(map(lambda p: p.rotate(angle, self.center), self.form.get_points(t)))

    def rotate(self, angle: float, center: Vec[float]) -> RotateForm:
        new_center = self.center.rotate(angle, center)
        new_form = self.form.rotate(angle, center)
        return RotateForm(new_form, new_center, self.start_angle, self.angle_speed, self.start_time, self.name)
