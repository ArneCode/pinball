from __future__ import annotations
import copy
import json
import math
import random
import time
from typing import List, Set, Tuple
import pygame
from ballang import parse_file
from ballang_vars import VarHandler
from game import GameState, PinballGame, make_flipper, make_rotating
from objects.ball import Ball
from collision.coll_direction import CollDirection
from objects.form import Form
from objects.forms.circleform import CircleForm
from objects.forms.lineform import LineForm
from objects.forms.periodicform import PeriodicForm
from objects.forms.polygonform import PolygonForm
from objects.forms.rotateform import RotateForm
from objects.forms.tempform import TempForm
from objects.formhandler import FormHandler
from math_utils.interval import SimpleInterval
from objects.material import Material
from math_utils.polynom import Polynom
from math_utils.vec import Vec
from ballang_interop import get_update_functions, prepare_coll_function, run_update_function

from collision.coll_thread import CollThread
from read_world import World

normal_material = Material(0.8, 0.95, 20, 1)
flipper_material = Material(1.1, 1.0, 40, 0.0)
speed = 8.0


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
    _ball = Ball(Vec(200, 550), 50, "red").with_acc(Vec(0, 9.81)).with_vel(Vec(
        -50, -300
    ))
    # 50.0 + 17.28480702·x, 479.61721365 - 93.0223965·x + 4.905·x²
    t_ = Polynom([0, 1])
    bahn = Vec((t_**0)*50.0 + (t_**1)*17.28480702, (t_**0) *
               479.61721365 + t_*(-93.0223965) + (t_**2)*4.905)
    _ball_neu = _ball.with_bahn(bahn).with_start_t(4.692454956294632)

    balls.append(_ball)
    # balls.append(_ball_neu)
    _ball2 = Ball(Vec(250, 550), 50, "red").with_acc(Vec(0, 0.1)).with_vel(Vec(
        2, 0.1
    ))
    _ball3 = Ball(Vec(700, 550), 50, "red").with_acc(Vec(0, 0.1)).with_vel(Vec(
        -2, 0.1
    ))
    # balls.append(_ball3)
    # balls.append(_ball2)
    _ball4 = Ball(Vec(700, 200), 50, "red").with_acc(Vec(0, 0.1)).with_vel(Vec(
        -2, 0.1
    ))
    # balls.append(_ball4)
    ball_form = _ball2.get_form()
    coll = ball_form.find_collision(_ball)
    print(f"got coll: {coll}")
    # exit()
    # balls.append(_ball)
    start_forms = FormHandler()
    # rand
    rand = PolygonForm([Vec(0, 0), Vec(1280, 0), Vec(1280, 720), Vec(
        0, 720)], normal_material, CollDirection.ALLOW_FROM_INSIDE, on_collision=["on_collide"], filled=False)
    start_forms.add_form(rand)

    flipper_line = LineForm(Vec(100, 720), Vec(
        450, 720), 50, material=flipper_material)
    # print(f"flipper steep: {flipper_line.paths[1].eq_x}, {flipper_line.paths[1].eq_y}")
    flipper_line_rotated = make_flipper(
        flipper_line, Vec(100, 720), 0, 0, 0.001, True)
    flipper_line_rotated.is_end = True
    # flipper = FormContainer(flipper_line_rotated, name="flipper")
    start_forms.set_named_form("flipper", flipper_line_rotated)
    a = 5.5
    floating_ball = CircleForm(
        Vec(700, 420), 100, normal_material, (0, 0, 0), -2 + a, 1.7 + a)
    polygon_pts: List[Vec[float]] = list(map(lambda v: v*1.1, [Vec(100, 100), Vec(
        200, 100), Vec(300, 150), Vec(200, 200), Vec(300, 400), Vec(100, 200)]))
    polygon = PolygonForm(polygon_pts, normal_material,
                          CollDirection.ALLOW_FROM_OUTSIDE)
    coll = polygon.find_collision(_ball_neu)
    print(f"got coll: {coll}")
    rotating_polygon = make_rotating(polygon, Vec(250, 250), 100)
    rotating_rotating_polygon = make_rotating(rotating_polygon, Vec(300, 300), 1000)
    print(f"rotating_polygon: {json.dumps(polygon.get_json())}")
    start_forms.add_form(polygon)
    #start_forms.add_form(rotating_polygon)
    rotated_floating_ball = make_rotating(floating_ball, Vec(500, 420), 100)
    #start_forms.add_form(rotated_floating_ball)
    curr_forms = start_forms
    last_time = 0

    flipper_moving_up = False
    n_colls = 0

    flipper_moving_up = make_flipper(
                flipper_line, Vec(100, 720), -1, 0, 3, False, 0.0)
    print(f"flipper_moving_up: {json.dumps(flipper_moving_up.get_json())}")
    flipper_moving_down = make_flipper(
                flipper_line, Vec(100, 720), -1, 0, 10, True, 0.0)
    print(f"flipper_moving_down: {json.dumps(flipper_moving_down.get_json())}")
    
    start_forms.set_hidden_form("flipper_moving_up", flipper_moving_up)
    start_forms.set_hidden_form("flipper_moving_down", flipper_moving_down)

    hidden_circle = CircleForm(Vec(100, 100), 50, normal_material, (0, 0, 0))
    start_forms.set_hidden_form("hidden_circle", hidden_circle)
    #globals = {"flipper_moving_up": False, "n_border_colls": 0, "hidden_circle_spawned": False}
    globals = VarHandler()
    globals.set_var("flipper_moving_up", False, 0.0)
    globals.set_var("n_border_colls", 0, 0.0)
    globals.set_var("hidden_circle_spawned", False, 0.0)

    on_update_code = """
 def on_update(){
      let t = calc_time();
     let flipper_moving_up = read_global("flipper_moving_up");
     let flipper_moving = is_moving("flipper",t);
     if flipper_moving {
        show_text("flipper_moving_up: "+str(flipper_moving_up), 100, 100, 20);
     }
     if is_key_pressed(32) && !flipper_moving_up && !flipper_moving {
        print("option 1");
         spawn_form_timed("flipper_moving_up", "flipper", t);
         print("c");
         restart_colls(t);
        set_global("flipper_moving_up", 1==1, t);
     }else if !is_key_pressed(32) && flipper_moving_up && !flipper_moving {
        print("option 2");
         spawn_form_timed("flipper_moving_down", "flipper", t);
         print("c");
         restart_colls(t);
         print("d");
         set_global("flipper_moving_up", 0==1, t);
         
         print("e");
    }
 }
"""
    on_collide_code = """
def on_collide(t, ball_id){
    let n_border_colls = read_global("n_border_colls");
    set_global("n_border_colls", n_border_colls + 1, t);
    if !read_global("hidden_circle_spawned") && 1==0 {
        print("spawning hidden circle");
        show_named_form("hidden_circle", "hidden_circle");
        set_global("hidden_circle_spawned", 1==1, t);
    }
}
"""
# while True:
#     for evt in pygame.event.get():
#         if evt.type == pygame.KEYDOWN:
#             print(f"key was pressed: {evt.key}")
#     continue
    def on_update(game: PinballGame, screen):
        run_update_function(on_update_code, game, "on_update", screen)
    def on_update_pseudo(game: PinballGame):
        funcs = get_update_functions(game, globals)
        # ballang_funcs = parse_file(on_update_code, funcs)
        # on_update = ballang_funcs.get("on_update")
        # print(f"on_update: {on_update}")
        # #assert isinstance(on_update, Function)
        # on_update()
        # print("executed on_update")
        flipper_moving_up = funcs["read_global"]("flipper_moving_up")
        t = funcs["calc_time"]()
        flipper_moving = funcs["is_moving"]("flipper", t)
        #print("a")
        if funcs["is_key_pressed"](32) and not flipper_moving_up and not flipper_moving:
            print("option 1")
            funcs["spawn_form_timed"]("flipper_moving_up", "flipper")
            print("c")
            funcs["restart_colls"](t)
            print("d")
            funcs["set_global"]("flipper_moving_up", 1==1)
            print("e")
        elif not funcs["is_key_pressed"](32) and flipper_moving_up and not flipper_moving:
            print("option 2")
            funcs["spawn_form_timed"]("flipper_moving_down", "flipper")
            print("c")
            funcs["restart_colls"](t)
            print("d")
            funcs["set_global"]("flipper_moving_up", 0==1)
            print("e")
    def on_update_python(game: PinballGame):

        global flipper_moving_up
        flipper = game.curr_forms.get_named_form("flipper")
        assert isinstance(flipper, TempForm)
        move_ended = game.calc_time() > flipper.form_duration
        if pygame.K_SPACE in game.curr_pressed and not flipper_moving_up and move_ended:
            print("a")
            t = game.calc_time()
            curr_state = game.coll_thread.check_coll(t, None)
            if curr_state is not None:
                game.balls, game.curr_forms, _, _ = curr_state
            # stop_process(coll_process, stop_event)
            game.curr_forms = game.curr_forms.clone()
            game.curr_forms.set_named_form("flipper", make_flipper(
                flipper_line, Vec(100, 720), 1, 0, 3, False, t))
            # flipper.set(make_flipper(flipper_line, Vec(100, 620), 1, 0, 1, False, t))
            game.restart_colls(t)
            flipper_moving_up = True
        elif pygame.K_SPACE not in game.curr_pressed and flipper_moving_up and move_ended:
            print("b")
            t = game.calc_time()
            curr_state = game.coll_thread.check_coll(t, None)
            if curr_state is not None:
                game.balls, game.curr_forms, _, _ = curr_state
            # stop_process(coll_process, stop_event)
            game.curr_forms = game.curr_forms.clone()
            game.curr_forms.set_named_form("flipper", make_flipper(
                flipper_line, Vec(100, 720), 1, 0, 10, True, t))
            # flipper.set(make_flipper(flipper_line, Vec(100, 620), 1, 0, 1, True, t))
            game.restart_colls(t)

            flipper_moving_up = False
    def on_keydown(key: int, game: PinballGame):
        if key == pygame.K_f:
            # global speed
            game.last_time = game.calc_time()
            game.start_time = time.time_ns()
            game.speed -= 0.1
        # if key is the letter "s", make game slower
        if key == pygame.K_s:
            # global speed
            game.last_time = game.calc_time()
            game.start_time = time.time_ns()
            game.speed += 0.1

            print(f"speed: {game.speed}")
        # if key is the letter "r", reset n_colls
        if key == pygame.K_r:
            game.n_colls = 0
    if False:
        coll_fns = {"on_collide": prepare_coll_function(on_collide_code, "on_collide")}
        game = PinballGame(start_state=GameState(start_forms, balls, globals),
                        on_keydown=on_keydown, on_update=on_update, coll_fns=coll_fns, speed=9.0)
    else:
        world = World("level/level1.json")
        #forms, ballang_funcs = world.get_forms()
        #print(f"ballang_funcs: {ballang_funcs}")
        game = world.parse_game()
    k = 0
    # curr_pressed.add(pygame.K_SPACE)
    while running:
        #print(f"globals: {game.curr_state.ballang_vars}")
        print(f"passed: {game.calc_time()}")
        if not game.update(screen=screen):
            print("end")
            break
        pygame.display.flip()
        clock.tick(60)

    pygame.quit()
    game.coll_thread.stop()
    # coll_process.join()