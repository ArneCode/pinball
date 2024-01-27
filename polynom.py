from __future__ import annotations
from typing import Callable, Dict, Optional, List, Tuple
import numbers
import math
from interval import Interval, SimpleInterval
import numpy as np


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
        if isinstance(other, Polynom):
            x = Polynom([0, 1])
            new_poly = Polynom([0])
            for (i_own, k_own) in enumerate(self.koefs):
                for (i_other, k_other) in enumerate(other.koefs):
                    new_poly += (x**(i_own+i_other))*(k_own*k_other)
            return new_poly
        if not isinstance(other, numbers.Number):
            raise TypeError(f"got weird other: {other}, type: {type(other)}")
        new_koeffs: List[float | int] = [0]*len(self.koefs)
        for (i, k) in enumerate(self.koefs):
            new_koeffs[i] = k*other
        return Polynom(new_koeffs)

    def __pow__(self, exp):
        assert isinstance(exp, int)
        pytag_pyramid: Dict[Tuple[int,...], float] = {} #pascall!!!!

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
        new_koeffs = [0.0]*(max_exp*exp + 1)
        for (iter_exps, loop_koeff) in pytag_pyramid.items():
            #assert isinstance(koeff, float)
            total_exp = 0
            for (exp, exp_factor) in enumerate(iter_exps):
                x: float = self.koefs[exp]**exp_factor
                loop_koeff *= x
                total_exp += exp*exp_factor
            new_koeffs[total_exp] += loop_koeff
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
            if not math.isclose(k, 0.0, abs_tol=1e-17):
                non0_end = i + 1
                break
        return Polynom(self.koefs[0:non0_end])

    def __str__(self) -> str:
        s = "Polynom{"
        for (i, k) in enumerate(self.koefs):
            s += f"{k}*t^{i} + "
        s = s[:-3]
        s += "}"
        return s
        #return f"Polynom{{{self.koefs}}}"

    def get_grad(self) -> int:
        return len(self.koefs) - 1

    def find_roots(self, x_range: Optional[Interval] = None, filter_fn: Optional[Callable[[float], bool]] = None, return_smallest=True, do_numeric=False) -> List[float]:
        this = self.reduce()
        result = []
        if this.get_grad() < 1:
            #raise ValueError(f"cannot find the roots of: {this}")
            return []
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
            result.sort()

        elif do_numeric and x_range is not None:
            assert x_range is not None
            #result = self.smallest_root_bisect(x_range, return_smallest=return_smallest
            result = np.roots(self.koefs[::-1])
            result = list(filter(np.isreal, result))
            result = np.real(result)
            #print(f"direct/dirty result: {result}")

            result = list(filter(lambda x: x>0.1, result))
            result.sort()
            #print(f"result: {result}")
            #old_result = self.smallest_root_bisect_old(x_range, return_smallest=return_smallest, filter_fn=filter_fn)
            #if len(result) > 0:
            #    print(f"result: {result}, old_result: {old_result}")
            #return old_result
        if x_range is not None:
            result = list(filter(x_range.check, result))
        if filter_fn is not None:
            len_before = len(result)
            result = list(filter(filter_fn, result))
        if return_smallest and len(result) > 0:
            return [result[0]]
        return result
    
    # find roots using midnight formula etc.
    def find_roots_algebraic(self, x_range: Optional[Interval] = None, return_smallest=True) -> List[float]:
        #this = self.reduce()
        this = self
        result = []
        if this.get_grad() < 1:
            raise ValueError(f"cannot find the roots of: {this}")
        if this.get_grad() == 1:
            a = self.koefs[0]
            b = self.koefs[1]
            result = [-a/b]

        elif this.get_grad() == 2:
            a = self.koefs[2]
            b = self.koefs[1]
            c = self.koefs[0]
            if b**2 < 4*a*c:
                return []
            root = math.sqrt(b**2-4*a*c)
            x1 = (-b + root)/(2*a)
            x2 = (-b - root)/(2*a)
            result = [x1, x2]
        else:
            raise ValueError(f"cannot find the roots of: {this}, too high degree: {this.get_grad()}")
        if x_range is not None:
            result = list(filter(x_range.check, result))
        if return_smallest and len(result) > 0:
            return [result[0]]
        return result
    
    def smallest_root_bisect(self, x_range: Interval, return_smallest=True) -> List[float]:
        # derive the polynom until it is quadratic
        # then use find_roots_algebraic
        curr = self
        prevs = []
        while curr.get_grad() > 2:
            prevs.append(curr)
            curr = curr.deriv()
        # curr is now quadratic
        # find roots
        curr_roots = curr.find_roots_algebraic(x_range, return_smallest=False)
        curr_roots.sort()
        curr_roots.append(x_range.get_max())
        # curr roots are the peaks/valleys of the previous polynom
        # find the roots of the previous polynoms by using the bisect method
        for prev in reversed(prevs):
            curr_roots.append(x_range.get_max())
            new_roots = []
            # to do bisect we need a point above and below the 0
            prev_value = prev.apply(x_range.get_min())
            prev_x = x_range.get_min()
            for root in curr_roots:
                curr_value = prev.apply(root)
                if prev_value < 0 and curr_value >= 0:
                    new_roots.append(prev.root_bisect(prev_x, root))
                elif prev_value >= 0 and curr_value < 0:
                    new_roots.append(prev.root_bisect(root, prev_x))
                prev_value = curr_value
                prev_x = root
            curr_roots = list(filter(x_range.check, new_roots))
            
        return curr_roots


    def smallest_root_bisect_old(self, x_range: Optional[Interval] = None, n_steps=1000, return_smallest=True, filter_fn: Optional[Callable[[float], bool]] = None) -> List[float]:
        """
        find roots using the bisection method
        """
        if x_range is None or True:
            x_range = SimpleInterval(0.5, 50.0)
        prev_x = None
        prev_y = None
        results: List[float] = []
        for x in x_range.step_through(n_steps):
            #print(f"x: {x}")
            y = self.apply(x)
            result = None
            if (prev_y is not None) and prev_y < 0 and y >= 0:
                result = self.root_bisect(prev_x, x)
            elif (prev_y is not None) and prev_y >= 0 and y < 0:
                result = self.root_bisect(x, prev_x)
            if result is not None:
                if (filter_fn is None or filter_fn(result)):
                    if result < 0.1:
                        raise ValueError(f"prev_y: {prev_y}, y: {y}, prev_x: {prev_x}, x: {x}, result: {result}, self: {self}")
                    results.append(result)
                    if return_smallest: #hässlich
                        return results
            prev_x = x
            prev_y = y
        # return results if return_list else None
        return results

    def root_bisect(self, a, b, max_steps=1000):
        """
        find a single root using the bisection method
        """
        # check if a and b are on different sides of the root
        if self.apply(a) > 0 and self.apply(b) > 0:
            raise ValueError(
                f"root is not between {a} and {b}, a: {self.apply(a)}, b: {self.apply(b)}")
        if self.apply(a) < 0 and self.apply(b) < 0:
            raise ValueError(
                f"root is not between {a} and {b}, a: {self.apply(a)}, b: {self.apply(b)}")
        ya = self.apply(a)
        yb = self.apply(b)
        i = 0

        while not math.isclose(yb, 0.0, abs_tol=0.0001) and i < max_steps and i > 1:
            #print(f"ya: {ya}, yb: {yb}")
            mid = (a+b)/2
            ym = self.apply(mid)
            if ym < 0:
                a = mid
                ya = ym
            else:
                b = mid
                yb = ym
            i += 1
        return b
