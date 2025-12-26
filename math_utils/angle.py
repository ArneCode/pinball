"""
This module provides utility functions for working with angles.

Functions:
- normalize_angle(angle: float) -> float: Returns the angle between 0 and 2pi.
- angle_distance(angle_a: float, angle_b: float) -> float: Returns the distance between two angles.
- check_angle_between(angle: float, angle_min: float, angle_max: float) -> bool: Checks if an angle is between two other angles.
- calc_angle_between(_from: Vec, to: Vec) -> float: Calculates the angle between two vectors.
"""
from __future__ import annotations

import math

from math_utils.vec import Vec


def normalize_angle(angle: float) -> float:
    """
    Returns the angle between 0 and 2pi.
    
    Args:
        angle (float): The input angle.
    
    Returns:
        float: The normalized angle between 0 and 2pi.
    """
    while angle < 0:
        angle += 2*math.pi
    return angle % (2*math.pi)


def angle_distance(angle_a: float, angle_b: float) -> float:
    """
    Returns the distance between two angles.
    
    Args:
        angle_a (float): The first angle.
        angle_b (float): The second angle.
    
    Returns:
        float: The distance between the two angles.
    """
    # in both directions, because a difference of 1.5pi is the same as 0.5pi
    # and we want the smallest distance
    dist_a = normalize_angle(angle_a - angle_b)
    dist_b = normalize_angle(angle_b - angle_a)
    return min(dist_a, dist_b)


def check_angle_between(angle: float, angle_min: float, angle_max: float) -> bool:
    """
    Checks if an angle is between two other angles.
    
    Args:
        - angle (float): The angle to check.
        - angle_min (float): The minimum angle.
        - angle_max (float): The maximum angle.
    
    Returns:
        - bool: True if the angle is between angle_min and angle_max, False otherwise.
    """
    angle = normalize_angle(angle)
    angle_min = normalize_angle(angle_min)
    angle_max = normalize_angle(angle_max)
    
    if angle_min < angle_max:
        return angle_min <= angle <= angle_max
    else:
        return angle_min <= angle or angle <= angle_max


def calc_angle_between(_from: Vec, to: Vec) -> float:
    """
    Calculates the angle between two vectors.
    
    Args:
        - _from (Vec): The starting vector.
        - to (Vec): The ending vector.
    
    Returns:
        - float: The angle between the two vectors.
    """
    angle_to = to.get_angle()
    angle_from = _from.get_angle()

    angle_between = angle_to - angle_from
    while angle_between < 0:
        angle_between += 2*math.pi
    return angle_between

def deg_to_rad(deg: float) -> float:
    """
    Converts degrees to radians.
    
    Args:
        - deg (float): The angle in degrees.
    
    Returns:
        - float: The angle in radians.
    """
    return deg * math.pi / 180

def rad_to_deg(rad: float) -> float:
    """
    Converts radians to degrees.
    
    Args:
        - rad (float): The angle in radians.
    
    Returns:
        - float: The angle in degrees.
    """
    return rad * 180 / math.pi