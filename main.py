from __future__ import annotations
import copy
import math
import time
from typing import Tuple
import pygame
from ball import Ball
from form import CircleForm, FormHandler, LineForm, RotateForm, TempForm
from interval import SimpleInterval
from polynom import Polynom
from vec import Vec
# use queue from multiprocessing to communicate between threads
from multiprocessing import Queue, Event
import multiprocessing as mp

def precalc_colls(ball: Ball, forms: FormHandler, queue: Queue, stop_event):
    ball = copy.deepcopy(ball)
    i = 0
    prev_obj = None
    prev_coll_t = 0
    remove_dup = False
    while not stop_event.is_set():
        #print(f"i: {i}")
        if remove_dup and prev_obj is not None and prev_obj:
            coll = forms.find_collision(ball, ignore=[prev_obj])
            remove_dup = False
        else:
            coll = forms.find_collision(ball)
        assert coll is not None
        if coll.obj is prev_obj and math.isclose(coll.time + ball.start_t, prev_coll_t, abs_tol=0.01):
            print("remove dup")
            remove_dup = True
            prev_coll_t = coll.time + ball.start_t
            continue
        prev_coll_t = coll.time + ball.start_t
        
        dir = coll.get_result_dir()  # *(-50)
        ball = ball.with_start_t(coll.time + ball.start_t).with_start_pos(
                ball.get_pos(coll.time+ball.start_t - 0.001)).with_vel(dir*(1))
        
        prev_obj = coll.obj
        queue.put((coll.time, ball))
        i += 1
    print("exit")
    raise SystemExit
pol = Polynom([6 ,-5, -2, 1])
print(pol.smallest_root_bisect(SimpleInterval(-10, 10)))

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
    ball = Ball(Vec(250, 300), 50, "red").with_acc(Vec(0, 90.8)).with_vel(Vec(
        70, 0.1
    ))
    form_handler = FormHandler()
    # ränder
    form_handler.add_form(LineForm(Vec(0, 0), Vec(1280, 0), 50))
    form_handler.add_form(LineForm(Vec(0, 0), Vec(0, 720), 50))
    form_handler.add_form(LineForm(Vec(1280, 0), Vec(1280, 720), 50))
    form_handler.add_form(LineForm(Vec(0, 720), Vec(1280, 720), 50))

    #boden = LineForm(Vec(100, 600), Vec(1280, 400), 50)
    form_handler.add_form(CircleForm(Vec(600, 1600), 1200,
                       SimpleInterval(200, 1080), SimpleInterval(100, 700), 1000))
    
    # a rotated line
    line = LineForm(Vec(0,720), Vec(500,720), 50)
    #rotateform: def __init__(self, form: Form, center: Vec[float], start_angle: float, angle_speed: float, time_interval: SimpleInterval):
    
    line_rotated = RotateForm(line, Vec(0, 720), 0, 0.2, SimpleInterval(0, 1000))

    line_fixed = LineForm(Vec(0, 720), Vec(500, 500), 50)

    line_temped = TempForm(line_rotated, 10, line_fixed)
    form_handler.add_form(line_temped)

    queue: Queue[Tuple[float, Ball]] = mp.Queue()
    stop_event = mp.Event()
    # start a thread to precalculate collisions
    coll_process = mp.Process(target=precalc_colls, args=(ball, form_handler, queue, stop_event))
    coll_process.start()
    next_coll_t, next_ball = queue.get()
    # bahn = ball.gen_flugbahn(-9.8, 6)
    start_time = time.time_ns()
    #coll = form_handler.find_collision(ball)
    #passed = (time.time_ns() - start_time)/(10**6)
    #print(f"calculating took {passed} ms")

    
    
    #print(f"coll_t: {coll.time}")
    k = 0
    while running:
        # poll for events
        # pygame.QUIT event means the user clicked X to close your window
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                stop_event.set()
                coll_process.terminate()
                break

                #coll_process.join()
        if not running:
            break
        # fill the screen with a color to wipe away anything from last frame
        screen.fill("black")

        # ball.update(dt)
        passed = (time.time_ns() - start_time)/(10**(8.3))
        # ball.pos_0 = bahn.get_pos(passed)
        while passed > next_coll_t+ ball.start_t:# and k < 5:
            print(f"coll, prev_veL: {ball.bahn.deriv().apply(passed).magnitude()}, next_vel: {next_ball.vel_0.magnitude()}")
            ball = next_ball
            next_coll_t, next_ball = queue.get()
            print(f"next_coll_t: {next_coll_t}, next_ball: {next_ball}")
            energy = ball.vel_0.magnitude()**2/2 + ball.pos_0.y*9.8
            print(f"energy: {energy}, k: {k}")
            k += 1
            # dir = coll.get_result_dir()  # *(-50)
            # ball = ball.with_start_t(coll.time + ball.start_t).with_start_pos(
            #     ball.get_pos(coll.time+ball.start_t - 0.0001)).with_vel(dir*(1))  # .with_acc(Vec(0.0, 0.0))
            # print(f"ball pos: {ball.pos_0}, actually: {ball.get_pos(passed)}")
            # coll = form_handler.find_collision(ball)
            #coll.time = float("inf")
            #if coll is None:
            #    print("found no collision")
            #else:
            #    i += 1
            #    print(f"found coll: {coll.time}, i: {i}")


        # screen.fill("black")
        # boden.draw(screen, (0, 255, 0))
        # continue

        # RENDER YOUR GAME HERE
        form_handler.draw(screen, (0, 255, 0), passed)
        #line_rotated.draw(screen, (0, 255, 0), passed)

        ball.draw(passed, screen)
        # flip() the display to put your work on screen
        pygame.display.flip()
        #clock.tick(60)

    pygame.quit()
    coll_process.join()