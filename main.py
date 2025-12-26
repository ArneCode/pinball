"""
Run the game
"""
from __future__ import annotations
import pygame
from objects.material import Material
from read_world import World
from screen import Button, Screen, ScreenHandler

normal_material = Material(0.8, 0.95, 20, 1)
flipper_material = Material(1.1, 1.0, 40, 0.0)
speed = 8.0


if __name__ == "__main__":
    # pygame setup
    pygame.init()
    screen = pygame.display.set_mode((720, 1000))

    clock = pygame.time.Clock()
    # clock.tick(60)  # limits FPS to 60
    running = True
    i = 0

    world = World("level/level2.json")
    # forms, ballang_funcs = world.get_forms()
    # print(f"ballang_funcs: {ballang_funcs}")
    game = world.parse_game()

    USE_ROTATING = True
    if not USE_ROTATING:
        game.curr_state.forms.hide_named_form("rotating")
    USE_MENUE = False
    if USE_MENUE:
        game.pause()
        kill_screen = Screen("kill_screen", None, color=(0, 0, 0))
        game_screen = Screen("game", lambda screen: game.update(screen))
        menu_screen = Screen("menu", None, color=(0, 0, 255))

        def play_fn():
            game.unpause()
            game_screen.makeScreen()
        game_button = Button(30, 30, 400, 100, play_fn, 'Play')
        menu_buttons = [game_button]

        def pause():
            game.pause()
            menu_screen.makeScreen()
        pause_button = Button(300, 00, 100, 45, pause, "Pause")
        game_buttons = [pause_button]

        kill_button = Button(
            30, 30, 400, 100, menu_screen.makeScreen, "Return to Menu")
        kill_buttons = [kill_button]
        kill_screen.setButtons(kill_buttons)
        menu_screen.setButtons(menu_buttons)
        game_screen.setButtons(game_buttons)

        Screen_list = [menu_screen, game_screen, kill_screen]
        Handler = ScreenHandler(Screen_list)
        k = 0
        # curr_pressed.add(pygame.K_SPACE)
        win = kill_screen.makeScreen()
        while running:

            if game_screen.checkState():
                game_screen.runFunction(screen)
            Handler.update(screen)
            for event in pygame.event.get():
                Handler.handle_event(event)
                game.handle_event(event)

            # if not game.update(screen=screen):
            #     break
            pygame.display.flip()
            clock.tick(60)
        # curr_pressed.add(pygame.K_SPACE)
    while running:
        # print(f"globals: {game.curr_state.ballang_vars}")
        print(f"passed: {game.calc_time()}")
        if not game.update(screen=screen):
            print("end")
            break
        pygame.display.flip()
        clock.tick(60)

    pygame.quit()
    game.coll_thread.stop()
    # coll_process.join()
