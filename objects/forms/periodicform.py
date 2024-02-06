"""
This module contains the class PeriodicForm, which is a form that swaps between different forms over time.
For example it can be used to make perpetual rotation, even when using a taylor series, by using a different form with a different taylor series for each part (for example each quarter) of the rotation.
"""
from __future__ import annotations
from typing import List, Tuple
from collision.coll_direction import CollDirection
from collision.collision import TimedCollision
from objects.form import Form
from objects.forms.polygonform import PolygonForm
from objects.material import Material
from math_utils.vec import Vec
from objects.path import Path
from objects.ball import Ball

class PeriodicForm(Form):
    """
    A form that swaps between different forms over time.

    Attributes:
        - forms (List[Tuple[Form, float]]): A list of tuples containing a form and the duration for which it is active.
        The time of the subforms is relative to when they start being active.
        - total_duration (float): The total duration of the periodic form.
        - outline (PolygonForm): The outline of the periodic form, a rectangle. 
        This is used to find out in which time intervals a ball is inside the periodic form and could collide with it.

    Methods:
        - __init__(forms: List[Tuple[Form, float]]): Initializes a PeriodicForm object.
        - get_form_nr(time: float) -> int: Returns the form number for a given time.
        - get_move_info(time: float) -> Tuple[Form, float, float]: Returns the form, start time, and end time for a given time.
        - find_collision(ball: Ball, ignore: List[Path] = []) -> TimedCollision: Finds the collision between the periodic form and a ball.
        - draw(screen, color, time: float): Draws the periodic form on the screen based on the current time.
        - get_name() -> str: Returns the name of the periodic form.
        - get_material() -> Material: Returns the material of the periodic form.
        - get_points(t: float) -> List[Vec[float]]: Returns the points of the periodic form at a given time.
        - rotate(angle: float, center: Vec[float]) -> PeriodicForm: Rotates the periodic form by a specified angle around a center point.
    """
    forms: List[Tuple[Form, float]]
    total_duration: float
    outline: PolygonForm

    def __init__(self, forms: List[Tuple[Form, float]]):
        """
        Initializes a PeriodicForm object.

        Args:
            - forms: A list of tuples containing a form and the duration for which it is active.
            The time of the subforms is relative to when they start being active.
        """
        self.forms = forms
        self.total_duration = 0
        for form, duration in forms:
            self.total_duration += duration

        # make an outline of the form
        # find the min and max x and y values
        min_x = None
        max_x = None
        min_y = None
        max_y = None

        for i in range(1000):
            t = self.total_duration*i/1000
            form_nr = self.get_form_nr(t)
            form, duration = self.forms[form_nr]
            points = form.get_points(t)
            for point in points:
                if min_x is None or point.x < min_x:
                    min_x = point.x
                if max_x is None or point.x > max_x:
                    max_x = point.x
                if min_y is None or point.y < min_y:
                    min_y = point.y
                if max_y is None or point.y > max_y:
                    max_y = point.y
        assert min_x is not None and min_y is not None and max_x is not None and max_y is not None
        # make the outline a bit bigger, to account for errors
        max_x *= 1.2
        max_y *= 1.2
        min_x /= 1.2
        min_y /= 1.2
        # make the outline as a rectangle polygon
        pts: List[Vec[float]] = [Vec(min_x, min_y), Vec(
            max_x, min_y), Vec(max_x, max_y), Vec(min_x, max_y)]
        self.outline = PolygonForm(pts, Material(
            0.0, 0.0, 0.0, 0.0), self_coll_direction=CollDirection.ALLOW_FROM_OUTSIDE,
            line_coll_direction=CollDirection.ALLOW_ALL, name="periodic_outline")

    def get_form_nr(self, time: float) -> int:
        """
        Returns the form number for a given time. The form number is the index of the form that is active at the given time.

        Args:
            - time (float): The time.

        Returns:
            - int: The form number.
        """
        time = time % self.total_duration
        for i in range(len(self.forms)):
            form, duration = self.forms[i]
            if time < duration:
                return i
            time -= duration
        raise ValueError("time is too big")

    def get_move_info(self, time: float) -> Tuple[Form, float, float]:
        """
        Returns information about the form that is active at a given time. This includes the form, the start time, and the end time of the form.
        TODO: find a better way to do this

        Args:
            - time (float): The time.

        Returns:
            - Tuple[Form, float, float]: A tuple containing the form, the start time, and the end time of the form.
        """
        time_rel = time % self.total_duration
        delta = time - time_rel
        mov_start = 0.0

        for i in range(len(self.forms)):
            form, duration = self.forms[i]
            if time_rel < duration:
                return (form, mov_start + delta, mov_start + delta + duration)
            time_rel -= duration
            mov_start += duration
        raise ValueError("time is too big")

    def find_collision(self, ball: Ball, ignore: List[Path] = []):
        """
        Finds the collision between the periodic form and a ball.

        Args:
            - ball (Ball): The ball to check for collision.
            - ignore (List[Path], optional): A list of paths to ignore for collision detection.

        Returns:
            - TimedCollision: The collision information if a collision is found, otherwise None.
        """
        times_inside = self.outline.find_times_inside(ball)
        for interval in times_inside:
            t0 = interval.get_min()
            tmax = interval.get_max()
            t = t0
            while True:
                move_form, mov_start, mov_end = self.get_move_info(t)
                if mov_start > tmax:
                    #print("mov_start > tmax, breaking")
                    break

                # find ot where the ball is at move_start
                if mov_start > t0:
                    ball_at_move_start = ball.get_pos(mov_start)
                    vel_at_move_start = ball.bahn.deriv().apply(mov_start - ball.start_t)
                    new_ball = ball.with_start_t(0.0).with_start_pos(
                        ball_at_move_start).with_vel(vel_at_move_start)
                else:
                    ball_at_t0 = ball.get_pos(t0)
                    vel_at_t0 = ball.bahn.deriv().apply(t0 - ball.start_t)
                    new_ball = ball.with_start_t(t0-mov_start).with_start_pos(
                        ball_at_t0).with_vel(vel_at_t0)
                # find the collision
                coll = move_form.find_collision(new_ball)

                if coll is None:
                    # TODO: find a better way to do this
                    t = mov_end + 0.2
                    continue
                abs_coll_t = coll.get_coll_t() + new_ball.start_t + mov_start
                if abs_coll_t > tmax:
                    break
                rel_coll_t = abs_coll_t - ball.start_t
                return TimedCollision(coll, rel_coll_t)

    def draw(self, screen, color, time: float):
        """
        Draws the periodic form on the screen based on the current time.

        Args:
            - screen: The screen to draw on.
            - color: The color to use for drawing.
            - time (float): The current time.

        Returns:
            None
        """
        form_nr = self.get_form_nr(time)
        t = time % self.total_duration
        for i in range(form_nr):
            form, duration = self.forms[i]
            t -= duration
        form, duration = self.forms[form_nr]
        form.draw(screen, color, t)

    def get_name(self) -> str:
        return "periodicform"

    def get_material(self) -> Material:
        """
        Get the material of the form
        """
        return self.forms[0][0].get_material()

    def get_points(self, t: float) -> List[Vec[float]]:
        """
        Get the points of the active form at a given time

        Args:
            - t (float): The time

        Returns:
            - List[Vec[float]]: The points of the form at the given time
        """
        form_nr = self.get_form_nr(t)
        form, duration = self.forms[form_nr]
        return form.get_points(t)

    def rotate(self, angle: float, center: Vec[float]) -> PeriodicForm:
        """
        Rotates the periodic form by a specified angle around a center point.

        Args:
            - angle (float): The angle of rotation
            - center (Vec[float]): The center point of rotation

        Returns:
            - PeriodicForm: The rotated periodic form
        """
        new_forms = []
        for form, duration in self.forms:
            new_form = form.rotate(angle, center)
            new_forms.append((new_form, duration))
        return PeriodicForm(new_forms)
    
    def get_json(self) -> dict:
        return {
            "type": "PeriodicForm",
            "params": {
                "forms": [
                    {
                        "form": form.get_json(),
                        "duration": duration
                    }
                    for form, duration in self.forms
                ]
            }
        }
    def is_moving(self, time: float) -> bool:
        form, _, _ = self.get_move_info(time)
        return form.is_moving(time)
