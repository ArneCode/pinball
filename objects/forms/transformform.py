from __future__ import annotations
from typing import List, Optional
import pygame
from math_utils.polynom import Polynom
from objects.ball import Ball
from objects.form import Form
from objects.material import Material
from math_utils.vec import Vec
class TransformForm(Form):
    """
    Transform a form by a function
    """
    form: Form
    transform: Vec[Polynom]
    name: str

    def __init__(self, form: Form, transform: Vec[Polynom], name="transformform"):
        self.form = form
        self.transform = transform
        self.name = name

    def draw(self, screen: pygame.Surface, color, time: Optional[float] = None):
        if time is None:
            return
        diff = self.transform.apply(time)
        pts = self.form.get_points(time)
        pts_transformed = list(map(lambda p: (p + diff).as_tuple(), pts))
        pygame.draw.lines(screen, color, False, pts_transformed, width=3)
        return

    def find_collision(self, ball: Ball):
        # print(f"finding collision for rotateform, ball: {ball}")
        # rotate the ball trajectory
        t = Polynom([0, 1])
        # rotate the ball trajectory
        bahn = ball.bahn - self.transform.apply(t+ball.start_t)
        # print(f"bahn transformed: {bahn}, ball bahn: {ball.bahn}")
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

    def get_points(self, t: float) -> List[Vec[float]]:
        transform = self.transform.apply(t)
        return list(map(lambda p: p + transform, self.form.get_points(t)))

    def rotate(self, angle: float, center: Vec[float]) -> TransformForm:
        new_form = self.form.rotate(angle, center)
        new_transform = self.transform.apply(angle)
        return TransformForm(new_form, new_transform, self.name)
