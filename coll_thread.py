import math
import time
from typing import List, Tuple

from ball import Ball
from formhandler import FormHandler
import multiprocessing as mp

def empty_queue(queue: mp.Queue):
    print("emptying queue")
    start_time = time.time()
    while not queue.empty():
        queue.get()
    end_time = time.time()
    print(f"emptying queue took {end_time - start_time} seconds")
# : Queue[Tuple[Ball, FormHandler]]
# : List[Queue[Tuple[float, Ball, FormHandler]]]
def precalc_colls(in_queue, out_queues, stop_event, read_lag_evt):
    assert len(out_queues) > 2
    curr_queue_n = 0
    curr_out_queue = out_queues[curr_queue_n]
    used_queues: List[int] = []
    ball, forms = in_queue.get()
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

            ball, forms = in_queue.get()
            prev_obj = None
            prev_coll_t = 0
            remove_dup = False
            i = 0
            continue
        if curr_out_queue.qsize() > 100:
            if len(used_queues) > 0:
                print("emptying prev queue")
                empty_queue(out_queues[used_queues.pop(0)])
            continue
        #print(f"running {random.randint(0, 100)}")
       # print(f"i: {i}")
        if remove_dup and prev_obj is not None and prev_obj:
            print("removing dup")
            coll = forms.find_collision(ball, ignore=[prev_obj])
            remove_dup = False
        else:
            coll = forms.find_collision(ball)
        assert coll is not None
        if coll.obj is prev_obj and math.isclose(coll.time + ball.start_t, prev_coll_t, abs_tol=0.1) and False:
            print("remove dup")
            remove_dup = True
            prev_coll_t = coll.time + ball.start_t
            continue
        prev_coll_t = coll.time + ball.start_t

        dir = coll.get_result_dir()  # *(-50)
        ball = ball.with_start_t(coll.time + ball.start_t).with_start_pos(
            ball.get_pos(coll.time+ball.start_t - 0.001)).with_vel(dir*(1))

        prev_obj = coll.obj
        if read_lag_evt.is_set() and coll.time + ball.start_t - last_coll_t < 30 and curr_out_queue.qsize() > 50:
            print("skipping")
            continue
        curr_out_queue.put((coll.time, ball, forms))
        last_coll_t = coll.time + ball.start_t
        i += 1
        end_time = time.time()
        #lock.release()
        #print(f"c thread: lock released, took {end_time - start_time} seconds")
        #print(f"calc took {end_time - start_time} seconds")
    print("exit")
    raise SystemExit

class CollThread:
    #out_queues: List[mp.Queue[Tuple[float, Ball, FormHandler]]]
    curr_queue_n: int
    #in_queue: mp.Queue[Tuple[Ball, FormHandler]]
#    stop_evt: mp.synchronize.Event
    proc: mp.Process

    ball: Ball
    form_handler: FormHandler
    has_read_lag: bool

    next_coll_t: float
    next_ball: Ball
    next_form: FormHandler

    def __init__(self, ball: Ball, form_handler: FormHandler, num_queues: int = 100):
        self.out_queues = []
        for i in range(num_queues):
            self.out_queues.append(mp.Queue())
        self.curr_queue_n = 0
        self.in_queue = mp.Queue()
        self.in_queue.put((ball, form_handler))
        self.stop_evt = mp.Event()
        self.read_lag_evt = mp.Event()
        self.has_read_lag = False
        self.proc = mp.Process(target=precalc_colls, args=(self.in_queue, self.out_queues, self.stop_evt, self.read_lag_evt))
        self.ball = ball
        self.form_handler = form_handler
        self.proc.start()
        self.next_coll_t, self.next_ball, self.next_form = self.out_queues[self.curr_queue_n].get()
    def get_curr_queue(self):# -> mp.Queue[Tuple[float, Ball, FormHandler]]:
        return self.out_queues[self.curr_queue_n]
    # checks weather the time is past the next collision and return the new ball and form if so
    def check_coll(self, time: float) -> Tuple[Ball, FormHandler, float | None] | None:
        looped = False
        n_looped = 0
        lagging_behind = None
        while time >= self.next_coll_t + self.ball.start_t:
            n_looped += 1
            if n_looped > 10:
                print("lagging behind")
                lagging_behind = self.next_coll_t + self.ball.start_t
                break
            if self.get_curr_queue().qsize() < 500 and n_looped > 10:
                print("queue is emptying")
                break
            looped = True
            self.ball = self.next_ball
            self.form_handler = self.next_form
            self.next_coll_t, self.next_ball, self.next_form = self.get_curr_queue().get()
        if looped and time - self.ball.start_t > 10:
            print("lagging behind")
            if not self.has_read_lag:
                self.read_lag_evt.set()
                self.has_read_lag = True
        elif self.has_read_lag:
            self.read_lag_evt.clear()
            self.has_read_lag = False
        if looped:
                #lagging_behind = time
            return self.ball, self.form_handler, lagging_behind
        return None
    def restart(self, ball: Ball, form_handler: FormHandler, time: float):
        #ball = ball.from_time(curr_t)
        #in_queue.put((ball, curr_forms))
        self.ball = ball
        self.form_handler = form_handler
        self.ball = self.ball.from_time(time)
        self.in_queue.put((self.ball, form_handler))
        self.curr_queue_n = (self.curr_queue_n + 1) % len(self.out_queues)
        self.next_coll_t, self.next_ball, self.next_form = self.get_curr_queue().get()
        print(f"restart, next_coll_t: {self.next_coll_t + self.ball.start_t}, curr_t: {time}, diff: {self.next_coll_t + self.ball.start_t - time}")
    def stop(self):
        self.stop_evt.set()
        self.proc.join()