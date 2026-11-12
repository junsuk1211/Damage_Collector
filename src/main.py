"""시작 메뉴와 게임 화면을 전환한다."""

import argparse
from pathlib import Path
from time import perf_counter

import pico2d
from sdl2 import SDL_GetKeyboardFocus

try:
    from .player import Player
    from .selectscreen import SelectScreen
    from .manual import Manual
    from .trainingcenter import TrainingCenter
    from .chapter1 import ChapterOne
    from .chapter2 import ChapterTwo
    from .gameover import GameOverScreen
except ImportError:
    from player import Player
    from selectscreen import SelectScreen
    from manual import Manual
    from trainingcenter import TrainingCenter
    from chapter1 import ChapterOne
    from chapter2 import ChapterTwo
    from gameover import GameOverScreen


WIDTH, HEIGHT = 1280, 720
TRAINING_GROUND_Y = 170
ROOT = Path(__file__).resolve().parents[1]


def main(frame_limit=None):
    pico2d.open_canvas(WIDTH, HEIGHT)
    try:
        background = pico2d.load_image(str(ROOT / 'assets/backgrounds/training-yard.png'))
        mountains = pico2d.load_image(str(ROOT / 'assets/backgrounds/mountain-training.png'))
        book = Manual(ROOT / 'assets/backgrounds/underground-library.png')
        player = Player()
        player.load_image()
        menu = SelectScreen(WIDTH, HEIGHT)
        game_over = GameOverScreen(WIDTH, HEIGHT)
        menus = {'menu': menu, 'gameover': game_over}
        training = TrainingCenter(WIDTH)
        stages = {'chapter1': ChapterOne(WIDTH), 'chapter2': ChapterTwo(WIDTH)}
        rooms = {'training': training, **stages}
        retry_stage = 'chapter1'
        screen = 'menu'
        previous = perf_counter()
        running, frames = True, 0
        while running:
            now = perf_counter()
            dt = min(now - previous, 0.05)
            previous = now
            for event in pico2d.get_events():
                if event.type == pico2d.SDL_QUIT:
                    running = False
                elif event.type == pico2d.SDL_KEYDOWN and event.key == pico2d.SDLK_ESCAPE:
                    if screen == 'menu':
                        running = False
                    else:
                        screen = 'menu'
                        player.clear_input()
                elif screen in menus:
                    destination = menus[screen].handle_event(event)
                    if destination:
                        if screen == 'gameover' and destination == 'chapter1':
                            destination = retry_stage
                        screen = destination
                        if screen in rooms:
                            player = Player(ground_y=TRAINING_GROUND_Y) if screen == 'training' else Player()
                            player.load_image()
                            rooms[screen].reset()
                elif screen in rooms:
                    room = rooms[screen]
                    if (screen in stages and event.type == pico2d.SDL_KEYDOWN
                            and event.key == pico2d.SDLK_z and room.can_advance(player)):
                        screen = room.NEXT_STAGE
                        stages[screen].reset()
                        stages[screen].health = room.health
                        player = Player()
                        player.load_image()
                        continue
                    if room.can_start_action(event, player):
                        player.handle_event(event)
                    room.handle_event(event, player)
            # 다른 창으로 전환할 때 키 해제 이벤트를 놓쳐도 계속 걷지 않는다.
            if not SDL_GetKeyboardFocus():
                player.clear_input()
                if screen in rooms:
                    rooms[screen].cancel_aim()
            if not running:
                break
            if screen in rooms:
                previous_attack_time = player.attack_time
                previous_action_time = player.action_time
                room = rooms[screen]
                platforms = room.platforms if screen in stages else ()
                boxes = room.solid_obstacles if screen in stages else ()
                player.update(dt, room.width, platforms, boxes)
                room.update(dt, player, previous_attack_time, previous_action_time)
                if screen in stages and not room.health:
                    retry_stage = screen
                    screen = 'gameover'
            pico2d.clear_canvas()
            if screen in menus:
                menus[screen].draw()
            elif screen == 'instructions':
                book.draw(WIDTH, HEIGHT)
            elif screen in rooms:
                room = rooms[screen]
                room.camera_x = max(0.0, min(room.width - WIDTH, player.x - WIDTH / 2))
                player.camera_x = room.camera_x
                if screen == 'training':
                    mountains.draw(WIDTH / 2, HEIGHT / 2, WIDTH, HEIGHT)
                else:
                    if room.camera_x < WIDTH:
                        background.draw(WIDTH / 2 - room.camera_x, HEIGHT / 2, WIDTH, HEIGHT)
                    if room.camera_x > 0:
                        background.composite_draw(0, 'h', WIDTH * 1.5 - room.camera_x,
                                                  HEIGHT / 2, WIDTH, HEIGHT)
                    room.draw_props()
                room.draw_dummy()
                if screen not in stages or int(room.hurt_time * 16) % 2 == 0:
                    player.draw()
                room.draw_banner(WIDTH, HEIGHT, player)
            pico2d.update_canvas()
            pico2d.delay(0.001)
            frames += 1
            if frame_limit is not None and frames >= frame_limit:
                break
    finally:
        pico2d.close_canvas()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--frames', type=int, help='실행 확인 후 지정 프레임에 종료')
    main(parser.parse_args().frames)
