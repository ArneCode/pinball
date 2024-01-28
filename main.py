from __future__ import annotations
import copy
import math
import random
import time
from typing import Set, Tuple
import pygame
from ball import Ball
from form import CircleForm, FormContainer, LineForm, NoneForm, RotateForm, TempForm, TransformForm
from formhandler import FormHandler
from interval import SimpleInterval
from material import Material
from polynom import Polynom
from vec import Vec

from coll_thread import CollThread

normal_material = Material(0.8, 0.95, 20, 1)
flipper_material = Material(1.1, 1.0, 20, 0.0)
speed = 8.5


pol = Polynom([6, -5, -2, 1])
#print(pol.smallest_root_bisect(SimpleInterval(-10, 10)))


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


if __name__ == "__main__":
    # pygame setup
    pygame.init()
    screen = pygame.display.set_mode((1280, 720))

    clock = pygame.time.Clock()
    # clock.tick(60)  # limits FPS to 60
    running = True
    i = 0

    dt = 0.001
    balls = []
    # create ball
    _ball = Ball(Vec(500, 550), 50, "red").with_acc(Vec(0, 9.81)).with_vel(Vec(
        -50, 0.5
    ))

    balls.append(_ball)
    _ball2 = Ball(Vec(250, 550), 50, "red").with_acc(Vec(0, 0.1)).with_vel(Vec(
        2, 0.1
    ))
    _ball3 = Ball(Vec(700, 550), 50, "red").with_acc(Vec(0, 0.1)).with_vel(Vec(
        -2, 0.1
    ))
    #balls.append(_ball3)
    #balls.append(_ball2)
    _ball4 = Ball(Vec(700, 200), 50, "red").with_acc(Vec(0, 0.1)).with_vel(Vec(
        -2, 0.1
    ))
    #balls.append(_ball4)
    ball_form = _ball2.get_form()
    coll = ball_form.find_collision(_ball)
    print(f"got coll: {coll}")
    #exit()
    #balls.append(_ball)
    start_forms = FormHandler()
    #floating_ball = CircleForm(Vec(700,620), 100, normal_material, -3, 2)
    #moving_ball = TransformForm(floating_ball, Vec(-x,-x)*3)
    #start_forms.add_form(moving_ball)
    #start_forms.add_form(floating_ball)
    #coll = floating_ball.find_collision(_ball)
    #print(f"got coll: {coll}")
    #exit()

    #start_forms.add_form(_ball.get_form())
    #balls.append(_ball)
    # x = Polynom([0, 1])
    # new_bahn = Vec((x**0)*1229.6231817424573 + (x**1)*(-376.81825756158787), (x**0)*55.43841365643251 + x*(-561.5152209065546) + (x**2)*45.4)
    # ball = ball.with_bahn(new_bahn).with_start_t(0.0)
    # ränder
    start_forms.add_form(LineForm(Vec(0, 0), Vec(
        1280, 0), 50, material=normal_material))
    start_forms.add_form(LineForm(Vec(0, 0), Vec(
        0, 720), 50, material=normal_material))
    start_forms.add_form(LineForm(Vec(1280, 0), Vec(
        1280, 720), 50, material=normal_material))
    start_forms.add_form(LineForm(Vec(0, 720), Vec(
        1280, 720), 50, material=normal_material))

    # boden = LineForm(Vec(100, 600), Vec(1280, 400), 50)
    #start_forms.add_form(CircleForm(Vec(600, 1600), 1200,normal_material,4,5, 1000))
    # form_handler.add_form(CircleForm(Vec(500, 300), 100, normal_material,0, 2, 1000))
    #start_forms.add_form(CircleForm(
    
    #    Vec(700, 300), 100, normal_material, 4, 6, 1000))
    #start_forms.add_form(CircleForm(
    #    Vec(900, 300), 100, normal_material, 4, 6, 1000))

    # line
    # form_handler.add_form(LineForm(Vec(100, 620), Vec(450, 720), 50, material=normal_material))
    # a rotated line
    flipper_line = LineForm(Vec(100, 720), Vec(
        450, 720), 50, material=flipper_material)
    # print(f"flipper steep: {flipper_line.paths[1].eq_x}, {flipper_line.paths[1].eq_y}")
    flipper_line_rotated = make_flipper(
        flipper_line, Vec(100, 720), 0, 0, 0.001, True)
    flipper_line_rotated.is_end = True
    # flipper = FormContainer(flipper_line_rotated, name="flipper")
    start_forms.set_named_form("flipper", flipper_line_rotated)

    floating_ball = CircleForm(Vec(700,420), 100, normal_material, -2, 1.7)
    start_forms.add_form(floating_ball)
    # #moving_ball = TransformForm(floating_ball, Vec(-x,-x)*3)
    # #start_forms.add_form(moving_ball)
    # start_forms.add_form(floating_ball)

    coll_thread = CollThread(balls, start_forms)
    # next_coll_t, next_ball, next_forms = queue.get()
    # bahn = ball.gen_flugbahn(-9.8, 6)
    start_time = time.time_ns()
    # coll = form_handler.find_collision(ball)
    # passed = (time.time_ns() - start_time)/(10**6)
    # print(f"calculating took {passed} ms")
    curr_forms = start_forms
    last_time = 0

    def calc_time():
        return last_time + (time.time_ns() - start_time)/(10**(speed))

    curr_pressed: Set[int] = set()
    flipper_moving_up = False
    n_colls = 0

    def handle_keydown(key: int):
        global speed, last_time, start_time, curr_forms, balls
        curr_pressed.add(key)
        # if key is the letter "k", remove flipper
        if key == pygame.K_k:
            t = calc_time()
            curr_forms = curr_forms.clone()
            curr_forms.remove_named_form("flipper")
            coll_thread.restart(balls, curr_forms, t)
            curr_state = coll_thread.check_coll(t)
            if curr_state is not None:
                balls, curr_forms, _ = curr_state
                #ball = balls[0]
        # if key is the letter "f", make game faster
        #print(f"speed: {speed}")

        if key == pygame.K_f:
            # global speed
            last_time = calc_time()
            start_time = time.time_ns()
            speed -= 0.1
        # if key is the letter "s", make game slower
        if key == pygame.K_s:
            # global speed
            last_time = calc_time()
            start_time = time.time_ns()
            speed += 0.1

            print(f"speed: {speed}")
        # if key is the letter "r", reset n_colls
        if key == pygame.K_r:
            global n_colls
            n_colls = 0

    def handle_keyup(key):
        curr_pressed.remove(key)

    k = 0
    #curr_pressed.add(pygame.K_SPACE)
    while running:
        #print(f"speed: {speed}, n_colls: {n_colls}, queue size: {coll_thread.get_curr_queue().qsize()}")
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                coll_thread.stop()
                break
            elif event.type == pygame.KEYDOWN:
                handle_keydown(event.key)
            elif event.type == pygame.KEYUP:
                handle_keyup(event.key)
        flipper = curr_forms.get_named_form("flipper")
        if flipper is not None and isinstance(flipper, TempForm):
            move_ended = calc_time() > flipper.form_duration
            if pygame.K_SPACE in curr_pressed and not flipper_moving_up and move_ended:
                print("a")
                t = calc_time()
                curr_state = coll_thread.check_coll(t)
                if curr_state is not None:
                    balls, curr_forms, _ = curr_state
                # stop_process(coll_process, stop_event)
                curr_forms = curr_forms.clone()
                curr_forms.set_named_form("flipper", make_flipper(
                    flipper_line, Vec(100, 720), 1, 0, 10, False, t))
                # flipper.set(make_flipper(flipper_line, Vec(100, 620), 1, 0, 1, False, t))
                coll_thread.restart(balls, curr_forms, t)
                curr_state = coll_thread.check_coll(t)
                if curr_state is not None:
                    balls, curr_forms, _ = curr_state
                flipper_moving_up = True
            elif pygame.K_SPACE not in curr_pressed and flipper_moving_up and move_ended:
                print("b")
                t = calc_time()
                curr_state = coll_thread.check_coll(t)
                if curr_state is not None:
                    balls, curr_forms, _ = curr_state
                # stop_process(coll_process, stop_event)
                curr_forms = curr_forms.clone()
                curr_forms.set_named_form("flipper", make_flipper(
                    flipper_line, Vec(100, 720), 1, 0, 10, True, t))
                # flipper.set(make_flipper(flipper_line, Vec(100, 620), 1, 0, 1, True, t))
                coll_thread.restart(balls, curr_forms, t)
                curr_state = coll_thread.check_coll(t)
                if curr_state is not None:
                    balls, curr_forms, _ = curr_state

                flipper_moving_up = False
        if pygame.K_s in curr_pressed:
            speed += 0.01
        if pygame.K_f in curr_pressed:
            speed -= 0.01

            # coll_process.join()
        if not running:
            break
        # fill the screen with a color to wipe away anything from last frame
        screen.fill("black")

        # ball.update(dt)
        passed = calc_time()
        #print(f"passed: {passed}")
        curr_forms.draw(screen, (0, 255, 0), passed)
        # ball.pos_0 = bahn.get_pos(passed)
        # looped = False
        curr_state = coll_thread.check_coll(passed)
        lagging_behind = None
        if curr_state is not None:
            print("coll")
            balls, curr_forms, lagging_behind = curr_state
            print(f"ball_start_pos: {balls[0].pos_0}, ball_start_t: {balls[0].start_t}, curr_t: {passed}")
            n_colls += 1
        # if lagging_behind is not None:
        #     print(f"lagging behind: {lagging_behind - passed}")
        #     ball.draw(lagging_behind, screen)
        # else:
        #     ball.draw(passed, screen)
        for ball in balls:
            ball.get_form().draw(screen, ball.color, passed)
            ball.draw(passed, screen)
        # flip() the display to put your work on screen
        pygame.display.flip()
        clock.tick(60)

    pygame.quit()
    # coll_process.join()
