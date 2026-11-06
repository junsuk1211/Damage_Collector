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
    from .gameover import GameOverScreen
except ImportError:
    from player import Player
    from selectscreen import SelectScreen
    from manual import Manual
    from trainingcenter import TrainingCenter
    from chapter1 import ChapterOne
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
        chapter = ChapterOne(WIDTH)
        rooms = {'training': training, 'chapter1': chapter}
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
                        screen = destination
                        if screen in ('chapter1', 'training'):
                            player = Player(ground_y=TRAINING_GROUND_Y) if screen == 'training' else Player()
                            player.load_image()
                            rooms[screen].reset()
                elif screen in rooms and (screen != 'chapter1' or chapter.health):
                    room = rooms[screen]
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
            if screen in rooms and (screen != 'chapter1' or chapter.health):
                previous_attack_time = player.attack_time
                previous_action_time = player.action_time
                player.update(dt, WIDTH)
                rooms[screen].update(dt, player, previous_attack_time, previous_action_time)
                if screen == 'chapter1' and not chapter.health:
                    screen = 'gameover'
            pico2d.clear_canvas()
            if screen in menus:
                menus[screen].draw()
            elif screen == 'instructions':
                book.draw(WIDTH, HEIGHT)
            elif screen in rooms:
                scene = mountains if screen == 'training' else background
                scene.draw(WIDTH / 2, HEIGHT / 2, WIDTH, HEIGHT)
                room = rooms[screen]
                room.draw_dummy()
                if screen != 'chapter1' or not chapter.health or int(chapter.hurt_time * 16) % 2 == 0:
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
