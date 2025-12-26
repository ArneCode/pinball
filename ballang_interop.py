"""
Prepare functions for running ballang code from python
"""
import json
import time
from typing import Dict, List, Set

import pygame
from collision.coll_thread import ChangeInfo
from game import GameState, PinballGame
from math_utils.vec import Vec
from objects.ball import Ball
from ballang import parse_file
from ballang.eval_visitor import Function, Value
from objects.formhandler import FormHandler
from objects.forms.timedform import TimedForm

# Arduino, unwichtig
hardware_connected = False #!!!WICHTIG!!! Ist False für Tastatur only und True wenn man den Arduinobasierten controller benutzen möchte
if hardware_connected:
    from hardware import Hardware
    com_port = "/dev/ttyACM0" # !!!WICHTIG!!! Muss je nach PC, BEtriebssystem und Port geändert werden.
    hardware1 = Hardware(com_port, 115200, 0.0005)
else:
    hardware1 = None

def get_state_functions(state: GameState, change_info: ChangeInfo) -> Dict:
    """
    Returns a dictionary of functions that can be called from ballang code
    """
    def read_global(name: str) -> Value:
        return state.ballang_vars.get_var(name)
    def is_defined(name: str) -> bool:
        return state.ballang_vars.is_defined(name)
    def set_global(name: str, value: Value, time: float) -> None:
        state.ballang_vars.set_var(name, value, time)
        change_info.set_globals_changed()

    def remove_named_form(name: str) -> None:
        state.forms = state.forms.copy()
        state.forms.remove_named_form(name)
        change_info.set_forms_changed()

    def hide_named_form(name: str) -> None:
        state.forms = state.forms.copy()
        state.forms.hide_named_form(name)
        change_info.set_forms_changed()

    def show_named_form(name: str, scene_name: str) -> None:
        state.forms = state.forms.copy()
        form = state.forms.get_hidden_form(name)
        assert form is not None, f"show_named_form: form with name {name} not found"
        state.forms.set_named_form(scene_name, form)
        change_info.set_forms_changed()

    def spawn_form_timed(hidden_name: str, scene_name: str, time: int):
        state.forms = state.forms.copy()
        form = state.forms.get_hidden_form(hidden_name)
        assert form is not None, f"spawn_form_timed: form with name {hidden_name} not found"
        timed_form = TimedForm(form, time)
        state.forms.set_named_form(scene_name, timed_form)
        change_info.set_forms_changed()

    def remove_ball(ball_id: int) -> None:
        for i, ball in enumerate(state.balls):
            if i == ball_id:
                state.balls = state.balls[:i] + state.balls[i+1:]
                change_info.set_balls_changed()
                return
        raise Exception(f"ball with id {ball_id} not found")
    
    def spawn_ball(pos: Vec, vel: Vec, acc: Vec, time: float):
        ball_radius = state.balls[0].radius
        ball = Ball(pos, ball_radius, (255, 0,0) ).with_vel(vel).with_acc(acc).with_start_t(time)
        id = len(state.balls)
        state.balls.append(ball)
        change_info.set_balls_changed()
        return id
    
    def set_ball_acc(ball_id: int, acc: Vec) -> None:
        state.balls = state.balls.copy()
        state.balls[ball_id].acc = acc
        change_info.set_balls_changed()
    def get_ball_acc(ball_id: int) -> Vec:
        return state.balls[ball_id].acc
    
    def increase_ball_acc(ball_id: int, acc: Vec) -> None:
        state.balls = state.balls.copy()
        state.balls[ball_id].acc += acc
        change_info.set_balls_changed()
    
    def decrease_ball_acc(ball_id: int, acc: Vec) -> None:
        state.balls = state.balls.copy()
        state.balls[ball_id].acc -= acc
        change_info.set_balls_changed()

    def is_moving(name: str, time: float = 0.0):

        form = state.forms.get_named_form(name)
        assert form is not None, f"is_moving: form with name {name} not found"
        return form.is_moving(time)
    def to_str(val: Value):
        return str(val)
    def get_vec(x: float,y: float):
        return Vec(x,y)

    funcs = {
        "read_global": read_global,
        "is_defined": is_defined,
        "set_global": set_global,
        "remove_ball": remove_ball,
        "set_ball_acc": set_ball_acc,
        "get_ball_acc": get_ball_acc,
        "increase_ball_acc": increase_ball_acc,
        "decrease_ball_acc": decrease_ball_acc,
        "print": print,
        "remove_named_form": remove_named_form,
        "hide_named_form": hide_named_form,
        "show_named_form": show_named_form,
        "spawn_form_timed": spawn_form_timed,
        "is_moving": is_moving,
        "str": to_str,
        "Vec": get_vec,
        "spawn_ball": spawn_ball
    }
    return funcs

def get_screen_functions(screen) -> Dict:
    """
    Returns screen functions that can be called from ballang code
    """
    def show_text(text: str, x: float, y: float, size: int):
        font = pygame.font.Font(None, int(size))
        text = font.render(text, True, (255, 255, 255))
        screen.blit(text, (x, y))
    funcs = {
        "show_text": show_text,
    }
    return funcs
def get_update_functions(game: PinballGame) -> Dict:
    """
    Returns ballang function that can be called from an update context
    """

    def is_key_pressed(key: int):
        return key in game.curr_pressed

    def calc_time():
        return game.calc_time()

    def restart_colls(t: float):
        game.restart_colls(t)

    def increase_speed(amnt: float):
        game.last_time = game.calc_time()
        game.start_time = time.time_ns()
        game.speed -= amnt
    
    def decrease_speed(amnt: float):
        game.last_time = game.calc_time()
        game.start_time = time.time_ns()
        game.speed += amnt

    def read_file_var(name: str):
        return game.file_vars.get(name)
    
    def file_var_exists(name: str):
        return name in game.file_vars
    
    def set_file_var(name: str, value):
        game.file_vars[name] = value
        file_name = f"{game.name}.json"
        with open(file_name, "w") as f:
            json.dump(game.file_vars, f)
    
    def play_sound(path: str):
        pygame.mixer.Sound(path).play()
    
    def play_sound_loop(path: str):
        pygame.mixer.Sound(path).play(-1)


    funcs = {
        "print": print,
        "is_key_pressed": is_key_pressed,
        "calc_time": calc_time,
        "restart_colls": restart_colls,
        "increase_speed": increase_speed,
        "decrease_speed": decrease_speed,
        "read_file_var": read_file_var,
        "file_var_exists": file_var_exists,
        "set_file_var": set_file_var,
        "play_sound": play_sound,
        "play_sound_loop": play_sound_loop,
        "hardware_collect_input": hardware_get_input,
        "hardware_get_l":hardware_check_l,
        "hardware_get_r":hardware_check_r,
        "hardware_get_power":hardware_check_power,
    }
    funcs.update(get_state_functions(game.curr_state, ChangeInfo()))
    return funcs



def prepare_update_function(file: str, function_name: str):
    """
    Prepare a function that can be called to run a ballang function from python
    """
    def run_update_function(game: PinballGame, screen: pygame.Surface):
        funcs = get_update_functions(game)
        funcs.update(get_screen_functions(screen))
        ballang_funcs = parse_file(file, funcs)
        on_update = ballang_funcs.get(function_name)
        assert on_update is not None, f"function {function_name} not found"
        on_update()
    return run_update_function

def prepare_init_function(file: str, function_name: str):
    """
    Prepare a function that can be called to run a ballang function from python
    """
    def run_init_function(game: PinballGame):
        funcs = get_update_functions(game)
        ballang_funcs = parse_file(file, funcs)
        on_init = ballang_funcs.get(function_name)
        assert on_init is not None, f"function {function_name} not found"
        on_init()
    return run_init_function


def prepare_coll_function(file: str, function_name: str):
    """
    Prepare a function that can be called to run a ballang function from python
    """
    def run_coll_function(state: GameState, coll_t: float, ball_id: int, change_info: ChangeInfo):
        funcs = get_state_functions(state, change_info)
        ballang_funcs = parse_file(file, funcs)
        coll_fn = ballang_funcs.get(function_name)
        assert coll_fn is not None, f"function {function_name} not found"
        coll_fn(coll_t, ball_id)
    return run_coll_function

def prepare_keydown_function(file: str, function_name: str):
    """
    Prepare a function that can be called to run a ballang function from python
    """
    def run_keydown_function(game: PinballGame, key: int):
        funcs = get_update_functions(game)
        ballang_funcs = parse_file(file, funcs)
        on_keydown = ballang_funcs.get(function_name)
        assert on_keydown is not None, f"function {function_name} not found"
        on_keydown(key)
    return run_keydown_function

# Used for Hardware
input_state_l = False
input_state_r = False
input_state_power = 0
def hardware_get_input():
    global input_state_l, input_state_r, input_state_power
    if hardware_connected:
        input_state_l, input_state_r, input_state_power = hardware1.check_input()

def hardware_check_l():
    return input_state_l

def hardware_check_r():
    return input_state_r

def hardware_check_power():
    return input_state_power



if __name__ == "__main__":
    global_vars: Dict[str, Value] = {}
    file = """
    def main() {
        print("Hello, world!");
    }
    """
    start_time = time.time()
    funcs = get_update_functions(FormHandler(), [], global_vars)
    global_scope = parse_file(file, funcs)
    main = global_scope.get("main")
    assert isinstance(main, Function)
    main.call([])
    print("elapsed time:", time.time() - start_time)
