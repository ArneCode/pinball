import time
from typing import Dict, List, Set
from game import PinballGame
from objects.ball import Ball
from ballang import parse_file
from ballang.eval_visitor import Function, Value
from objects.formhandler import FormHandler
from objects.forms.timedform import TimedForm

def prepare_functions(game: PinballGame, global_vars: Dict) -> Dict:
    def read_global(name: str) -> Value:
        assert name in global_vars, f"global variable {name} not found"
        return global_vars[name]
    def set_global(name: str, value: Value) -> None:
        global_vars[name] = value
    def remove_named_form(name: str) -> None:
        game.curr_forms = game.curr_forms.clone()
        game.curr_forms.remove_named_form(name)
    def hide_named_form(name: str) -> None:
        game.curr_forms = game.curr_forms.clone()
        game.curr_forms.hide_named_form(name)
    def show_named_form(name: str) -> None:
        game.curr_forms = game.curr_forms.clone()
        game.curr_forms.show_named_form(name)
    def spawn_form_timed(hidden_name: str, scene_name: str, time = None):
        if time is None:
            time = game.calc_time()
        game.curr_forms = game.curr_forms.clone()
        form = game.curr_forms.get_hidden_form(hidden_name)
        assert form is not None, f"spawn_form_timed: form with name {hidden_name} not found"
        timed_form = TimedForm(form, time)
        game.curr_forms.set_named_form(scene_name, timed_form)
    def remove_ball(ball_id: int) -> None:
        for i, ball in enumerate(game.balls):
            if i == ball_id:
                del game.balls[i]
                return
        raise Exception(f"ball with id {ball_id} not found")
    def is_key_pressed(key: int):
        return key in game.curr_pressed
    def is_moving(name: str, time: float = 0.0):
        form = game.curr_forms.get_named_form(name)
        assert form is not None, f"is_moving: form with name {name} not found"
        return form.is_moving(time)
    
    def calc_time():
        return game.calc_time()
    
    def restart_colls(t: float):
        game.restart_colls(t)
    
    funcs = {
        "read_global": read_global,
        "set_global": set_global,
        "remove_ball": remove_ball,
        "print": print,
        "remove_named_form": remove_named_form,
        "hide_named_form": hide_named_form,
        "show_named_form": show_named_form,
        "spawn_form_timed": spawn_form_timed,
        "is_key_pressed": is_key_pressed,
        "calc_time": calc_time,
        "restart_colls": restart_colls,
        "is_moving": is_moving,
    }
    return funcs

if __name__ == "__main__":
    global_vars: Dict[str, Value] = {}
    file = """
    def main() {
        print("Hello, world!");
    }
    """
    start_time = time.time()
    funcs = prepare_functions(FormHandler(), [], global_vars)
    global_scope = parse_file(file, funcs)
    main = global_scope.get("main")
    assert isinstance(main, Function)
    main.call([])
    print("elapsed time:", time.time() - start_time)