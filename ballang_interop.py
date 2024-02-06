import time
from typing import Dict, List, Set
from collision.coll_thread import ChangeInfo
from game import GameState, PinballGame
from objects.ball import Ball
from ballang import parse_file
from ballang.eval_visitor import Function, Value
from objects.formhandler import FormHandler
from objects.forms.timedform import TimedForm


def get_state_functions(state: GameState, change_info: ChangeInfo) -> Dict:
    def read_global(name: str) -> Value:
        assert name in state.ballang_vars, f"global variable {name} not found"
        return state.ballang_vars[name]

    def set_global(name: str, value: Value) -> None:
        state.ballang_vars[name] = value
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

    def is_moving(name: str, time: float = 0.0):

        form = state.forms.get_named_form(name)
        assert form is not None, f"is_moving: form with name {name} not found"
        return form.is_moving(time)

    funcs = {
        "read_global": read_global,
        "set_global": set_global,
        "remove_ball": remove_ball,
        "print": print,
        "remove_named_form": remove_named_form,
        "hide_named_form": hide_named_form,
        "show_named_form": show_named_form,
        "spawn_form_timed": spawn_form_timed,
        "is_moving": is_moving,
    }
    return funcs


def get_update_functions(game: PinballGame) -> Dict:

    def is_key_pressed(key: int):
        return key in game.curr_pressed

    def calc_time():
        return game.calc_time()

    def restart_colls(t: float):
        game.restart_colls(t)

    funcs = {
        "print": print,
        "is_key_pressed": is_key_pressed,
        "calc_time": calc_time,
        "restart_colls": restart_colls,
    }
    funcs.update(get_state_functions(game.curr_state, ChangeInfo()))
    return funcs


def run_update_function(file: str, game: PinballGame, function_name: str):
    funcs = get_update_functions(game)
    ballang_funcs = parse_file(file, funcs)
    on_update = ballang_funcs.get(function_name)
    assert on_update is not None, f"function {function_name} not found"
    on_update()


# def run_state_function(state: GameState, change_info: ChangeInfo, file: str, function_name: str):
#     funcs = get_state_functions(state, change_info)
#     ballang_funcs = parse_file(file, funcs)
#     on_update = ballang_funcs.get(function_name)
#     assert on_update is not None, f"function {function_name} not found"
#     on_update()

def prepare_coll_function(file: str, function_name: str):
    def run_coll_function(state: GameState, coll_t: float, ball_id: int, change_info: ChangeInfo):
        funcs = get_state_functions(state, change_info)
        ballang_funcs = parse_file(file, funcs)
        coll_fn = ballang_funcs.get(function_name)
        assert coll_fn is not None, f"function {function_name} not found"
        coll_fn(coll_t, ball_id)
    return run_coll_function


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
