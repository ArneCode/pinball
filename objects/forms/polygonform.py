"""This module contains the PolygonForm class."""
from __future__ import annotations
import math
from typing import Callable, Dict, List
import pygame
from collision.coll_direction import CollDirection
from math_utils.angle import calc_angle_between
from math_utils.interval import SimpleInterval
from objects.ball import Ball
from objects.material import Material
from objects.form import Form, StaticForm
from objects.path import Path, CirclePath, LinePath
from math_utils.vec import Vec
from math_utils.polynom import Polynom
from typing import Optional, Tuple


def get_all_coll_times(paths: List[Path], bahn: Vec[Polynom]) -> List[float]:
    """
    Get all collision times between a ball and a list of paths
    
    Args:
        - paths: list of paths
        - bahn: ball trajectory
            
    Returns:
        List[float]: list of collision times
        
    """
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


class PolygonForm(StaticForm):
    """
    A polygon form. It can be used to represent a Polygon in the game or sometimes as an outline for a more complex form.

    Attributes:
        - points (List[Vec[float]]): The points of the polygon
        - point_tuples (List[Tuple[float, float]]): The points of the polygon as tuples
        - name (str): The name of the polygon
        - material (Material): The material of the polygon
        - paths (List[Path]): The paths that make up the polygon
        - edge_normals (List[Vec[float]]): The normals of the edges of the polygon. They always point outwards from the polygon
        - self_coll_direction (CollDirection): The collision direction of the polygon with itself
        - line_coll_direction (CollDirection): The collision direction of the polygon with lines
    """
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
                 line_coll_direction: CollDirection = CollDirection.ALLOW_FROM_OUTSIDE, name="polygon", edge_normals: Optional[List[Vec[float]]] = None,
                  on_collision: Optional[str] = None):
        """
        Create a new polygon form
        
        Args:
            - points (List[Vec[float]]): The points of the polygon
            - material (Material): The material of the polygon
            - self_coll_direction (CollDirection, optional): The collision direction of the polygon with itself. Defaults to CollDirection.ALLOW_FROM_OUTSIDE.
            - line_coll_direction (CollDirection, optional): The collision direction of the polygon with lines. Defaults to CollDirection.ALLOW_FROM_OUTSIDE.
            - name (str, optional): The name of the polygon. Defaults to "polygon".
            - edge_normals (Optional[List[Vec[float]]], optional): The normals of the edges of the polygon. They always point outwards from the polygon. Defaults to None. If None, they will be calculated.
        
        Returns:
            None
        """
        self.points = points
        self.name = name
        self.material = material
        self.self_coll_direction = self_coll_direction
        self.line_coll_direction = line_coll_direction
        if edge_normals is None:
            self.find_edge_normals()
        else:
            self.edge_normals = edge_normals
        if self_coll_direction == CollDirection.ALLOW_FROM_INSIDE:
            self.paths = self.make_paths(50, -1)
        elif self_coll_direction == CollDirection.ALLOW_FROM_OUTSIDE:
            self.paths = self.make_paths(50, 1)
        else:
            self.paths = self.make_paths(50) + self.make_paths(50, -1)
        self.point_tuples = []

        for point in points:
            self.point_tuples.append((point.x, point.y))
        super().__init__(self.paths, on_collision=on_collision)

    def find_edge_normals(self):
        """
        Find the normals of the edges of the polygon. They always point outwards from the polygon.
        To do this, a ray is cast from the middle of each edge plus the assumed normal. If the ray intersects an odd number of edges, the normal points inwards and is flipped.

        Returns:
            None
        """
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
        """
        Make the paths that give the polygon the ability to collide with balls.
        The paths are the edges of the polygon and circles that cap the edges if the corner is pointed outwards.
        Edges are moved by the normals times a factor, either pointing them inwards or outwards.

        Args:
            - ball_radius (float): The radius of the balls
            - normal_factor (float, optional): The factor by which to multiply the normals. Defaults to 1.0.

        Returns:
            List[Path]: The paths that make up the polygon
        """
        paths: List[Path] = []
        prev_pt = None
        for i in range(len(self.points)):
            p1 = self.points[i]
            p2 = self.points[(i+1) % len(self.points)]
            p3 = self.points[(i+2) % len(self.points)]
            normal = self.edge_normals[i]*normal_factor
            next_normal = self.edge_normals[(
                i+1) % len(self.points)]*normal_factor
            # the line
            if prev_pt is None:
                line = LinePath(p1 + normal*ball_radius, p2 + normal *
                                ball_radius, self, normal, self.line_coll_direction)
            else:
                line = LinePath(prev_pt, p2 + normal*ball_radius,
                                self, normal, self.line_coll_direction)
            # make a circle to cap the line if the corner between this edge and the next is pointed outwards
            # to do this, check if the angle between the two normals is smaller than 180°
            # EXPLAIN: why do we need to switch the normals based on the normal_factor?
            if normal_factor > 0:
                angle = calc_angle_between(normal, next_normal)
            else:
                angle = calc_angle_between(next_normal, normal)

            # if the angle is smaller than 180°, the corner is pointed outwards
            if angle < math.pi:
                # make a circle to cap the line
                if normal_factor > 0:
                    angle_a = normal.get_angle()
                    angle_b = next_normal.get_angle()
                else:
                    angle_a = next_normal.get_angle()
                    angle_b = normal.get_angle()
                paths.append(line)
                paths.append(CirclePath(p2, ball_radius, self, angle_a,
                             angle_b, self.line_coll_direction))
                prev_pt = None
            else:
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
                    line = LinePath(p1 + normal*ball_radius, inrsct,
                                    self, normal, self.line_coll_direction)
                else:
                    line = LinePath(prev_pt, inrsct, self, normal,
                                    self.line_coll_direction)
                prev_pt = inrsct
                paths.append(line)
        if prev_pt is not None:
            # redoing the first line, if it would collide with the last line
            line_0 = paths[0]
            assert isinstance(line_0, LinePath)
            p2 = line_0.pos2
            normal = line_0.normal
            line = LinePath(prev_pt, p2, self, normal,
                            self.line_coll_direction)
            paths[0] = line

        return paths

    def find_times_inside(self, ball: Ball) -> List[SimpleInterval]:
        """
        Find the time intervals in which the ball is inside the polygon.

        Args:
            - ball (Ball): The ball to check for collision

        Returns:
            List[SimpleInterval]: The time intervals in which the ball is inside the polygon
        """
        colls = get_all_coll_times(self.paths, ball.bahn)

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
        """
        Draw the polygon on the screen.

        Args:
            - screen (pygame.Surface): The surface to draw on
            - color: The color of the form
            - time (float, optional): The current time. Defaults to None.

        Returns:
            None
        """
        pygame.draw.polygon(screen, color, self.point_tuples, width=3)
        for path in self.paths:
            path.draw(screen, color)

    def get_points(self, t: float) -> List[Vec[float]]:
        """
        Get the points of the polygon, constant over time.

        Args:
            - t (float): The time, not used

        Returns:
            List[Vec[float]]: The points of the polygon
        """
        return self.points

    def get_name(self):
        """
        Get the name of the form

        Returns:
            str: The name of the form
        """
        return self.name

    def rotate(self, angle: float, center: Vec[float]) -> PolygonForm:
        """
        Rotate the polygon by a specified angle around a center point.

        Args:
            - angle (float): The angle to rotate by
            - center (Vec[float]): The center of the rotation

        Returns:
            PolygonForm: The rotated polygon
        """
        new_points = []
        for point in self.points:
            new_points.append(point.rotate(angle, center))
        return PolygonForm(new_points, self.material, self.self_coll_direction, self.line_coll_direction, self.name)

    def get_material(self) -> Material:
        """
        Get the material of the form

        Returns:
            Material: The material of the form
        """
        return self.material

    def __str__(self) -> str:
        """
        Get the string representation of the form

        Returns:
            str: The string representation of the form
        """
        point_str = ""
        for point in self.points:
            point_str += f"{point}, "
        return f"PolygonForm(points=[{point_str}], name={self.name})"

    def get_json(self) -> dict:
        return {
            "type": "PolygonForm",
            "params": {
                "points": [point.get_json() for point in self.points],
                "name": self.name,
                "material": self.material.get_json(),
                "self_coll_direction": self.self_coll_direction.name,
                "line_coll_direction": self.line_coll_direction.name,
            }
        }