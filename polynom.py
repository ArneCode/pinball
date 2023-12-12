from __future__ import annotations
from typing import Optional, List
import numbers
import math
from interval import Interval


class Polynom:
    koefs: List[float | int]

    def __init__(self, koefs):
        self.koefs = koefs

    def deriv(self):
        new_koeffs = []
        for (exp, koeff) in enumerate(self.koefs):
            if exp == 0:
                continue
            new_koeffs.append(koeff*exp)
        return Polynom(new_koeffs)

    def __add__(self, other: int | float | Polynom) -> Polynom:
        if isinstance(other, numbers.Number):
            other = Polynom([other])
        if not isinstance(other, Polynom):
            raise TypeError(
                f"expected Polynom or Number, but got {type(other)}: {other}")
        if self.get_grad() > other.get_grad():
            l = self.koefs
            s = other.koefs
        else:
            l = other.koefs
            s = self.koefs
        new_koeffs = l.copy()
        for (i, k) in enumerate(s):
            new_koeffs[i] += k
        return Polynom(new_koeffs)

    def __neg__(self) -> Polynom:
        return Polynom(list(map(lambda k: -k, self.koefs)))

    def __sub__(self, other: float | int | Polynom):
        return self + (-other)

    def __mul__(self, other: int | float):
        if not isinstance(other, numbers.Number):
            raise TypeError(f"got weird other: {other}, type: {type(other)}")
        new_koeffs: List[float | int] = [0]*len(self.koefs)
        for (i, k) in enumerate(self.koefs):
            new_koeffs[i] = k*other
        return Polynom(new_koeffs)

    def __pow__(self, exp):
        assert isinstance(exp, int)
        pytag_pyramid = {}

        depth = 0
        exps = [0] * len(self.koefs)
        sum = 0
        max_exp = self.get_grad()
        backtracked = False
        while depth >= 0:
            if depth == max_exp:
                exps[depth] = exp - sum
                sum = exp
            if sum == exp:
                koeff = math.factorial(exp)
                for new_exp in exps:
                    koeff //= math.factorial(new_exp)
                # assert not (tuple(exps) in pytag_pyramid)
                pytag_pyramid[tuple(exps)] = koeff
                sum -= exps[depth]
                exps[depth] = 0
                depth -= 1
                backtracked = True
                continue
            if backtracked:
                exps[depth] += 1
                sum += 1
                backtracked = False
            depth += 1
        new_koeffs = [0]*(max_exp*exp + 1)
        for (exps, koeff) in pytag_pyramid.items():
            total_exp = 0
            for (exp, exp_factor) in enumerate(exps):
                koeff *= self.koefs[exp]**exp_factor
                total_exp += exp*exp_factor
            new_koeffs[total_exp] += koeff
        return Polynom(new_koeffs)

    def apply(self, x):
        sum = 0
        for (i, k) in enumerate(self.koefs):
            # diese Reihenfolge, sodass overload-operatoren verwendet werden können
            sum = (x**i)*k + sum
        return sum

    def reduce(self) -> Polynom:
        """
        if there are zeros-koefficients for the highest exponents, they are removed
        """
        non0_end = len(self.koefs)
        for i in range(non0_end-1, -1, -1):  # loops backwards
            k = self.koefs[i]
            if not math.isclose(k, 0.0, abs_tol=1e-6):
                non0_end = i + 1
                break
        return Polynom(self.koefs[0:non0_end])

    def __str__(self) -> str:
        return f"Polynom{{{self.koefs}}}"

    def get_grad(self) -> int:
        return len(self.koefs) - 1

    def find_roots(self, x_range: Optional[Interval] = None, return_smallest=True, do_numeric=False) -> List[float]:
        this = self.reduce()
        result = []
        if this.get_grad() < 1:
            raise ValueError(f"cannot find the roots of: {this}")
        if this.get_grad() == 1:
            a = self.koefs[0]
            b = self.koefs[1]
            result = [-a/b]

        elif this.get_grad() == 2:  # Mitternachtsformel
            a = self.koefs[2]
            b = self.koefs[1]
            c = self.koefs[0]
            if b**2 < 4*a*c:
                return []
            root = math.sqrt(b**2-4*a*c)
            x1 = (-b + root)/(2*a)
            x2 = (-b - root)/(2*a)
            result = [x1, x2]

        elif do_numeric and x_range is not None:
            return self.smallest_root_bisect(x_range, return_smallest=return_smallest)
        if x_range is not None:
            result = list(filter(x_range.check, result))
        if return_smallest and len(result) > 0:
            return [result[0]]
        return result

    def smallest_root_bisect(self, x_range: Interval, n_steps=100, return_smallest=True) -> List[float]:
        """
        find roots using the bisection method
        """
        prev_x = None
        prev_y = None
        results: List[float] = []
        for x in x_range.step_through(n_steps):

            y = self.apply(x)
            if (prev_y is not None) and prev_y < 0 and y >= 0:
                result = self.root_bisect(prev_x, x)
                results.append(result)
                if return_smallest:
                    return results
                # if return_list:
                #     results.append(result)
                # else:
                #     return result
            elif (prev_y is not None) and prev_y >= 0 and y < 0:
                result = self.root_bisect(x, prev_x)
                results.append(result)
                if return_smallest:
                    return results
                # else:
                #     return result
            prev_x = x
            prev_y = y
        # return results if return_list else None
        return results

    def root_bisect(self, a, b):
        """
        find a single root using the bisection method
        """
        # ya = self.apply(a)
        yb = self.apply(b)

        while not math.isclose(yb, 0.0, abs_tol=1e-6):
            mid = (a+b)/2
            ym = self.apply(mid)
            if ym < 0:
                a = mid
                # ya = ym
            else:
                b = mid
                yb = ym
        return b
