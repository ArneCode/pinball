"""
This file contains the TransformForm class, which is a wrapper for a form that moves it around over time using a given transformation.
"""
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
    A Wrapper for a form that moves it around over time using a given transformation

    Attributes:
        - form (Form): The form to transform
        - transform (Vec[Polynom]): The transformation to apply to the form
        - name (str): The name of the form
    """
    form: Form
    transform: Vec[Polynom]
    name: str

    def __init__(self, form: Form, transform: Vec[Polynom], name="transformform"):
        """
        Initialize the TransformForm

        Args:
            - form: form to transform
            - transform: transformation to apply to the form
            - name: name of the form
        """
        self.form = form
        self.transform = transform
        self.name = name

    def draw(self, screen: pygame.Surface, color, time: Optional[float] = None):
        """
        Draw the transformed form on the screen

        Args:
            screen (pygame.Surface): The surface to draw on
            color: color of the form
            time (float): The current time

        Returns:
            None
        """
        if time is None:
            return
        diff = self.transform.apply(time)
        pts = self.form.get_points(time)
        pts_transformed = list(map(lambda p: (p + diff).as_tuple(), pts))
        pygame.draw.lines(screen, color, False, pts_transformed, width=3)
        return

    def find_collision(self, ball: Ball):
        """
        Find the first collision of the ball with the form. This is done by moving the ball trajectory using the transformation and then finding the collision with the form.

        Args:
            - ball: ball to check for collision

        Returns:
            - Collision: first collision of the ball with the form
        """
        # move the ball trajectory using the transformation
        t = Polynom([0, 1])
        # rotate the ball trajectory
        bahn = ball.bahn - self.transform.apply(t+ball.start_t)
        # calculate the collision
        coll = self.form.find_collision(ball.with_bahn(bahn))
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

    def get_json(self) -> dict:
        return {
            "type": "TransformForm",
            "params": {
                "form": self.form.get_json(),
                "transform": self.transform.get_json(),
            }
        }
    def is_moving(self, t: float) -> bool:
        return True