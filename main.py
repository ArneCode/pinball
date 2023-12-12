from __future__ import annotations
import math
import time
import pygame
from pygame.math import Vector2
from ball import Ball
from form import CircleForm, FormHandler, LineForm
from interval import SimpleInterval
from polynom import Polynom
from vec import Vec

def sin(k):
    x = Polynom([0, 1])
    sum = Polynom([0])
    for i in range(k):
        a = [0,1,0,-1][i%4]
        sum += (x**i)*(a/math.factorial(i))
    return sum
def cos(k):
    x = Polynom([0, 1])
    sum = Polynom([0])
    for i in range(k):
        a = [1,0,-1,0][i%4]
        sum += (x**i)*(a/math.factorial(i))
    return sum


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
    ball = Ball(Vec(100, 100), 50, "red").with_acc(Vec(0, 90.8)).with_vel(Vec(
        111, 0
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
    # bahn = ball.gen_flugbahn(-9.8, 6)
    start_time = time.time_ns()
    coll = form_handler.find_collision(ball)
    passed = (time.time_ns() - start_time)/(10**6)
    print(f"calculating took {passed} ms")
    print(f"coll_t: {coll.time}")
    k = 0
    while running:
        screen.fill("black")
        # poll for events
        # pygame.QUIT event means the user clicked X to close your window
        passed = (time.time_ns() - start_time)/(10**(8))
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
        # draw sine line
        pts = []
        k = int(passed // 1)
        f = sin(k)
        for i in range(0,1280,1):
            x = (i-640)/10
            pts.append((i, 360+f.apply(x)*100))
        pygame.draw.lines(screen, (255, 0, 0), False, pts, 1)
        #print(f"pts: {pts}")
        print(f"k: {k//2}")
        pygame.display.flip()
        continue
        # fill the screen with a color to wipe away anything from last frame
        screen.fill("black")

        # ball.update(dt)
        passed = (time.time_ns() - start_time)/(10**(8))
        # ball.pos_0 = bahn.get_pos(passed)
        if coll is not None and passed > coll.time + ball.start_t:
            dir = coll.get_result_dir()  # *(-50)
            ball = ball.with_start_t(passed).with_start_pos(
                ball.get_pos(coll.time+ball.start_t - 0.001)).with_vel(dir*(1))  # .with_acc(Vec(0.0, 0.0))
            print(f"ball pos: {ball.pos_0}, actually: {ball.get_pos(passed)}")
            coll = form_handler.find_collision(ball)
            #coll.time = float("inf")
            if coll is None:
                print("found no collision")
            else:
                i += 1
                print(f"found coll: {coll.time}, i: {i}")


        # screen.fill("black")
        # boden.draw(screen, (0, 255, 0))
        # continue

        # RENDER YOUR GAME HERE
        form_handler.draw(screen, (0, 255, 0))
        ball.draw(passed, screen)
        # flip() the display to put your work on screen
        pygame.display.flip()
        clock.tick(60)

    pygame.quit()
