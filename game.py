"""
Defines the game class, which is the main class for the game. It handles the game loop, and the game state.
"""
from __future__ import annotations

import math
import time
from typing import Any, Callable, Dict, List, Set, Tuple
import pygame
from ballang_vars import VarHandler
import json

from objects.material import Material

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
    """
    Makes a rotating form
    """
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
    """
    Makes a flipper"""
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
    """
    Represents the state of the game
    """
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
    """
    The main class for the game
    
    Attributes:
    - curr_state (GameState): The current state of the game
    - coll_thread (CollThread): The thread for collision detection
    - curr_pressed (Set[int]): The currently pressed keys
    - speed (float): The inverse speed of the game
    - last_time (float): The time relative to which time is calculated
    - start_time (int): The time when the game started
    - on_keydown (Callable[[int, PinballGame], None]): The function to call when a key is pressed
    - on_update (Callable[[PinballGame], None]): The function to call when the game is updated
    - n_colls (int): The number of collisions that have happened
    """
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
            on_update = lambda game, screen: None
        self.last_time = 0
        self.start_time = time.time_ns()
        self.curr_state = start_state

        self.on_keydown = on_keydown
        self.on_update = on_update
        self.n_colls = 0
        self.speed = speed
        self.curr_pressed = set()
        self.file_vars = file_vars
        self.name = name
        if on_init is not None:
            on_init(self)
        self.coll_thread = CollThread(self.curr_state, form_functions=coll_fns)

    def calc_time(self):
        return self.last_time + (time.time_ns() - self.start_time)/(10**(self.speed))
    def pause(self):
        self.last_time = self.calc_time()
        self.start_time = time.time_ns()
        self.old_speed = self.speed
        self.speed = float("inf")

    def unpause(self):
        self.last_time = self.calc_time()
        self.start_time = time.time_ns()
        self.speed = self.old_speed
    
    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
                self.handle_keydown(event.key)
        elif event.type == pygame.KEYUP:
            self.handle_keyup(event.key)
    
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
        """
        Updates the game
        """
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


if __name__ == "__main__":
    # for generatong the json stuff for the moving flipper arms
    line = LineForm(Vec(200,950), Vec(260,990), 30, Material(1.1, 1.0, 40, 0))
    print("")
    print(json.dumps(make_flipper(line, Vec(200,950), -1.7, 0, 0.5, False, 0 ).get_json()))
    print("")
    print(json.dumps(make_flipper(line, Vec(200,950), -1.7, 0, 2, True, 0 ).get_json()))
    print("")

    line2 = LineForm(Vec(400,950), Vec(340,990), 30, Material(1.1, 1.0, 40, 0))
    print(json.dumps(make_flipper(line2, Vec(400,950), 1.7, 0, 0.5, False, 0 ).get_json()))
    print("")
    print(json.dumps(make_flipper(line2, Vec(400,950), 1.7, 0, 2, True, 0 ).get_json()))
    print("")