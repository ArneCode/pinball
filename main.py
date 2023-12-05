from __future__ import annotations
import time
import math
from typing import Tuple
import pygame
from pygame.math import Vector2
from interval import SimpleInterval, MultiInterval
import copy
from polynom import Polynom


class FlugKurve:
    def __init__(self, pos: Vec, r=5.0):
        self.pos = pos
        self.ball_r = r

    def get_pos(self, t):
        return Vec(self.pos.x.apply(t), self.pos.y.apply(t))

    def get_vel(self, t):
        x = self.pos.x.deriv().apply(t)
        y = self.pos.y.deriv().apply(t)
        return Vec(x, y)


class BoundingBox:
    def __init__(self, x_range: SimpleInterval, y_range: SimpleInterval):
        self.x_range = x_range
        self.y_range = y_range

    def times_inside(self, ball: Ball) -> MultiInterval | None:
        # find when ball enters/exits range
        rpos = SimpleInterval(0, float("inf"))  # positive real
        x_t_ranges = []
        x_min_colls = (
            ball.bahn.x - (self.x_range.min - ball.radius)).find_roots(rpos)
        x_max_colls = (
            ball.bahn.x - (self.x_range.max + ball.radius)).find_roots(rpos)

        x0 = ball.pos_0.x
        x_colls = x_min_colls + x_max_colls  # .sort()
        x_colls.sort()
        if x_colls is None or len(x_colls) == 0:
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
        # x_t_ranges.append(Range(prev_t, self.x_range.max))

        y_min_colls = (
            ball.bahn.y - (self.y_range.min - ball.radius)).find_roots(rpos)
        y_max_colls = (
            ball.bahn.y - (self.y_range.max + ball.radius)).find_roots(rpos)

        y_colls = y_min_colls + y_max_colls
        y_colls.sort()
        y0 = ball.pos_0.y

        prev_t = 0
        if not self.y_range.check(y0) and len(y_colls) > 0:
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
        multi_range = MultiInterval(t_ranges)  # anderen name wählen
        return multi_range


class Vec:
    def __init__(self, x, y) -> None:
        self.x = x
        self.y = y

    def __add__(self, other: Vec):
        x = self.x + other.x
        y = self.y + other.y
        return Vec(x, y)

    def __str__(self) -> str:
        return f"Vec({self.x}, {self.y})"

    def get_angle(self) -> float:
        return math.atan2(self.y, self.x)

    @staticmethod
    def from_angle(angle: float) -> Vec:
        return Vec(math.cos(angle), math.sin(angle))

    def __mul__(self, other) -> Vec:
        return Vec(other*self.x, other*self.y)

    def apply(self, v: float) -> Vec:
        if isinstance(self.x, Polynom) and isinstance(self.y, Polynom):
            return Vec(self.x.apply(v), self.y.apply(v))
        else:
            raise ValueError("can only apply to Polynom")

    def deriv(self) -> Vec:
        if isinstance(self.x, Polynom) and isinstance(self.y, Polynom):
            return Vec(self.x.deriv(), self.y.deriv())
        else:
            raise ValueError("can only derive polynom")

    def magnitude(self) -> float:
        return math.sqrt(self.x**2+self.y**2)

    def normalize(self) -> Vec:
        return self*(1/self.magnitude())


class Collision:
    time: float
    bahn: Vec
    obj: CirclePath  # replace with interface

    def __init__(self, time: float, bahn: Vec, obj: CirclePath):
        self.time = time
        self.bahn = bahn
        self.obj = obj

    def get_result_dir(self) -> Vec:
        normal = self.obj.get_normal(self.bahn.apply(self.time))
        vel_before = self.bahn.deriv().apply(self.time)

        normal_angle = normal.get_angle()
        vel_angle = vel_before.get_angle()
        diff = normal_angle - vel_angle

        result_angle = vel_angle + 2*diff

        vel_before_mag = vel_before.magnitude()


        # return normal*vel_before.magnitude()
        return Vec.from_angle(result_angle)*vel_before_mag*(-1)


class CirclePath:
    def __init__(self, pos: Vector2, radius, x_range, y_range, name=""):
        self.pos = pos
        self.radius = radius
        self.bound = BoundingBox(x_range, y_range)
        self.points = []
        self.name = name

        resolution = 1000
        step_size = 2*math.pi/resolution
        for i in range(resolution):
            a_r = i*step_size
            x = math.cos(a_r)*radius + pos.x
            y = math.sin(a_r)*radius + pos.y
            if x_range.check(x) and y_range.check(y):
                self.points.append((x, y))

    def get_normal(self, pos: Vec) -> Vec:
        steep = -(pos.x - self.pos.x)/(pos.y-self.pos.y)
        m = -1/steep
        return Vec(1, m).normalize()

    def draw(self, screen, color):
        pygame.draw.lines(screen, color, False, self.points, width=1)

    def find_collision(self, ball: Ball) -> Collision | None:
        # TODO: restrict searched t by already found!
        t_range = self.bound.times_inside(ball)
        check_eq = ((ball.bahn.x-self.pos.x)**2 +
                    (ball.bahn.y-self.pos.y)**2 - (self.radius)**2)
        coll = check_eq.find_roots(
            t_range, return_smallest=True, do_numeric=True)
        if len(coll) > 0:
            return Collision(coll[0], ball.bahn, self)
        return None


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
                              x_range_small, self.y_range, "large_inner"))
            self.paths.append(CirclePath(self.pos, rlarge,
                              x_range_large, self.y_range, "large_outer"))
        for edge in self.edges:
            kante_x_range = SimpleInterval(
                edge.x-ball_radius, edge.x+ball_radius)
            kante_y_range = SimpleInterval(
                edge.y-ball_radius, edge.y+ball_radius)
            self.paths.append(CirclePath(
                edge, ball_radius, kante_x_range, kante_y_range, "kant"))

    def draw(self, screen, color):
        pygame.draw.lines(screen, color, False, self.points, width=3)
        for kante in self.paths:
            # pygame.draw.circle(screen, color, kante, 50)
            kante.draw(screen, color)

    def find_collision(self, ball: Ball):
        first_coll = None
        i = 0
        for path in self.paths:
            coll = path.find_collision(ball)
            if coll is None:
                continue
            if first_coll is None or coll.time < first_coll.time:
                first_coll = coll
            i += 1
        if first_coll == float("inf"):
            return None
        return first_coll


class Ball:
    pos_0: Vec
    bahn: Vec
    radius: float
    color: Tuple[int]
    start_t: float

    def __init__(self, pos, radius, color):
        self.pos_0 = pos
        self.radius = radius
        self.color = color
        self.vel_0 = Vec(0.0, 0.0)
        self.acc = Vec(0.0, 0.0)
        self.bahn = Vec(0.0, 0.0)
        self.start_t = 0

    def get_pos(self, t: float) -> Vec:
        return self.bahn.apply(t-self.start_t)

    def draw(self, t):
        pos = self.get_pos(t)
        pygame.draw.circle(screen, self.color,
                           (pos.x, pos.y), self.radius)

    def update_bahn(self):
        t = Polynom([0, 1])
        self.bahn = self.acc*0.5*(t**2)+self.vel_0*t+self.pos_0

    def with_acc(self, acc: Vec):
        new = copy.copy(self)
        new.acc = acc
        new.update_bahn()
        return new

    def with_vel(self, vel: Vec):
        new = copy.copy(self)
        new.vel_0 = vel
        new.update_bahn()
        return new

    def with_start_pos(self, pos: Vec):
        new = copy.copy(self)
        new.pos_0 = pos
        new.update_bahn()
        return new

    def with_start_t(self, start_t: float):
        new = copy.copy(self)
        new.start_t = start_t
        return new


a = Polynom([1, 2, 3])
b = Polynom([3, 4, 1, 1])
print((a-b).koefs)
print(((Polynom([1, 1, 1])**4)).koefs)
print(Polynom([0, 0, 0, 0, 1]).apply(Polynom([1, 1, 1])).koefs)
print(Polynom([1, 0, 0, 0, 0, 0, 0]).reduce())
print(Polynom([0, -15, -2, 1]).find_roots(SimpleInterval(-10, 10)))
print(Polynom([30, -11, -4, 1]).find_roots(SimpleInterval(-10, 10)))


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
    ball = Ball(Vector2(100, 100), 50, "red").with_acc(Vec(0, 90.8)).with_vel(Vec(
        120.0, 0
    ))
    boden = CircleForm(Vector2(600, 1600), 1200,
                       SimpleInterval(200, 1080), SimpleInterval(100, 700), 1000)
    # bahn = ball.gen_flugbahn(-9.8, 6)
    start_time = time.time_ns()
    coll = boden.find_collision(ball)
    passed = (time.time_ns() - start_time)/(10**6)
    print(f"calculating took {passed} ms")
    print(f"coll_t: {coll}")
    while running:
        # poll for events
        # pygame.QUIT event means the user clicked X to close your window
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        # fill the screen with a color to wipe away anything from last frame
        screen.fill("black")

        # ball.update(dt)
        passed = (time.time_ns() - start_time)/(10**(8.7))
        # ball.pos_0 = bahn.get_pos(passed)
        if coll is not None and passed > coll.time + ball.start_t:
            dir = coll.get_result_dir()  # *(-50)
            ball = ball.with_start_t(passed).with_start_pos(
                ball.get_pos(coll.time+ball.start_t - 0.001)).with_vel(dir*(0.8))  # .with_acc(Vec(0.0, 0.0))
            print(f"ball pos: {ball.pos_0}, actually: {ball.get_pos(passed)}")
            coll = boden.find_collision(ball)
            print(f"found coll: {coll}")

        # screen.fill("black")
        # boden.draw(screen, (0, 255, 0))
        # continue

        # RENDER YOUR GAME HERE
        boden.draw(screen, (0, 255, 0))
        ball.draw(passed)
        # flip() the display to put your work on screen
        pygame.display.flip()
        i += 1
        clock.tick(60)

    pygame.quit()
