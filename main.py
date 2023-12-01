from __future__ import annotations
import time
import math
import numbers
# Example file showing a basic pygame "game loop"
import pygame
from pygame.math import Vector2
from interval import SimpleInterval, MultiInterval

from typing import Iterator, Optional, List


class Polynom:
    koefs: List[float | int]

    def __init__(self, koefs):
        self.koefs = koefs
        self.grad = len(self.koefs) - 1

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
        if self.grad > other.get_grad():
            print("a")
            l = self.koefs
            s = other.koefs
        else:
            print("b")
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
        max_exp = self.grad
        backtracked = False
        while depth >= 0:
            # print(f"exps: {exps}")
            if depth == max_exp:
                exps[depth] = exp - sum
                sum = exp
            if sum == exp:
                k = math.factorial(exp)
                for new_exp in exps:
                    k //= math.factorial(new_exp)
                # assert not (tuple(exps) in pytag_pyramid)
                pytag_pyramid[tuple(exps)] = k
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
        # print(pytag_pyramid)
        new_koeffs = [0]*(max_exp*exp + 1)
        for (exps, k) in pytag_pyramid.items():
            total_exp = 0
            for (exp, exp_factor) in enumerate(exps):
                k *= self.koefs[exp]**exp_factor
                total_exp += exp*exp_factor
            new_koeffs[total_exp] += k
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

    def find_smallest_root(self, x_range: Optional[SimpleInterval] = None, return_list=False, do_numeric=False) -> List[float] | float | None:
        print(f"finding roots: {self}")
        this = self.reduce()
        if this.grad < 1:
            raise ValueError(f"cannot find the roots of: {this}")
        if this.get_grad() == 1:
            a = self.koefs[0]
            b = self.koefs[1]
            result: float = -a/b
            if return_list:
                return result if x_range is None else list(filter(x_range.check, [result]))
            return result if x_range is None or x_range.check(result) else None
        #    if math.isclose(this.koefs[0], 0.0, abs_tol=1e-6):  # satz vom Nullprodukt, nicht wahrscheinlich, dass es vorkommt, da es eine Kollision direkt am Anfang der Flugbahn bedeutet
        #        roots_svn = Polynom(self.koefs[1:]).find_roots(
        #            x_range.restrict_max(0))
        #        roots_svn.append(0)
        #        return roots_svn
        if this.get_grad() == 2:  # Mitternachtsformel
            a = self.koefs[2]
            b = self.koefs[1]
            c = self.koefs[0]
            if b**2 < 4*a*c:
                return [] if return_list else None
            root = math.sqrt(b**2-4*a*c)
            x1 = (-b + root)/(2*a)
            x2 = (-b - root)/(2*a)
            result: List[float] = [x1, x2]
            if x_range is not None:
                result = list(filter(x_range.check, result))
            if return_list:
                return result
            return min(result) if result else None
        if do_numeric and x_range is not None:
            return self.smallest_root_bisect(x_range, return_list=return_list)

    def smallest_root_bisect(self, x_range: SimpleInterval, n_steps=1000, return_list=False) -> List[float] | float | None:
        """
        find roots using the bisection method
        """
        prev_x = None
        prev_y = None
        if return_list:
            results: List[float] = []
        for x in x_range.step_through(n_steps):

            # print(f"trying: {x}")
            y = self.apply(x)
            if (prev_y is not None) and prev_y < 0 and y >= 0:
                result = self.root_bisect(prev_x, x)
                if return_list:
                    results.append(result)
                else:
                    return result
            elif (prev_y is not None) and prev_y >= 0 and y < 0:
                result = self.root_bisect(x, prev_x)
                if return_list:
                    results.append(result)
                else:
                    return result
            prev_x = x
            prev_y = y
        return results if return_list else None

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


class FlugKurve:
    def __init__(self, x: Polynom, y: Polynom, r=5):
        self.x = x
        self.y = y
        self.r = r

    def get_pos(self, t):
        return Vector2(self.x.apply(t), self.y.apply(t))


class BoundingBox:
    def __init__(self, x_range: SimpleInterval, y_range: SimpleInterval):
        self.x_range = x_range
        self.y_range = y_range

    def times_inside(self, kurve: FlugKurve) -> MultiInterval | None:
        # find when ball enters/exits range
        rpos = SimpleInterval(0, float("inf"))  # positive real
        x_t_ranges = []
        x_min_colls = (
            kurve.x - (self.x_range.min - kurve.r)).find_smallest_root(rpos, return_list=True)
        x_max_colls = (
            kurve.x - (self.x_range.max + kurve.r)).find_smallest_root(rpos, return_list=True)

        x0 = kurve.x.apply(0)
        x_colls = x_min_colls + x_max_colls  # .sort()
        x_colls.sort()
        print(f"x_cols: {x_colls}")
        if x_colls is None or len(x_colls) == 0:
            print(f"x_colls is None, min: {x_min_colls}, max: {x_max_colls}")
            return None
        prev_t = 0

        if not self.x_range.check(x0):
            prev_t = x_colls.pop(0)
        for (i, t) in enumerate(x_colls):
            if i % 2 == 0:
                x_t_ranges.append(SimpleInterval(prev_t, t))
                # prev_t = None
            else:
                prev_t = t
        # if prev_t is not None:
        #     raise ValueError("Hmmmmm, sollte nicht passien")
        print(f"{len(x_t_ranges)} x_t_ranges")
        # x_t_ranges.append(Range(prev_t, self.x_range.max))

        y_min_colls = (
            kurve.y - (self.y_range.min - kurve.r)).find_smallest_root(rpos, return_list=True)
        y_max_colls = (
            kurve.y - (self.y_range.max + kurve.r)).find_smallest_root(rpos, return_list=True)

        y_colls = y_min_colls + y_max_colls
        y_colls.sort()
        print(f"y_colls: {y_colls}")
        y0 = kurve.y.apply(0)

        prev_t = 0
        if not self.y_range.check(y0):
            prev_t = y_colls.pop(0)
        t_ranges = []
        x_rang_i = 0

        for (i, t) in enumerate(y_colls):
            if i % 2 == 0:
                y_range = SimpleInterval(prev_t, t)
                # x_i = 0
                while x_rang_i < len(x_t_ranges):
                    intersect = y_range.intersect(x_t_ranges[x_rang_i])
                    if intersect is None:
                        break
                    t_ranges.append(intersect)
                    x_rang_i += 1

                # prev_t = None
            else:
                prev_t = t
        print(f"found {len(t_ranges)} ranges")
        multi_range = MultiInterval(t_ranges)  # anderen name wählen
        return multi_range


class CirclePath:
    def __init__(self, pos: Vector2, radius, x_range, y_range):
        self.pos = pos
        self.radius = radius
        self.bound = BoundingBox(x_range, y_range)

    def find_collision(self, kurve: FlugKurve) -> float | None:
        # TODO: restrict searched t by already found!
        t_range = self.bound.times_inside(kurve)
        check_eq = ((kurve.x-self.pos.x)**2 +
                    (kurve.y-self.pos.y)**2 - (self.radius)**2)
        coll = check_eq.find_smallest_root(t_range, do_numeric=True)
        return coll


class CircleForm:
    def __init__(self, pos: Vector2, radius, x_range: SimpleInterval, y_range: SimpleInterval, resolution=100, ball_radius=50):
        self.pos = pos
        self.radius = radius
        self.x_range = x_range
        self.y_range = y_range
        self.points = []
        self.edges = []
        edge_angles = []
        prev_included = False
        step_size = 2*math.pi/resolution
        for i in range(resolution):
            # print(f"i: {i}")
            a_r = i*step_size
            x = math.cos(a_r)*self.radius + self.pos.x
            y = math.sin(a_r)*self.radius + self.pos.y
            if x_range.check(x) and y_range.check(y):
                self.points.append(Vector2(x, y))
                if not prev_included:
                    self.edges.append(Vector2(x, y))
                    edge_angles.append(a_r)
                    prev_included = True
            elif prev_included:
                self.edges.append(self.points[-1])
                edge_angles.append(a_r - step_size)
                prev_included = False
        if len(edge_angles) % 2 == 1:
            raise ValueError("Weird number of kanten")
        self.paths = []
        for i in range(len(edge_angles)//2):
            a_1 = edge_angles[i*2]
            a_2 = edge_angles[i*2+1]
            rsmall = self.radius - ball_radius
            rlarge = self.radius + ball_radius
            x_range_small = SimpleInterval(math.cos(a_1)*rsmall +
                                           self.pos.x, math.cos(a_2)*rsmall+self.pos.x)
            x_range_large = SimpleInterval(math.cos(a_1)*rlarge +
                                           self.pos.x, math.cos(a_2)*rlarge+self.pos.x)
            self.paths.append(CirclePath(self.pos, rsmall,
                              x_range_small, self.y_range))
            self.paths.append(CirclePath(self.pos, rlarge,
                              x_range_large, self.y_range))
        for edge in self.edges:
            kante_x_range = SimpleInterval(
                edge.x-ball_radius, edge.x+ball_radius)
            kante_y_range = SimpleInterval(
                edge.y-ball_radius, edge.y+ball_radius)
            self.paths.append(CirclePath(
                edge, ball_radius, kante_x_range, kante_y_range))

    def draw(self, screen, color):
        # print(f"points: {self.points}")
        pygame.draw.lines(screen, color, False, self.points, width=3)
        # for kante in self.kanten:
        #     pygame.draw.circle(screen, color, kante, 50)

    def find_collision(self, kurve: FlugKurve):
        min_t = float("inf")
        for path in self.paths:
            coll_t = path.find_collision(kurve)
            if coll_t is None:
                continue
            min_t = min(min_t, coll_t)
        if min_t == float("inf"):
            return None
        return min_t
        # colls = []
        # check_outer_eq = ((kurve.x-self.pos.x)**2 +
        #                   (kurve.y-self.pos.y)**2 - (self.radius + kurve.r)**2)
        # coll_outer = check_outer_eq.find_smallest_root(
        #     multi_range, do_numeric=True)
        # if coll_outer is not None:
        #     colls.append(coll_outer)
        # check_inner_eq = ((kurve.x-self.pos.x)**2 +
        #                   (kurve.y-self.pos.y)**2 - (self.radius - kurve.r)**2)
        # coll_inner = check_inner_eq.find_smallest_root(
        #     multi_range, do_numeric=True)
        #
        # if coll_inner is not None:
        #     colls.append(coll_inner)
        # for kante in self.edges:
        #     check_kante = ((kurve.x-kante[0])**2 +
        #                    (kurve.y-kante[1])**2 - kurve.r**2)
        #     coll_kante = check_kante.find_smallest_root(
        #         multi_range, do_numeric=True)
        #     if coll_kante is not None:
        #         colls.append(coll_kante)
        #
        # if len(colls) == 0:
        #     return None
        # return min(colls)


class Ball:
    def __init__(self, pos, vel, radius, color):
        self.pos = pos
        self.radius = radius
        self.color = color
        self.vel = vel

    def draw(self):
        pygame.draw.circle(screen, self.color, self.pos, self.radius)

    def gen_flugbahn(self, ay, vx):
        t = Polynom([0, 1])
        x = t*vx + self.pos.x
        y = -((t**2)*ay*0.5) + self.pos.y
        return FlugKurve(x, y, self.radius)


a = Polynom([1, 2, 3])
b = Polynom([3, 4, 1, 1])
print((a-b).koefs)
print(((Polynom([1, 1, 1])**4)).koefs)
print(Polynom([0, 0, 0, 0, 1]).apply(Polynom([1, 1, 1])).koefs)
print(Polynom([1, 0, 0, 0, 0, 0, 0]).reduce())
print(Polynom([0, -15, -2, 1]).find_smallest_root(SimpleInterval(-10, 10)))
print(Polynom([30, -11, -4, 1]).find_smallest_root(SimpleInterval(-10, 10)))


# for i in range(1):
#    r = Polynom([31.92, -11.32, -4.32, 1]
#                ).smallest_root_bisect(Range(-100, 10), 10000)
# passed = time.time_ns()-start_time
# print(f"r: {r}, took: {passed/1000000} ms")
render = True
if render:
    # pygame setup
    pygame.init()
    screen = pygame.display.set_mode((1280, 720))
    clock = pygame.time.Clock()
    # clock.tick(60)  # limits FPS to 60
    running = True
    i = 0

    dt = 0.001
    # create ball
    ball = Ball(Vector2(100, 100), Vector2(200, 100), 50, "red")
    boden = CircleForm(Vector2(600, -600), 1200,
                       SimpleInterval(200, 1080), SimpleInterval(500, 700), 1000)
    bahn = ball.gen_flugbahn(-9.8, 6)
    start_time = time.time_ns()
    coll_t = boden.find_collision(bahn)
    passed = (time.time_ns() - start_time)/(10**6)
    print(f"calculating took {passed} ms")
    print(f"coll_t: {coll_t}")
    while running:
        # poll for events
        # pygame.QUIT event means the user clicked X to close your window
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        # fill the screen with a color to wipe away anything from last frame
        screen.fill("black")

        # ball.update(dt)
        passed = (time.time_ns() - start_time)/(10**9)
        ball.pos = bahn.get_pos(passed)
        if coll_t is not None and passed > coll_t:
            start_time = time.time_ns()
            ball.pos = bahn.get_pos(coll_t)
        # screen.fill("black")
        # boden.draw(screen, (0, 255, 0))
        # continue

        # RENDER YOUR GAME HERE
        boden.draw(screen, (0, 255, 0))
        ball.draw()
        # flip() the display to put your work on screen
        pygame.display.flip()
        i += 1
        clock.tick(60)

    pygame.quit()
