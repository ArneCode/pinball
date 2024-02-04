"""
This file contains the RotateForm class which can be used as a wrapper for a Form to make it rotate around a point.
"""
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
    
    Attributes:
        - form (Form): The form to rotate
        - center (Vec[float]): The point to rotate around
        - start_angle (float): The angle to start with
        - angle_speed (float): The speed of rotation
        - start_time (float): The time at which the rotation starts. If this time is in the future, the form is rotated backwards from the start_angle
        - name (str): The name of the form
"""
    form: Form
    center: Vec[float]
    start_angle: float  # the point which the form is rotated around
    angle_speed: float
    start_time: float
    name: str

    def __init__(self, form: Form, center: Vec[float], start_angle: float, angle_speed: float, start_time: float, name="rotateform"):
        """
        Initialize the RotateForm

        Args:
            - form: form to rotate
            - center: point to rotate around
            - start_angle: angle to start with
            - angle_speed: speed of rotation
            - start_time: time at which the rotation starts. 
            If this time is in the future, the form is rotated backwards from the start_angle
            - name: name of the form
        """
        self.form = form
        self.center = center
        self.start_angle = start_angle
        self.angle_speed = angle_speed
        self.start_time = start_time
        self.name = name

    def draw(self, screen: pygame.Surface, color, time: Optional[float] = None):
        """
        Draw the rotated form on the screen

        Args:
            screen (pygame.Surface): The surface to draw on
            color: The color of the form
            time (float, optional): The current time. Defaults to None.
        """
        if time is None:
            return
        angle = self.start_angle + self.angle_speed*(time-self.start_time)
        pts = self.form.get_points(time)
        pts_rotated = list(map(lambda p: p.rotate(
            angle, self.center).as_tuple(), pts))
        pygame.draw.lines(screen, color, False, pts_rotated, width=3)
        return

    def find_collision(self, ball: Ball):
        """
        Find the first collision of the ball with the form by rotating the ball trajectory

        Args:
            - ball (Ball): The ball to check for collision

        Returns:
            - RotatedCollision: The first collision of the ball with the form. Using a RotatedCollision to store the angle of the form at the time of collision to rotate the reflection vector back
        """
        # rotate the ball trajectory
        t = Polynom([0, 1])
        # rotate the ball trajectory
        angle = (t-self.start_time+ball.start_t) * \
            (-self.angle_speed)-self.start_angle # angle is a function of time
        bahn = ball.bahn.rotate_poly(angle, self.center, 6)
        # calculate the collision
        coll = self.form.find_collision(ball.with_bahn(bahn))
        if coll is None:
            return None
        # calculate the objects angle at the time of collision
        angle = self.start_angle + self.angle_speed*coll.get_coll_t()
        # return the collision. It is still in the rotated reference system, so the reflection vector has to be rotated back
        return RotatedCollision(coll, -angle)

    def get_name(self):
        """
        Get the name of the form

        Returns:
            - str: The name of the form
        """
        return self.name

    def get_material(self) -> Material:
        """
        Get the material of the form

        Returns:
            - Material: The material of the form
        """
        return self.form.get_material()

    def get_points(self, t: float) -> List[Vec[float]]:
        """
        Get the points of the form at a given time

        Args:
            - t (float): The time

        Returns:
            - List[Vec[float]]: The points of the form
        """
        angle = self.start_angle + self.angle_speed*(t-self.start_time)
        return list(map(lambda p: p.rotate(angle, self.center), self.form.get_points(t)))

    def rotate(self, angle: float, center: Vec[float]) -> RotateForm:
        """
        Rotate the form by a given angle around a given center point

        Args:
            - angle (float): The angle of rotation
            - center (Vec[float]): The center point of rotation

        Returns:
            - RotateForm: The rotated form
        """
        new_center = self.center.rotate(angle, center)
        new_form = self.form.rotate(angle, center)
        return RotateForm(new_form, new_center, self.start_angle, self.angle_speed, self.start_time, self.name)
