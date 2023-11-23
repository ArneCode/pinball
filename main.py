import time
import math
import numbers
# Example file showing a basic pygame "game loop"
import pygame
from pygame.math import Vector2


class RangeIter:
    def __init__(self, range, n_steps):
        self.range = range
        self.n_steps = n_steps

    def __iter__(self):
        self.i = 0
        return self

    def __next__(self):
        if self.i > self.n_steps:
            raise StopIteration
        step_size = (self.range.max-self.range.min)/self.n_steps
        result = self.range.min + step_size*self.i
        self.i += 1
        return result


class Range:
    def __init__(self, min, max, l_inclusive=True, r_inclusive=False):
        self.min = min
        self.max = max
        self.l_inclusive = l_inclusive
        self.r_inclusive = r_inclusive

    def get_size(self):
        return self.max - self.min

    def restrict_max(self, new_max):
        # maybe it would be smarter to also have an option to change the inclusivity, but I currently dont see a reason for that
        return Range(self.min, min(new_max, self.max), self.l_inclusive, self.r_inclusive)

    def restrict_min(self, new_min):
        return Range(max(self.min, new_min), self.max, self)

    def check(self, v):
        return ((self.l_inclusive and v >= self.min) or (v > self.min)) and ((self.r_inclusive and v <= self.max) or (v < self.max))

    def step_through(self, n_steps):
        return RangeIter(self, n_steps)

    def intersect(self, other):
        print(
            f"intersect range {{{self.min} to {self.max}}}, {{{other.min} to {other.max}}}")
        if self.min <= other.min:
            links = self
            rechts = other
        else:
            links = other
            rechts = self
        if links.max <= rechts.min:
            return None
        return Range(rechts.min, min(links.max, rechts.max))


class MultiRangeIter:
    def __init__(self, multi_range, n_steps):
        self.multi_range = multi_range
        self.n_steps = n_steps
        self.range_step_i = 0
        self.range_n = 0

    def __iter__(self):
        return self

    def __next__(self):
        if self.range_n > len(self.multi_range.ranges):
            raise StopIteration
        size_per_step = self.multi_range.size / self.n_steps
        curr_range = self.multi_range.ranges[self.range_n]
        x = curr_range.min + self.range_step_i*size_per_step
        if x > curr_range.min:
            self.range_step_i = 0
            self.range_n += 1
            return next(self)
        self.range_step_i += 1
        return x


class MultiRange:
    def __init__(self, ranges):
        size = 0
        for range in ranges:
            size += range.get_size()
        self.size = size
        self.ranges = ranges

    def step_through(self, n_steps):
        print("stepping through multirange")
        return MultiRangeIter(self, n_steps)

    def check(self, v):
        for r in self.ranges:
            if r.check(v):
                return True
        return False


class Polynom:
    def __init__(self, koefs):
        self.koefs = koefs
        self.grad = len(self.koefs) - 1

    def deriv(self):
        new_koeffs = []
        for (exp, koeff) in enumerate(self.koefs):
            if exp == 0:
                continue
            new_koeffs.push(koeff*exp)
        return Polynom(new_koeffs)

    def __add__(self, other):
        if isinstance(other, numbers.Number):
            other = Polynom([other])
        if type(other) != Polynom:
            raise TypeError(
                f"expected Polynom or Number, but got {type(other)}: {other}")
        if self.grad > other.grad:
            l = self.koefs
            s = other.koefs
        else:
            l = other.koefs
            s = self.koefs
        new_koeffs = l.copy()
        for (i, k) in enumerate(s):
            new_koeffs[i] += k
        return Polynom(new_koeffs)

    def __neg__(self):
        return Polynom(list(map(lambda k: -k, self.koefs)))

    def __sub__(self, other):
        return self + (-other)

    def __mul__(self, other):
        if not isinstance(other, numbers.Number):
            raise TypeError(f"got weird other: {other}, type: {type(other)}")
        new_koeffs = [0]*len(self.koefs)
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

    def reduce(self):
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

    def grad(self):
        return len(self.koefs)

    def find_smallest_root(self, x_range: Range = None, return_list=False, do_numeric=False):
        print(f"finding roots: {self}")
        this = self.reduce()
        if this.grad < 1:
            raise ValueError(f"cannot find the roots of: {this}")
        if this.grad == 1:
            a = self.koefs[0]
            b = self.koefs[1]
            result = -a/b
            if return_list:
                return result if x_range is None else list(filter(x_range.check, [result]))
            return result if x_range is None or x_range.check(result) else None
        #    if math.isclose(this.koefs[0], 0.0, abs_tol=1e-6):  # satz vom Nullprodukt, nicht wahrscheinlich, dass es vorkommt, da es eine Kollision direkt am Anfang der Flugbahn bedeutet
        #        roots_svn = Polynom(self.koefs[1:]).find_roots(
        #            x_range.restrict_max(0))
        #        roots_svn.append(0)
        #        return roots_svn
        if this.grad == 2:  # Mitternachtsformel
            a = self.koefs[2]
            b = self.koefs[1]
            c = self.koefs[0]
            root = math.sqrt(b**2-4*a*c)
            x1 = (-b + root)/(2*a)
            x2 = (-b - root)/(2*a)
            result = filter(x_range.check, [x1, x2])
            if return_list:
                return list(result)
            return min(result) if result else None
        if do_numeric:
            return self.smallest_root_bisect(x_range, return_list=return_list)

    def smallest_root_bisect(self, x_range: Range, n_steps=1000, return_list=False):
        """
        find roots using the bisection method
        """
        prev_x = None
        prev_y = None
        if return_list:
            results = []
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


class CircleForm:
    def __init__(self, pos: Vector2, radius, x_range: Range, y_range: Range, resolution=100) -> None:
        self.pos = pos
        self.radius = radius
        self.x_range = x_range
        self.y_range = y_range
        self.points = []
        for i in range(resolution):
            a_r = i*2*math.pi/resolution
            x = math.cos(a_r)
            y = math.sin(a_r)
            if x_range.check(x) and y_range.check(y):
                self.points.append((x, y))

    def draw(self, screen, color):
        pygame.draw.circle(screen, color, self.pos, self.radius, width=3)

    def find_collision(self, kurve: FlugKurve):
        # find when ball enters/exits range
        rpos = Range(0, float("inf"))  # positive real
        x_t_ranges = []
        x_min_colls = (
            kurve.x - self.x_range.min).find_smallest_root(rpos, return_list=True)
        x_max_colls = (
            kurve.x - self.x_range.max).find_smallest_root(rpos, return_list=True)

        x0 = kurve.x.apply(0)
        x_colls = x_min_colls + x_max_colls  # .sort()
        x_colls.sort()
        print(f"x_cols: {x_colls}")
        if x_colls is None or len(x_colls) == 0:
            print(f"x_colls is None, min: {x_min_colls}, max: {x_max_colls}")
            return None
        prev_t = 0

        if not self.x_range.check(x0):
            prev_t = x_colls.pop()
        for (i, t) in enumerate(x_colls):
            if i % 2 == 0:
                x_t_ranges.append(Range(prev_t, t))
                prev_t = None
            else:
                prev_t = t
        if prev_t is not None:
            raise ValueError("Hmmmmm, sollte nicht passieren")
        print(f"{len(x_t_ranges)} x_t_ranges")
        # x_t_ranges.append(Range(prev_t, self.x_range.max))

        y_min_colls = (
            kurve.y - self.y_range.min).find_smallest_root(rpos, return_list=True)
        y_max_colls = (
            kurve.y - self.y_range.max).find_smallest_root(rpos, return_list=True)

        y_colls = y_min_colls + y_max_colls
        y_colls.sort()
        print(f"y_colls: {y_colls}")
        y0 = kurve.y.apply(0)

        prev_t = 0
        if not self.y_range.check(y0):
            prev_t = y_colls.pop()
        t_ranges = []
        x_rang_i = 0

        for (i, t) in enumerate(y_colls):
            if i % 2 == 0:
                y_range = Range(prev_t, t)
                x_i = 0
                while x_i < len(x_t_ranges):
                    intersect = y_range.intersect(x_t_ranges[x_i])
                    if intersect is None:
                        break
                    t_ranges.append(intersect)
                    x_i += 1

                prev_t = None
            else:
                prev_t = t
        print(f"found {len(t_ranges)} ranges")
        multi_range = MultiRange(t_ranges)  # anderen name wählen
        check_outer_eq = ((kurve.x-self.pos.x)**2 +
                          (kurve.y-self.pos.y)**2 - (self.radius + kurve.r)**2)
        coll_outer = check_outer_eq.find_smallest_root(
            multi_range, do_numeric=True)

        check_inner_eq = ((kurve.x-self.pos.x)**2 +
                          (kurve.y-self.pos.y)**2 - (self.radius - kurve.r)**2)
        coll_inner = check_inner_eq.find_smallest_root(
            multi_range, do_numeric=True)

        if coll_outer is None:
            return coll_inner
        if coll_inner is None:
            return coll_outer
        return min(coll_inner, coll_outer)


class PolyForm:
    def __init__(self, poly: Polynom, range: Range, resolution=100):
        self.poly = poly
        print(f"poly: {poly}")
        self.range = range
        points = []
        for x in range.step_through(resolution):
            y = self.poly.apply(x)
            points.append((x, y))
        self.points = points

    def draw(self, screen, color):
        pygame.draw.polygon(screen, color, self.points, 3)

    def find_collision(self, kurve: FlugKurve):
        assert kurve.x.grad < 3
        min_eq = kurve.x - (self.range.min - kurve.r)
        tmin = min_eq.find_smallest_root(Range(0, float("inf"))) or 0
        tmax = (kurve.x - (self.range.max + kurve.r)
                ).find_smallest_root(Range(0, float('inf'))) or float("inf")
        print(f"tmin: {tmin}, tmax: {tmax}, min_eq: {min_eq}")

        kugel_gleichung = (kurve.x)**2 + (yp - kurve.y)**2 - kurve.r**2
        return kugel_gleichung.find_smallest_root(Range(tmin, tmax))


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
print(Polynom([0, -15, -2, 1]).find_smallest_root(Range(-10, 10)))
print(Polynom([30, -11, -4, 1]).find_smallest_root(Range(-10, 10)))


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
    ball = Ball(Vector2(100, 100), Vector2(200, 100), 20, "red")
    boden = CircleForm(Vector2(600, -600), 1200,
                       Range(0, 1280), Range(400, 700), 1000)
    bahn = ball.gen_flugbahn(-9.8, 100)
    start_time = time.time_ns()
    coll_t = boden.find_collision(bahn)
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
        passed = (time.time_ns() - start_time)/(10**8)
        ball.pos = bahn.get_pos(passed)
        if passed > coll_t:
            start_time = time.time_ns()
            # screen.fill("black")
            # boden.draw(screen, (0, 255, 0))
            continue

        # RENDER YOUR GAME HERE
        ball.draw()
        boden.draw(screen, (0, 255, 0))
        # flip() the display to put your work on screen
        pygame.display.flip()
        i += 1
        clock.tick(60)

    pygame.quit()
