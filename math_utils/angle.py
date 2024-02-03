from __future__ import annotations

import math

from math_utils.vec import Vec


# function that return the angle between 0 and 2pi
def normalize_angle(angle: float) -> float:
    while angle < 0:
        angle += 2*math.pi
    return angle % (2*math.pi)
def angle_distance(angle_a: float, angle_b: float) -> float:
    """
    returns the distance between two angles
    """
    # calculate the difference between the angles
    # in both directions, because a difference of 1.5pi is the same as 0.5pi
    # and we want the smallest distance
    dist_a = normalize_angle(angle_a - angle_b)
    dist_b = normalize_angle(angle_b - angle_a)
    return min(dist_a, dist_b)
def check_angle_between(angle: float, angle_min: float, angle_max: float) -> bool:
    """
    returns wether angle is between angle_min and angle_max
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
    returns the angle between two vectors, calculated from "from" to "to"
    """
    angle_to = to.get_angle()
    angle_from = _from.get_angle()

    angle_between = angle_to - angle_from
    while angle_between < 0:
        angle_between += 2*math.pi
    return angle_between