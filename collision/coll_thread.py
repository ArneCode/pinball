from __future__ import annotations
import copy
import math
import time
from typing import Any, Callable, Dict, List, Optional, Tuple
from ballang_vars import VarHandler
#from game import GameState

from objects.ball import Ball
from collision.collision import TimedCollision
from objects.form import Form, StaticForm
from objects.formhandler import FormHandler
import multiprocessing as mp
from multiprocessing import Queue

from objects.forms.transformform import TransformForm


def empty_queue(queue: Queue):
    """
    Empties the given queue by removing all elements from it.

    Args:
        queue (Queue): The queue to be emptied.
    """
    print("emptying queue")
    start_time = time.time()
    while not queue.empty():
        queue.get()
    end_time = time.time()
    print(f"emptying queue took {end_time - start_time} seconds")


def precalc_colls(in_queue: Queue[Any], out_queues: List[Queue[GameStateChange]], stop_event, 
                  form_functions: Dict[str, Callable[["GameState", float, int, ChangeInfo], None]]):
    from game import GameState
    in_queue: Queue[GameState] = in_queue
    form_functions: Dict[str, Callable[[GameState, float, int, ChangeInfo], None]] = form_functions
    assert len(out_queues) > 2
    curr_queue_n = 0
    curr_out_queue = out_queues[curr_queue_n]
    used_queues: List[int] = []
    game_state = in_queue.get()
    i = 0
    prev_obj = None
    prev_coll_t = 0
    remove_dup = False
    last_coll_t = 0
    while not stop_event.is_set():
        # print("c thread: aquire lock")
        # lock.acquire()
        # print("c thread: lock aquired")
        start_time = time.time()
        if not in_queue.empty():
            print("in_queue not empty")
            used_queues.append(curr_queue_n)
            curr_queue_n = (curr_queue_n + 1) % len(out_queues)
            curr_out_queue = out_queues[curr_queue_n]

            game_state = in_queue.get()
            print(
                f"aquired new balls and forms, named_forms: {game_state.forms.named_forms}, new_ballang_vars: {game_state.ballang_vars}")
            #raise Exception("new balls and forms")
            prev_obj = None
            prev_coll_t = 0
            remove_dup = False
            i = 0
            continue
        if curr_out_queue.qsize() > 1000 or game_state.is_end:
            if len(used_queues) > 0:
                print("emptying prev queue")
                empty_queue(out_queues[used_queues.pop(0)])
            continue

        first_coll = None
        first_coll_t = float("inf")
        first_coll_ball: int = -1
        ball_forms = []
        change_info = ChangeInfo()
        form_with_balls = game_state.forms.copy()
        for ball in game_state.balls:
            form = ball.get_form()
            ball_forms.append(form)
            form_with_balls.add_form(form)
        ball_inner_forms: List[Form] = []
        for form in ball_forms:
            assert isinstance(form, TransformForm)
            ball_inner_forms.append(form.form)
        for i in range(len(game_state.balls)):
            ball = game_state.balls[i]
            form = ball_forms[i]
            coll = form_with_balls.find_collision(ball, ignore=[form])
            # print("found coll")
            if coll is None:
                continue

            coll_time = coll.get_coll_t() + ball.start_t
            if coll_time < first_coll_t:
                first_coll = coll
                first_coll_t = coll_time
                first_coll_ball = i
        if first_coll is None:
            continue
            raise Exception("no collision found")
        coll = first_coll
        if first_coll_t < 50:
            log = True
        else:
            log = False
        log = False
        if log:
            print(f"found coll at t: {first_coll_t}")
        ball = game_state.balls[first_coll_ball]
        other: StaticForm = coll.get_obj_form()
        if other.do_reflect:
            dir = coll.get_result_dir()
            if other in ball_inner_forms:
                print(f"ball-to-ball: {first_coll_t}")
                other_ball_i = ball_inner_forms.index(other)
                other_ball = game_state.balls[other_ball_i]
                other_ball = other_ball.with_start_t(first_coll_t).with_start_pos(
                    other_ball.get_pos(first_coll_t)).with_vel(dir*(-1))
                game_state.balls[other_ball_i] = other_ball
                #assert isinstance(other, StaticForm)
            ball = ball.with_start_t(first_coll_t).with_start_pos(
            ball.get_pos(first_coll_t)).with_vel(dir)
            # print(f"ball_start_t: {ball.start_t}, first_coll_t: {first_coll_t}, other: {other}")
            game_state.balls[first_coll_ball] = ball
        else:
            vel = ball.get_vel(first_coll_t)
            ball = ball.with_start_t(first_coll_t).with_start_pos(
                ball.get_pos(first_coll_t)).with_vel(vel)
            game_state.balls[first_coll_ball] = ball
        change_info.set_balls_changed()

        on_collision = other.on_collision

        for fn_name in on_collision:
            print(f"collision, executing {fn_name}, on_collision: {on_collision}")
            form_functions[fn_name](game_state, first_coll_t, first_coll_ball, change_info)
            print(f"ballang_vars: {game_state.ballang_vars.vars}")
        # print(f"new ball pos: {ball.get_pos(coll.time + ball.start_t)}")
        if log:
            print(f"ball-to-form: {first_coll_t}")
        if len(game_state.balls) == 0:
            print("no balls left")
            curr_out_queue.put(GameStateChange(first_coll_t, None, None, None, True))
        change = GameStateChange(first_coll_t, None, None, None)
        if change_info.balls_changed:
            change.new_balls = game_state.balls.copy()
        if change_info.forms_changed:
            change.new_forms = game_state.forms.copy()
        if change_info.globals_changed:
            change.new_globals = copy.deepcopy(game_state.ballang_vars)
        curr_out_queue.put(change)
        i += 1
        end_time = time.time()
    print("exit")
    raise SystemExit


class GameStateChange:
    change_t: float
    new_balls: Optional[List[Ball]]
    new_forms: Optional[FormHandler]
    new_globals: Optional[VarHandler]

    is_end: bool

    def __init__(self, change_t: float, new_balls: Optional[List[Ball]]=None, new_forms: Optional[FormHandler]=None, new_globals: Optional[Dict[str, Any]]=None, is_end: bool = False):
        self.change_t = change_t
        self.new_balls = new_balls
        self.new_forms = new_forms
        self.new_globals = new_globals
        self.is_end = is_end
class ChangeInfo:
    balls_changed: bool
    forms_changed: bool
    globals_changed: bool
    def __init__(self, balls_changed: bool = False, forms_changed: bool = False, globals_changed: bool = False):
        self.balls_changed = balls_changed
        self.forms_changed = forms_changed
        self.globals_changed = globals_changed
    def set_balls_changed(self):
        self.balls_changed = True
    def set_forms_changed(self):
        self.forms_changed = True
    def set_globals_changed(self):
        self.globals_changed = True
class CollThread:
    out_queues: List[mp.Queue[GameStateChange]]
    curr_queue_n: int
    in_queue: mp.Queue
    #    stop_evt: mp.synchronize.Event
    proc: mp.Process

    #state: GameState
    has_read_lag: bool

    next_change: GameStateChange

    def __init__(self, game_state, num_queues: int = 100, form_functions: Dict[str, Callable[["GameState", float, int, ChangeInfo], None]] = {}):
        self.out_queues = []
        for i in range(num_queues):
            self.out_queues.append(mp.Queue())
        self.curr_queue_n = 0
        self.in_queue = mp.Queue()
        self.state = game_state
        self.in_queue.put(game_state)
        self.stop_evt = mp.Event()
        self.has_read_lag = False
        self.proc = mp.Process(target=precalc_colls, args=(
            self.in_queue, self.out_queues, self.stop_evt, form_functions))
        self.proc.start()
        self.next_change = self.out_queues[self.curr_queue_n].get()

    def get_curr_queue(self) -> mp.Queue[Tuple[float, List[Ball], Optional[FormHandler]]]:
        return self.out_queues[self.curr_queue_n]
    # checks weather the time is past the next collision and return the new ball and form if so
    def apply_next_change(self):
        c = self.next_change
        if c.new_balls is not None:
            self.state.balls = c.new_balls
        if c.new_forms is not None:
            self.state.forms = c.new_forms
        if c.new_globals is not None:
            self.state.ballang_vars.merge(c.new_globals)
        if c.is_end:
            self.state.is_end = True
    def check_coll(self, time: float, break_after: Optional[int] = 5) -> Optional[Tuple[Any,int]]:
        looped = False
        n_looped = 0
        lagging_behind = None
        while time >= self.next_change.change_t:
            if break_after is not None and n_looped >= break_after:
                print("breaking")
                break
            n_looped += 1
            self.apply_next_change()
            if not self.state.is_end:
                self.next_change = self.get_curr_queue().get()
            looped = True
        if looped:
            return self.state, n_looped
        return None

    def restart(self, state, time: float):
        self.check_coll(time, None)
        from game import GameState
        state: GameState = state
        self.state = state
        for i in range(len(self.state.balls)):
            self.state.balls[i] = self.state.balls[i].from_time(time)
        self.in_queue.put(self.state)
        self.curr_queue_n = (self.curr_queue_n + 1) % len(self.out_queues)
        self.next_change = self.get_curr_queue().get()

    def stop(self):
        self.stop_evt.set()
        self.proc.join()
