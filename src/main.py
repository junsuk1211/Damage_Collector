"""시작 메뉴와 게임 화면을 전환한다."""

import argparse
from pathlib import Path
from time import perf_counter

import pico2d
from sdl2 import SDL_GetKeyboardFocus

try:
    from .player import Player
    from .selectscreen import SelectScreen, fill
    from .trainingcenter import TrainingCenter
except ImportError:
    from player import Player
    from selectscreen import SelectScreen, fill
    from trainingcenter import TrainingCenter


WIDTH, HEIGHT = 1280, 720
ROOT = Path(__file__).resolve().parents[1]


def main(frame_limit=None):
    pico2d.open_canvas(WIDTH, HEIGHT)
    try:
        background = pico2d.load_image(str(ROOT / 'assets/backgrounds/training-yard.png'))
        player = Player()
        player.load_image()
        menu = SelectScreen(WIDTH, HEIGHT)
        training = TrainingCenter()
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
                elif screen == 'menu':
                    destination = menu.handle_event(event)
                    if destination:
                        screen = destination
                        if screen in ('chapter1', 'training'):
                            player = Player()
                            player.load_image()
                        if screen == 'training':
                            training.reset()
                elif screen in ('chapter1', 'training'):
                    player.handle_event(event)
                    if screen == 'training':
                        training.handle_event(event, player)
            # 다른 창으로 전환할 때 키 해제 이벤트를 놓쳐도 계속 걷지 않는다.
            if not SDL_GetKeyboardFocus():
                player.clear_input()
            if not running:
                break
            if screen in ('chapter1', 'training'):
                previous_attack_time = player.attack_time
                player.update(dt, WIDTH)
                if screen == 'training':
                    training.update(dt, player, previous_attack_time)
            pico2d.clear_canvas()
            background.draw(WIDTH / 2, HEIGHT / 2, WIDTH, HEIGHT)
            if screen == 'menu':
                menu.draw()
            elif screen == 'instructions':
                fill(320, 145, 640, 430, (19, 25, 42))
                menu.font.draw(350, 535, '설명', (255, 230, 177))
            else:
                if screen == 'training':
                    training.draw_dummy()
                player.draw()
                if screen == 'training':
                    training.draw_banner(WIDTH, HEIGHT)
                else:
                    menu.font.draw(24, HEIGHT - 28, '챕터 1', (255, 230, 177))
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
