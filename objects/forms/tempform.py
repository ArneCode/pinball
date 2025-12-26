"""
This module defines the TempForm class, which represents a form that is a certain Form for a period of time and becomes another form afterwards.

Classes:
- TempForm
"""

from __future__ import annotations
from typing import List
from objects.form import Form
from objects.ball import Ball
from objects.material import Material
from math_utils.vec import Vec
from objects.path import Path

# A form that is a certain Form for a period of time and becomes another form afterwards
class TempForm(Form):
    """
    A temporary form that transitions between two forms over a specified duration.

    Attributes:
        - start_form (Form): The starting form.
        - form_duration (float): The duration of the transition between the start and end forms.
        - end_form (Form): The ending form.
        - name (str): The name of the temporary form.
        - i (int): A counter for tracking collisions.

    Methods:
        - __init__(start_form: Form, form_duration: float, end_form: Form, name="tempform"): Initializes a TempForm object.
        - draw(screen, color, time: float): Draws the temporary form on the screen based on the current time.
        - find_collision(ball: Ball, ignore: List[Path] = []): Finds the collision between the temporary form and a ball.
        - get_name(): Returns the name of the temporary form.
        - get_material() -> Material: Returns the material of the temporary form.
        - get_points(t: float) -> List[Vec[float]]: Returns the points of the temporary form at a given time.
        - rotate(angle: float, center: Vec[float]) -> TempForm: Rotates the temporary form by a specified angle around a center point.
    """
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
        """
        Draws the temporary form on the screen based on the current time.

        Args:
            - screen: The screen to draw on.
            - color: The color to use for drawing.
            - time (float): The current time.

        Returns:
            None
        """
        if time is None:
            return
        if time < self.form_duration:
            self.start_form.draw(screen, color, time)
        else:
            self.end_form.draw(screen, color, time)

    def find_collision(self, ball: Ball, ignore: List[Path] = []):
        """
        Finds the collision between the temporary form and a ball.

        Args:
            ball (Ball): The ball to check for collision.
            ignore (List[Path], optional): A list of paths to ignore for collision detection.

        Returns:
            The collision information if a collision is found, otherwise None.
        """
        self.i += 1
        if ball.start_t >= self.form_duration:
            return self.end_form.find_collision(ball)

        coll_start = self.start_form.find_collision(ball)
        if coll_start is not None and coll_start.get_coll_t() + ball.start_t < self.form_duration:
            return coll_start

        coll_end = self.end_form.find_collision(ball)
        if coll_end is None:
            pass
        elif coll_end.get_coll_t() + ball.start_t >= self.form_duration:
            return coll_end

        return None

    def get_name(self):
        """
        Returns the name of the temporary form.

        Returns:
            The name of the temporary form.
        """
        return self.name

    def get_material(self) -> Material:
        """
        Returns the material of the temporary form.

        Returns:
            The material of the temporary form.
        """
        return self.start_form.get_material()

    def get_points(self, t: float) -> List[Vec[float]]:
        """
        Returns the points of the temporary form at a given time. 
        If the time is before the form duration, the points of the start form are returned. Otherwise, the points of the end form are returned.

        Args:
            t (float): The time.

        Returns:
            The points of the temporary form at the given time.
        """
        if t < self.form_duration:
            return self.start_form.get_points(t)
        else:
            return self.end_form.get_points(t)

    def rotate(self, angle: float, center: Vec[float]) -> TempForm:
        """
        Rotates the temporary form by a specified angle around a center point.

        Args:
            angle (float): The angle of rotation in degrees.
            center (Vec[float]): The center point of rotation.

        Returns:
            A new TempForm object that is rotated.
        """
        new_start_form = self.start_form.rotate(angle, center)
        new_end_form = self.end_form.rotate(angle, center)
        return TempForm(new_start_form, self.form_duration, new_end_form, self.name)
    def get_json(self) -> dict:
        return {
            "type": "TempForm",
            "params": {
                "start_form": self.start_form.get_json(),
                "form_duration": self.form_duration,
                "end_form": self.end_form.get_json()
            }
        }
    def is_moving(self, t: float) -> bool:
        return self.start_form.is_moving(t) if t < self.form_duration else self.end_form.is_moving(t)