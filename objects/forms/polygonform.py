from __future__ import annotations
import math
from typing import List
import pygame
from collision.coll_direction import CollDirection
from math_utils.angle import calc_angle_between
from math_utils.interval import SimpleInterval
from objects.ball import Ball
from objects.material import Material
from objects.form import Form
from objects.path import Path, CirclePath, LinePath
from math_utils.vec import Vec
from math_utils.polynom import Polynom
from typing import Optional, Tuple


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

    # def transform(self, transform: Vec[float]) -> StaticForm:
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
