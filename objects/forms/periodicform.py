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
    forms: List[Tuple[Form, float]]
    total_duration: float
    outline: PolygonForm

    def __init__(self, forms: List[Tuple[Form, float]]):
        self.forms = forms
        self.total_duration = 0
        for form, duration in forms:
            self.total_duration += duration

        # make an outline of the form
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
        max_x *= 1.03
        max_y *= 1.03
        min_x /= 1.03
        min_y /= 1.03
        # make the outline
        pts: List[Vec[float]] = [Vec(min_x, min_y), Vec(
            max_x, min_y), Vec(max_x, max_y), Vec(min_x, max_y)]
        self.outline = PolygonForm(pts, Material(
            0.0, 0.0, 0.0, 0.0), self_coll_direction=CollDirection.ALLOW_FROM_OUTSIDE,
            line_coll_direction=CollDirection.ALLOW_ALL, name="periodic_outline")

    def get_form_nr(self, time: float) -> int:
        # print(f"getting form nr for time {time}, total_duration: {self.total_duration}")
        time = time % self.total_duration
        for i in range(len(self.forms)):
            form, duration = self.forms[i]
            if time < duration:
                return i
            time -= duration
        raise ValueError("time is too big")

    def get_move_info(self, time: float) -> Tuple[Form, float, float]:
        """
        Returns: (form, mov_start, mov_end)
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
        times_inside = self.outline.find_times_inside(ball)
        for interval in times_inside:
            t0 = interval.get_min()
            tmax = interval.get_max()
            # print(f"t0: {t0}, tmax: {tmax}, ball: {ball}")
            # while t < interval.end:
            t = t0
            while True:
                move_form, mov_start, mov_end = self.get_move_info(t)
                # print(f"t: {t}, mov_start: {mov_start}, mov_end: {mov_end}")
                if mov_start > tmax:
                    print("mov_start > tmax, breaking")
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
                # print("new_ball: ", new_ball)
                # print(f"pos_old_ball: {ball.get_pos(t + 100.0)}, pos_new_ball: {new_ball.get_pos(t + 100.0)}")
                # print(f"old_ball: {ball}, new_ball: {new_ball}")
                # find the collision
                coll = move_form.find_collision(new_ball)

                if coll is None:
                    t = mov_end + 0.2
                    continue
                coll_form = coll.get_obj_form()
                other_coll = coll_form.find_collision(new_ball)
                # if other_coll is not None:
                #    print(f"other_coll: {other_coll}")
                # print(f"coll_obj: {coll.get_obj_form()}")
                abs_coll_t = coll.get_coll_t() + new_ball.start_t + mov_start
                if abs_coll_t > tmax:
                    break
                rel_coll_t = abs_coll_t - ball.start_t
                # print(f"found coll at {abs_coll_t} (inside PeriodicForm), coll_t: {coll.get_coll_t()}, ball_start_t: {ball.start_t}, mov_start: {mov_start}, rel_coll_t: {rel_coll_t}")
                if abs_coll_t > 7.0 and abs_coll_t < 8.0 and False:
                    raise ValueError("test")
                return TimedCollision(coll, rel_coll_t)

                # ball_at_move_start = ball.get_pos(mov_start)
                # vel_at_move_start = ball.bahn.deriv().apply(mov_start)

    def draw(self, screen, color, time: float):
        form_nr = self.get_form_nr(time)
        print(f"form_nr: {form_nr}")
        t = time % self.total_duration
        for i in range(form_nr):
            form, duration = self.forms[i]
            # form.draw(screen, color, duration)
            t -= duration
        form, duration = self.forms[form_nr]
        form.draw(screen, color, t)

    def get_name(self) -> str:
        return "periodicform"

    def get_material(self) -> Material:
        return self.forms[0][0].get_material()

    def get_points(self, t: float) -> List[Vec[float]]:
        form_nr = self.get_form_nr(t)
        form, duration = self.forms[form_nr]
        return form.get_points(t)

    def rotate(self, angle: float, center: Vec[float]) -> PeriodicForm:
        new_forms = []
        for form, duration in self.forms:
            new_form = form.rotate(angle, center)
            new_forms.append((new_form, duration))
        return PeriodicForm(new_forms)
