from __future__ import annotations

import math
import time
from typing import Callable, List, Set, Tuple
import pygame

from collision.coll_thread import CollThread
from math_utils.vec import Vec
from objects.ball import Ball
from objects.form import Form
from objects.formhandler import FormHandler
from objects.forms.lineform import LineForm
from objects.forms.periodicform import PeriodicForm
from objects.forms.rotateform import RotateForm
from objects.forms.tempform import TempForm


def make_rotating(form: Form, rot_point: Vec, period: float):
    n_subforms = 5
    step_size = 2*math.pi/n_subforms
    step_duration = period/n_subforms
    subforms: List[Tuple[Form, float]] = []
    for i in range(n_subforms):
        angle = 2*math.pi*i/n_subforms
        sub_form = form.rotate(angle, rot_point)
        rotating_sub_form = RotateForm(
            sub_form, rot_point, 0.0, step_size/step_duration, 0)
        subforms.append((rotating_sub_form, step_duration))
    return PeriodicForm(subforms)


def make_flipper(line: LineForm, rot_point: Vec, up_angle: float, down_angle: float, turn_duration: float, curr_up: bool, curr_time: float = 0):
    up_line = line.rotate(up_angle, rot_point)
    down_line = line.rotate(down_angle, rot_point)

    speed = (up_angle - down_angle)/turn_duration

    if curr_up:
        rotating_line = RotateForm(up_line, rot_point, -0.0, -speed, curr_time)
        return TempForm(rotating_line, turn_duration + curr_time, down_line)
    else:
        rotating_line = RotateForm(
            down_line, rot_point, -0.0, speed, curr_time)
        return TempForm(rotating_line, turn_duration + curr_time, up_line)


class PinballGame:
    coll_thread: CollThread
    curr_pressed: Set[int]
    speed: float
    last_time: float
    start_time: int
    curr_forms: FormHandler
    balls: List[Ball]
    on_keydown: Callable[[int, PinballGame], None]
    on_update: Callable[[PinballGame], None]
    n_colls: int

    def __init__(self, start_forms: FormHandler, balls: List[Ball], on_keydown, on_update, speed: float = 8.0):
        print("a")
        self.coll_thread = CollThread(balls, start_forms)
        print("b")
        self.last_time = 0
        self.start_time = time.time_ns()
        self.curr_forms = start_forms
        self.balls = balls
        self.on_keydown = on_keydown
        self.on_update = on_update
        self.n_colls = 0
        self.speed = speed
        self.curr_pressed = set()

    def calc_time(self):
        return self.last_time + (time.time_ns() - self.start_time)/(10**(self.speed))
    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
                self.handle_keydown(event.key)
        elif event.type == pygame.KEYUP:
            self.handle_keyup(event.key)
    def handle_keydown(self, key: int):
        self.curr_pressed.add(key)
        self.on_keydown(key, self)

    def handle_keyup(self, key):
        self.curr_pressed.remove(key)
    def update(self, screen):
        #print(f"pinballgame update, args: self: {self}, screen: {screen}")
        # print(f"speed: {speed}, n_colls: {n_colls}, queue size: {coll_thread.get_curr_queue().qsize()}")
        
        self.on_update(self)

        if pygame.K_s in self.curr_pressed:
            self.speed += 0.01
        if pygame.K_f in self.curr_pressed:
            self.speed -= 0.01

            # coll_process.join()
        # fill the screen with a color to wipe away anything from last frame
        screen.fill("black")

        passed = self.calc_time()
        print(
            f"passed: {passed}, queue size: {self.coll_thread.get_curr_queue().qsize()}")
        for ball in self.balls:
            vel = ball.bahn.deriv().apply(passed)
            print(f"vel: {vel}")
        self.curr_forms.draw(screen, (0, 255, 0), passed)
        print(
            f"forms drawn, queue size: {self.coll_thread.get_curr_queue().qsize()}")
        curr_state = self.coll_thread.check_coll(passed)
        lagging_behind = None
        if curr_state is not None:
            self.balls, self.curr_forms, lagging_behind, n_looped = curr_state
            self.n_colls += n_looped

        for ball in self.balls:
            ball.get_form().draw(screen, ball.color, passed)
            ball.draw(passed, screen)
            print("ball drawn")
        return True
        # flip() the display to put your work on screen
