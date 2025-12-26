from __future__ import annotations
from typing import Callable, Dict, List, Optional
from math_utils.angle import angle_distance, calc_angle_between, normalize_angle
from objects.ball import Ball
from collision.coll_direction import CollDirection
from collision.collision import RotatedCollision, TimedCollision
from math_utils.interval import SimpleInterval
from objects.material import Material
from objects.path import CirclePath, LinePath, Path
from math_utils.polynom import Polynom
from math_utils.vec import Vec
from abc import ABC, abstractmethod


class Form(ABC):
    """
    Interface for all forms. A Form is an Object inside the game. 
    Collision detection is done using the objects paths, which are extended out from the form.
    """

    @abstractmethod
    def draw(self, screen, color, time: float):
        """
        Draw the form on the screen. This must be implemented by forms.

        Args:
            - screen: pygame screen
            - color: color of the form
            - time: current time of the game
        """
        pass

    @abstractmethod
    def get_name(self) -> str:
        pass

    @abstractmethod
    def find_collision(self, ball: Ball):
        pass

    @abstractmethod
    def get_material(self) -> Material:
        """
        Get the material of the form. This must be implemented by forms.

        Returns:
            - Material: material of the form
        """
        pass

    @abstractmethod
    def get_points(self, t: float) -> List[Vec[float]]:
        """
        Get the points of the form at a given time. This must be implemented by forms.

        Args:
            - t: time

        Returns:
            - List[Vec[float]]: list of points of the form
        """
        pass

    @abstractmethod
    def rotate(self, angle: float, center: Vec[float]) -> Form:
        """
        Rotate the form around a given center. This must be implemented by forms.

        Args:
            - angle: angle to rotate the form
            - center: center of the rotation

        Returns:
            - Form: rotated form
        """
        pass

    @abstractmethod
    def get_json(self) -> dict:
        pass

    @abstractmethod
    def is_moving(self, time: float) -> bool:
        pass


class StaticForm(Form):
    paths: List[Path]
    on_collision: List[str]
    do_reflect: bool

    def __init__(self, paths: List[Path], on_collision: List[str], do_reflect: bool = True):
        self.paths = paths
        self.on_collision = on_collision
        self.do_reflect = do_reflect

    def find_collision(self, ball: Ball):
        """
        Find the first collision of the ball with the form.

        Args:
            - ball: ball to check for collision

        Returns:
            - Collision: first collision of the ball with the form
        """
        # print("finding collision for abstract form")
        first_coll = None
        for path in self.paths:
            # print(f"checking path: {path}")
            coll = path.find_collision(ball)
            if coll is None:
                # print("no collision")
                continue

            if first_coll is None or coll.get_coll_t() < first_coll.get_coll_t():
                first_coll = coll
                # print(f"new first collision: {first_coll}")
        return first_coll

    def is_moving(self, time: float) -> bool:
        return False
