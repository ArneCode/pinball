from __future__ import annotations

import math
import time
from typing import Any, Callable, Dict, List, Set, Tuple
import pygame
from ballang_vars import VarHandler

from collision.coll_thread import ChangeInfo, CollThread
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

class GameState:
    forms: FormHandler
    balls: List[Ball]
    ballang_vars: VarHandler

    is_end: bool

    def __init__(self, forms: FormHandler, balls: List[Ball], ballang_vars: VarHandler, is_end: bool = False):
        self.forms = forms
        self.balls = balls
        self.ballang_vars = ballang_vars

        self.is_end = is_end
    
    def draw(self, screen, time):
        self.forms.draw(screen, (0, 255, 0), time)
        for ball in self.balls:
            ball.get_form().draw(screen, ball.color, time)
            ball.draw(time, screen)
class PinballGame:
    curr_state: GameState
    coll_thread: CollThread
    curr_pressed: Set[int]
    speed: float
    last_time: float
    start_time: int
    on_keydown: Callable[[int, PinballGame], None]
    on_update: Callable[[PinballGame], None]
    n_colls: int
    file_vars: Dict[str, Any]
    name: str

    def __init__(self, start_state: GameState, on_keydown = None, on_update = None, on_init = None ,speed: float = 8.0, coll_fns: Dict[str, Callable[[GameState, float, int, ChangeInfo], None]] = {}, file_vars: Dict[str, Any] = {}, name: str = "PinballGame"):
        if on_keydown is None:
            on_keydown = lambda key, game: None
        if on_update is None:
            on_update = lambda game: None
        self.last_time = 0
        self.start_time = time.time_ns()
        self.curr_state = start_state
        self.speed = speed
        self.file_vars = file_vars
        self.name = name

        if on_init is not None:
            on_init(self)
        self.coll_thread = CollThread(self.curr_state, form_functions=coll_fns)
        self.on_keydown = on_keydown
        self.on_update = on_update
        self.n_colls = 0
        self.curr_pressed = set()

    def calc_time(self):
        return self.last_time + (time.time_ns() - self.start_time)/(10**(self.speed))

    def handle_keydown(self, key: int):
        self.curr_pressed.add(key)
        self.on_keydown(self, key)

    def handle_keyup(self, key):
        self.curr_pressed.remove(key)
    def restart_colls(self, t: float):
        #print(f"restarting colls, self.balls: {self.balls}, self.curr_forms: {self.curr_forms}, t: {t}")
        self.coll_thread.restart(self.curr_state, t)
        print("thread restarted")
        new_state = self.coll_thread.check_coll(t, None)
        if new_state is not None:
            self.curr_state, n_looped = new_state
            self.n_colls += n_looped

    def update(self, screen):
        # print(f"speed: {speed}, n_colls: {n_colls}, queue size: {coll_thread.get_curr_queue().qsize()}")
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                self.coll_thread.stop()
                return False
            elif event.type == pygame.KEYDOWN:
                self.handle_keydown(event.key)
            elif event.type == pygame.KEYUP:
                self.handle_keyup(event.key)

            # coll_process.join()
        # fill the screen with a color to wipe away anything from last frame
        screen.fill("black")
        self.curr_state.draw(screen, self.calc_time())
        passed = self.calc_time()
        new_state = self.coll_thread.check_coll(passed)
        lagging_behind = None
        self.on_update(self, screen)
        if new_state is not None:
            self.curr_state, n_looped = new_state
            self.n_colls += n_looped
        if self.curr_state.is_end:
            return False
        return True
        # flip() the display to put your work on screen
