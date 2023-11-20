import time
import math
import numbers
# Example file showing a basic pygame "game loop"
import pygame
from pygame.math import Vector2

render = True
if render:
    # pygame setup
    pygame.init()
    screen = pygame.display.set_mode((1280, 720))
    clock = pygame.time.Clock()
    running = True


class Range:
    def __init__(self, min, max, l_inclusive=True, r_inclusive=False):
        self.min = min
        self.max = max
        self.l_inclusive = l_inclusive
        self.r_inclusive = r_inclusive

    def check(self, v):
        return ((self.l_inclusive and v >= self.min) or (v > self.min)) and ((self.r_inclusive and v <= self.max) or (v < self.max))


class Polynom:
    def __init__(self, koefs):
        self.koefs = koefs
        # Ball class

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
        if len(self.koefs) > len(other.koefs):
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
        max_exp = len(exps) - 1
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

    def __len__(self):
        return len(self.koefs)

    def find_roots(self):
        print(f"finding roots: {self}")
        this = self.reduce()
        if len(this) < 2:
            raise ValueError(f"cannot find the roots of: {this}")
        if len(this) == 2:
            a = self.koefs[0]
            b = self.koefs[1]
            return [-a/b]
        if math.isclose(this.koefs[0], 0.0, abs_tol=1e-6):  # satz vom Nullprodukt
            roots_svn = Polynom(self.koefs[1:]).find_roots()
            roots_svn.append(0)
            return roots_svn
        if len(this) == 3:  # Mitternachtsformel
            a = self.koefs[2]
            b = self.koefs[1]
            c = self.koefs[0]
            root = math.sqrt(b**2-4*a*c)
            x1 = (-b + root)/(2*a)
            x2 = (-b - root)/(2*a)
            return [x1, x2]

    def roots_bisect(self, minx, maxx, steps=100):
        """
        find roots using the bisection method
        """
        roots = []
        i_len = maxx - minx
        step = i_len / steps
        prev_x = None
        prev_y = None
        for i in range(0, steps):
            x = minx + i*step
            y = self.apply(x)
            if i > 0 and prev_y < 0 and y >= 0:
                roots.append(self.root_bisect(prev_x, x))
            elif i > 0 and prev_y >= 0 and y < 0:
                roots.append(self.root_bisect(x, prev_x))
            prev_x = x
            prev_y = y
        return roots

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


class PolyEq:
    def __init__(self, xs: Polynom, ys: Polynom) -> None:
        self.xs = xs
        self.ys = ys


class Ball:
    def __init__(self, pos, vel, radius, color):
        self.pos = pos
        self.radius = radius
        self.color = color
        self.vel = vel

    def draw(self):
        pygame.draw.circle(screen, self.color, self.pos, self.radius)

    def update(self, dt):
        self.pos += self.vel * dt
        if self.pos.x < self.radius:
            self.pos.x = self.radius
            self.vel.x *= -1
        if self.pos.x > 1280 - self.radius:
            self.pos.x = 1280 - self.radius
            self.vel.x *= -1
        if self.pos.y < self.radius:
            self.pos.y = self.radius
            self.vel.y *= -1
        if self.pos.y > 720 - self.radius:
            self.pos.y = 720 - self.radius
            self.vel.y *= -1


a = Polynom([1, 2, 3])
b = Polynom([3, 4, 1, 1])
print((a-b).koefs)
print(((Polynom([1, 1, 1])**4)).koefs)
print(Polynom([0, 0, 0, 0, 1]).apply(Polynom([1, 1, 1])).koefs)
print(Polynom([1, 0, 0, 0, 0, 0, 0]).reduce())
print(Polynom([0, -15, -2, 1]).find_roots())
print(Polynom([30, -11, -4, 1]).roots_bisect(-10, 10, 1000))

start_time = time.time_ns()
for i in range(1000):
    r = Polynom([31.92, -11.32, -4.32, 1]).roots_bisect(-10, 10, 1000)
passed = time.time_ns()-start_time
print(f"r: {r}, took: {passed/1000000} ms")

if render:
    dt = 0.001
    # create ball
    ball = Ball(Vector2(100, 100), Vector2(200, 100), 50, "red")
    while running:
        dt = clock.tick(60)/1000  # limits FPS to 60
        # poll for events
        # pygame.QUIT event means the user clicked X to close your window
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        # fill the screen with a color to wipe away anything from last frame
        screen.fill("black")

        ball.update(dt)

        # RENDER YOUR GAME HERE
        ball.draw()

        # flip() the display to put your work on screen
        pygame.display.flip()

    pygame.quit()
