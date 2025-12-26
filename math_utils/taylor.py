"""
This module provides functions for calculating sine and cosine using Taylor series expansion.

Functions:
- sin_taylor(k): Calculates the sine of x using Taylor series expansion up to the k-th term.
- cos_taylor(k): Calculates the cosine of x using Taylor series expansion up to the k-th term.
"""

import math
from math_utils.polynom import Polynom


def sin_taylor(k):
    """
    Calculates the sine of x using Taylor series expansion around 0.0 up to the k-th term.

    Parameters:
    - k (int): The number of terms to include in the Taylor series expansion.

    Returns:
    - sum (Polynom): The approximation of sine(x) using the Taylor series expansion.
    """
    x = Polynom([0, 1])
    sum = Polynom([0])
    for i in range(k):
        a = [0, 1, 0, -1][i % 4]
        sum += (x**i)*(a/math.factorial(i))
    return sum


def cos_taylor(k):
    """
    Calculates the cosine of x using Taylor series expansion aound 0.0 up to the k-th term.

    Parameters:
    - k (int): The number of terms to include in the Taylor series expansion.

    Returns:
    - sum (Polynom): The approximation of cosine(x) using the Taylor series expansion.
    """
    x = Polynom([0, 1])
    sum = Polynom([0])
    for i in range(k):
        a = [1, 0, -1, 0][i % 4]
        sum += (x**i)*(a/math.factorial(i))
    return sum
