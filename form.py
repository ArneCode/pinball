from __future__ import annotations
import copy
import math
from typing import Dict, List, Optional, Tuple
import pygame
from angle import angle_distance, calc_angle_between, normalize_angle
from ball import Ball
from coll_direction import CollDirection
from collision import Collision, RotatedCollision, TimedCollision
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
        # print("finding collision for abstract form")
        first_coll = None
        for path in self.paths:
            # print(f"checking path: {path}")
            coll = path.find_collision(ball)
            if coll is None:
                # print("no collision")
                continue

            if first_coll is None or coll.time < first_coll.time:
                first_coll = coll
                # print(f"new first collision: {first_coll}")
        return first_coll

    @abstractmethod
    def get_material(self) -> Material:
        pass

    @abstractmethod
    def get_points(self, t: float) -> List[Vec[float]]:
        pass
    @abstractmethod
    def rotate(self, angle: float, center: Vec[float]) -> Form:
        pass


# class StaticForm(Form):

#     @abstractmethod
#     def rotate(self, angle: float, center: Vec[float]) -> StaticForm:
#         pass

#     @abstractmethod
#     def transform(self, transform: Vec[float]) -> StaticForm:
#         pass


class CircleForm(Form):
    pos: Vec
    radius: float
    min_angle: float
    max_angle: float
    name: str
    material: Material

    points: List[Tuple[float, float]]
    edges: List[Tuple[Vec, bool]]
    paths: List[Path]
    color: Tuple[float, float, float]

    def __init__(self, pos: Vec, radius, material: Material, color: Tuple, min_angle: float = 0, max_angle: float = 2*math.pi, resolution=100, ball_radius=50, name="circle"):

        self.pos = pos
        self.radius = radius
        self.min_angle = min_angle
        self.max_angle = max_angle
        self.points = []
        self.edges = []
        self.paths = []
        self.name = name
        self.material = material
        self.color = color
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
            cap = CirclePath(cap_pos, ball_radius, self, angle_a,
                             angle_b, CollDirection.ALLOW_FROM_OUTSIDE, "min_cap")
            self.paths.append(cap)
            # max cap:
            cap_pos = Vec(math.cos(max_angle)*radius + pos.x,
                          math.sin(max_angle)*radius + pos.y)
            angle_a = max_angle
            angle_b = max_angle + math.pi
            cap = CirclePath(cap_pos, ball_radius, self, angle_a,
                             angle_b, CollDirection.ALLOW_FROM_OUTSIDE, "max_cap")
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

    def get_points(self, t):
        return map(lambda p: Vec(p[0], p[1]), self.points)
        # for kante in self.paths:
        # pygame.draw.circle(screen, color, kante, 50)
        #    kante.draw(screen, color)

    def get_name(self):
        return self.name

    def rotate(self, angle: float, center: Vec[float]) -> CircleForm:
        angle = -angle
        new_pos = self.pos.rotate(angle, center)
        return CircleForm(new_pos, self.radius, self.material, self.color, self.min_angle+angle, self.max_angle+angle, name=self.name)

    # def transform(self, transform: Vec[float]) -> StaticForm:
    #     new_pos = self.pos + transform
    #     return CircleForm(new_pos, self.radius, self.material, self.color, self.min_angle, self.max_angle, name=self.name)

    def get_material(self) -> Material:
        return self.material


class LineForm(Form):
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
        self.paths.append(LinePath(pos1+normal, pos2+normal,
                          self, normal, CollDirection.ALLOW_FROM_OUTSIDE))
        self.paths.append(LinePath(pos1-normal, pos2-normal,
                          self, normal*(-1), CollDirection.ALLOW_FROM_OUTSIDE))
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

    def get_points(self, t):
        return [self.pos1, self.pos2]

    def get_name(self):
        return self.name

    def rotate(self, angle: float, center: Vec[float]) -> LineForm:
        new_pos1 = self.pos1.rotate(angle, center)
        new_pos2 = self.pos2.rotate(angle, center)
        return LineForm(new_pos1, new_pos2, self.ball_radius, self.material, self.name)

    # def transform(self, transform: Vec[float]) -> StaticForm:
    #     new_pos1 = self.pos1 + transform
    #     new_pos2 = self.pos2 + transform
    #     return LineForm(new_pos1, new_pos2, self.ball_radius, self.material, self.name)

    def get_material(self) -> Material:
        return self.material


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
        pts_rotated = list(map(lambda p: p.rotate(angle, self.center).as_tuple(), pts))
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
            #print(f"t0: {t0}, tmax: {tmax}, ball: {ball}")
            #while t < interval.end:
            t = t0
            while True:
                move_form, mov_start, mov_end = self.get_move_info(t)
                #print(f"t: {t}, mov_start: {mov_start}, mov_end: {mov_end}")
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
                #print("new_ball: ", new_ball)
                #print(f"pos_old_ball: {ball.get_pos(t + 100.0)}, pos_new_ball: {new_ball.get_pos(t + 100.0)}")
                #print(f"old_ball: {ball}, new_ball: {new_ball}")
                # find the collision
                coll = move_form.find_collision(new_ball)
                
                if coll is None:
                    t = mov_end + 0.2
                    continue
                coll_form = coll.get_obj_form()
                other_coll = coll_form.find_collision(new_ball)
                #if other_coll is not None:
                #    print(f"other_coll: {other_coll}")
                #print(f"coll_obj: {coll.get_obj_form()}")
                abs_coll_t = coll.get_coll_t() + new_ball.start_t + mov_start
                if abs_coll_t > tmax:
                    break
                rel_coll_t = abs_coll_t - ball.start_t
                #print(f"found coll at {abs_coll_t} (inside PeriodicForm), coll_t: {coll.get_coll_t()}, ball_start_t: {ball.start_t}, mov_start: {mov_start}, rel_coll_t: {rel_coll_t}")
                if abs_coll_t > 7.0 and abs_coll_t < 8.0 and False:
                    raise ValueError("test")
                return TimedCollision(coll, rel_coll_t)
                

                #ball_at_move_start = ball.get_pos(mov_start)
                #vel_at_move_start = ball.bahn.deriv().apply(mov_start)


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


def get_all_coll_times(paths: List[Path], bahn: Vec[Polynom]) -> List[float]:
    colls = []
    for path in paths:
        coll = path.find_all_collision_times(bahn)
        if coll is not None:
            colls += coll
    # sort the collisions
    colls.sort()
    # remove duplicates
    new_colls = []
    for i in range(len(colls)):
        if i == 0 or not math.isclose(colls[i], colls[i-1], abs_tol=0.0001):
            new_colls.append(colls[i])
    return new_colls


class PolygonForm(Form):
    points: List[Vec[float]]
    point_tuples: List[Tuple[float, float]]
    name: str
    material: Material
    paths: List[Path]
    edge_normals: List[Vec[float]]
    self_coll_direction: CollDirection
    line_coll_direction: CollDirection

    def __init__(self, points: List[Vec[float]],
                 material: Material, self_coll_direction: CollDirection = CollDirection.ALLOW_FROM_OUTSIDE,
                 line_coll_direction: CollDirection = CollDirection.ALLOW_FROM_OUTSIDE, name="polygon", edge_normals: Optional[List[Vec[float]]] = None):
        self.points = points
        self.name = name
        self.material = material
        self.self_coll_direction = self_coll_direction
        self.line_coll_direction = line_coll_direction
        if edge_normals is None:
            self.find_edge_normals()
        else:
            self.edge_normals = edge_normals
        # print(f"self_coll_direction: {self_coll_direction}")
        if self_coll_direction == CollDirection.ALLOW_FROM_INSIDE:
            self.paths = self.make_paths(50, -1)
        elif self_coll_direction == CollDirection.ALLOW_FROM_OUTSIDE:
            self.paths = self.make_paths(50, 1)
        else:
            self.paths = self.make_paths(50) + self.make_paths(50, -1)
        # self.paths = self.make_paths(50)
        self.point_tuples = []

        for point in points:
            self.point_tuples.append((point.x, point.y))
        super().__init__(self.paths)

    def find_edge_normals(self):
        points = self.points
        self.edge_normals = []

        # paths that lie on the polygon edges
        edge_paths: List[Path] = []
        for i in range(len(points)):
            p1 = points[i]
            p2 = points[(i+1) % len(points)]
            edge_paths.append(
                LinePath(p1, p2, self, Vec(0, 0), CollDirection.ALLOW_ALL))

        # find the normal for each edge
        for i in range(len(points)):
            p1 = points[i]
            p2 = points[(i+1) % len(points)]
            middle = (p1+p2)*0.5
            normal = (p2-p1).normalize().orhtogonal()
            t = Polynom([0, 1])
            # find out if the normal points inwards or outwards
            # put a point in the middle of the line moved by the normal
            checked_pt = middle + normal

            # construct a ray from the point, direction doesn't matter
            ray = checked_pt + normal*t
            # find all collisions with the ray
            colls = get_all_coll_times(edge_paths, ray)
            # if there is an odd number of collisions, the checked point is inside the polygon, meaning the normal points inwards
            # otherwise it points outwards

            # if the normal points inwards, flip it
            if len(colls) % 2 == 1:
                # print("flipping normal")
                normal = normal*(-1)
            else:
                # print(f"not flipping normal, colls: {colls}")
                pass
            self.edge_normals.append(normal)

    def make_paths(self, ball_radius: float, normal_factor: float = 1.0) -> List[Path]:
        paths: List[Path] = []
        prev_pt = None
        for i in range(len(self.points)):
            p1 = self.points[i]
            p2 = self.points[(i+1) % len(self.points)]
            p3 = self.points[(i+2) % len(self.points)]
            normal = self.edge_normals[i]*normal_factor
            next_normal = self.edge_normals[(
                i+1) % len(self.points)]*normal_factor
            # print(f"p1: {p1}, p2: {p2}")
            # the line
            if prev_pt is None:
                line = LinePath(p1 + normal*ball_radius, p2 + normal *
                                ball_radius, self, normal, self.line_coll_direction)
            else:
                # print(f"prev_pt: {prev_pt}")
                line = LinePath(prev_pt, p2 + normal*ball_radius,
                                self, normal, self.line_coll_direction)
            # make a circle to cap the line if the corner between this edge and the next is pointed outwards
            # to do this, check if the angle between the two normals is smaller than 180°
            if normal_factor > 0:
                angle = calc_angle_between(normal, next_normal)
            else:
                angle = calc_angle_between(next_normal, normal)

            # if the angle is smaller than 180°, the corner is pointed outwards
            if angle < math.pi:
                # print("corner pointed outwards")
                # make a circle to cap the line
                if normal_factor > 0:
                    angle_a = normal.get_angle()
                    angle_b = next_normal.get_angle()
                else:
                    angle_a = next_normal.get_angle()
                    angle_b = normal.get_angle()
                # angle_a = normal.get_angle()
                # angle_b = next_normal.get_angle()
                paths.append(line)
                paths.append(CirclePath(p2, ball_radius, self, angle_a,
                             angle_b, self.line_coll_direction))
                prev_pt = None
            else:
                # print("corner pointed inwards")
                # find the intersection of this line and the next line
                # make a ray starting from p1 going towards p2
                ray_dir = (p2-p1).normalize()
                t = Polynom([0, 1])
                ray = p1 + normal*ball_radius + ray_dir*t
                # find where the next line intersects with the ray
                next_line = LinePath(p2 + next_normal*ball_radius, p3 + next_normal *
                                     ball_radius, self, next_normal, CollDirection.ALLOW_ALL)
                colls = next_line.find_all_collision_times(ray)
                if len(colls) == 0:
                    paths.append(line)
                    continue
                    print(
                        f"no intersection found, p1: {p1}, p2: {p2}, p3: {p3}, normal: {normal}, next_normal: {next_normal}, ray: {ray}")
                    raise ValueError("no intersection found")
                inrsct = ray.apply(colls[0])
                if prev_pt is None:
                    # print("prev_pt is none, down here")
                    line = LinePath(p1 + normal*ball_radius, inrsct,
                                    self, normal, self.line_coll_direction)
                else:
                    # print("using down here")
                    line = LinePath(prev_pt, inrsct, self, normal,
                                    self.line_coll_direction)
                prev_pt = inrsct
                paths.append(line)
        if prev_pt is not None:
            # print("redoing first line")
            line_0 = paths[0]
            assert isinstance(line_0, LinePath)
            p2 = line_0.pos2
            normal = line_0.normal
            line = LinePath(prev_pt, p2, self, normal,
                            self.line_coll_direction)
            paths[0] = line

        return paths

    def find_times_inside(self, ball: Ball) -> List[SimpleInterval]:
        colls = get_all_coll_times(self.paths, ball.bahn)

        # assert len(colls) % 2 == 0
        if len(colls) % 2 == 1:
            # ball is already inside the polygon
            # add 0 to colls, first element
            colls = [0] + colls
        for i in range(len(colls)):
            colls[i] += ball.start_t
        intervals = []
        for i in range(0, len(colls), 2):
            intervals.append(SimpleInterval(colls[i], colls[i+1]))
        return intervals

    def draw(self, screen, color, time: float):
        pygame.draw.polygon(screen, color, self.point_tuples, width=3)
        for path in self.paths:
            path.draw(screen, color)

    def get_points(self, t: float) -> List[Vec[float]]:
        return self.points

    def get_name(self):
        return self.name

    def rotate(self, angle: float, center: Vec[float]) -> PolygonForm:
        new_points = []
        for point in self.points:
            new_points.append(point.rotate(angle, center))
        return PolygonForm(new_points, self.material, self.self_coll_direction, self.line_coll_direction, self.name)

    #def transform(self, transform: Vec[float]) -> StaticForm:
    #     new_points = []
    #     for point in self.points:
    #         new_points.append(point + transform)
    #     return PolygonForm(new_points, self.material, self.self_coll_direction, self.line_coll_direction, self.name)

    def get_material(self) -> Material:
        return self.material
    def __str__(self) -> str:
        point_str = ""
        for point in self.points:
            point_str += f"{point}, "
        return f"PolygonForm(points=[{point_str}], name={self.name})"
    