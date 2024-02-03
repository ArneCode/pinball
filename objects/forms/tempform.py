from __future__ import annotations
from typing import List
from objects.form import Form
from objects.ball import Ball
from objects.material import Material
from math_utils.vec import Vec
from objects.path import Path

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
        if coll_start is not None and coll_start.get_coll_t() + ball.start_t < self.form_duration:
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

    def get_points(self, t: float) -> List[Vec[float]]:
        if t < self.form_duration:
            return self.start_form.get_points(t)
        else:
            return self.end_form.get_points(t)

    def rotate(self, angle: float, center: Vec[float]) -> TempForm:
        new_start_form = self.start_form.rotate(angle, center)
        new_end_form = self.end_form.rotate(angle, center)
        return TempForm(new_start_form, self.form_duration, new_end_form, self.name)
