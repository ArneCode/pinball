from __future__ import annotations
import copy
import math
import time
from typing import List, Tuple

from ball import Ball
from form import Form, TransformForm
from formhandler import FormHandler
import multiprocessing as mp
from multiprocessing import Queue

def empty_queue(queue: Queue):
    print("emptying queue")
    start_time = time.time()
    while not queue.empty():
        queue.get()
    end_time = time.time()
    print(f"emptying queue took {end_time - start_time} seconds")
# 
# 
def precalc_colls(in_queue: Queue[Tuple[List[Ball], FormHandler]], out_queues: List[Queue[Tuple[float, List[Ball], FormHandler]]], stop_event, read_lag_evt):
    assert len(out_queues) > 2
    curr_queue_n = 0
    curr_out_queue = out_queues[curr_queue_n]
    used_queues: List[int] = []
    balls, forms = in_queue.get()
    i = 0
    prev_obj = None
    prev_coll_t = 0
    remove_dup = False
    last_coll_t = 0
    while not stop_event.is_set():
        #print("c thread: aquire lock")
        #lock.acquire()
        #print("c thread: lock aquired")
        start_time = time.time()
        if not in_queue.empty():
            used_queues.append(curr_queue_n)
            curr_queue_n = (curr_queue_n + 1) % len(out_queues)
            curr_out_queue = out_queues[curr_queue_n]

            balls, forms = in_queue.get()
            prev_obj = None
            prev_coll_t = 0
            remove_dup = False
            i = 0
            continue
        if curr_out_queue.qsize() > 1000:
            if len(used_queues) > 0:
                print("emptying prev queue")
                empty_queue(out_queues[used_queues.pop(0)])
            continue
        #print(f"running {random.randint(0, 100)}")
       # print(f"i: {i}")
        
        first_coll = None
        first_coll_t = float("inf")
        first_coll_ball: int = -1
        ball_forms = []
        form_with_balls = forms.clone()
        for ball in balls:
            form = ball.get_form()
            ball_forms.append(form)
            form_with_balls.add_form(form)
        ball_inner_forms: List[Form] = []
        for form in ball_forms:
            assert isinstance(form, TransformForm)
            ball_inner_forms.append(form.form)
        for i in range(len(balls)):
            ball = balls[i]
            form = ball_forms[i]
            coll = form_with_balls.find_collision(ball, ignore=[form])
            if coll is None:
                continue
            coll_time = coll.time + ball.start_t
            if coll_time < first_coll_t:
                first_coll = coll
                first_coll_t = coll_time
                first_coll_ball = i
        if first_coll is None:
            continue
            raise Exception("no collision found")
        coll = first_coll
        ball = balls[first_coll_ball]
        other: Form = coll.get_obj_form()
        dir = coll.get_result_dir()
        if other in ball_inner_forms:
            print(f"ball-to-ball: {first_coll_t}")
            other_ball_i = ball_inner_forms.index(other)
            other_ball = balls[other_ball_i]
            other_ball = other_ball.with_start_t(first_coll_t).with_start_pos(
                other_ball.get_pos(first_coll_t - 0.00001)).with_vel(dir*(-1))
            balls[other_ball_i] = other_ball
        #print(f"new ball pos: {ball.get_pos(coll.time + ball.start_t)}")
        ball = ball.with_start_t(first_coll_t).with_start_pos(
            ball.get_pos(first_coll_t - 0.00001)).with_vel(dir)
        #print(f"ball_start_t: {ball.start_t}, first_coll_t: {first_coll_t}, other: {other}")
        balls[first_coll_ball] = ball
        if first_coll_t < 50 or True:
            curr_out_queue.put((first_coll_t, copy.copy(balls), forms))
        i += 1
        end_time = time.time()
        #lock.release()
        #print(f"c thread: lock released, took {end_time - start_time} seconds")
        #print(f"calc took {end_time - start_time} seconds")
    print("exit")
    raise SystemExit

class CollThread:
    out_queues: List[mp.Queue[Tuple[float, List[Ball], FormHandler]]]
    curr_queue_n: int
    in_queue: mp.Queue[Tuple[List[Ball], FormHandler]]
    #    stop_evt: mp.synchronize.Event
    proc: mp.Process

    balls: List[Ball]
    form_handler: FormHandler
    has_read_lag: bool

    next_coll_t: float
    next_balls: List[Ball]
    next_form: FormHandler

    def __init__(self, balls: List[Ball], form_handler: FormHandler, num_queues: int = 100):
        self.out_queues = []
        for i in range(num_queues):
            self.out_queues.append(mp.Queue())
        self.curr_queue_n = 0
        self.in_queue = mp.Queue()
        self.in_queue.put((balls, form_handler))
        self.stop_evt = mp.Event()
        self.read_lag_evt = mp.Event()
        self.has_read_lag = False
        self.proc = mp.Process(target=precalc_colls, args=(self.in_queue, self.out_queues, self.stop_evt, self.read_lag_evt))
        self.balls = balls
        self.form_handler = form_handler
        self.proc.start()
        self.next_coll_t, self.next_balls, self.next_form = self.out_queues[self.curr_queue_n].get()
    def get_curr_queue(self) -> mp.Queue[Tuple[float, List[Ball], FormHandler]]:
        return self.out_queues[self.curr_queue_n]
    # checks weather the time is past the next collision and return the new ball and form if so
    def check_coll(self, time: float) -> Tuple[List[Ball], FormHandler, float | None] | None:
        looped = False
        n_looped = 0
        lagging_behind = None
        if time >= self.next_coll_t:
            n_looped += 1
            self.balls = self.next_balls
            self.form_handler = self.next_form
            self.next_coll_t, self.next_balls, self.next_form = self.get_curr_queue().get()
            return self.balls, self.form_handler, None
        print(f"curr queue len: {self.get_curr_queue().qsize()}")
        # if looped and time - self.ball.start_t > 10:
        #     print("lagging behind")
        #     if not self.has_read_lag:
        #         self.read_lag_evt.set()
        #         self.has_read_lag = True

        # if looped:
        #         #lagging_behind = time
        #     return self.balls, self.form_handler, lagging_behind
        return None
    def restart(self, balls: List[Ball], form_handler: FormHandler, time: float):
        #ball = ball.from_time(curr_t)
        #in_queue.put((ball, curr_forms))
        self.balls = balls
        self.form_handler = form_handler
        for i in range(len(self.balls)):
            self.balls[i] = self.balls[i].from_time(time)
        #self.ball = self.ball.from_time(time)
        self.in_queue.put((self.balls, form_handler))
        self.curr_queue_n = (self.curr_queue_n + 1) % len(self.out_queues)
        self.next_coll_t, self.next_balls, self.next_form = self.get_curr_queue().get()
        #print(f"restart, next_coll_t: {self.next_coll_t + self.ball.start_t}, curr_t: {time}, diff: {self.next_coll_t + self.ball.start_t - time}")
    def stop(self):
        self.stop_evt.set()
        self.proc.join()