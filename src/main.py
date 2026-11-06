"""방향키로 주인공의 크기와 이동을 확인하는 실행 화면."""

import argparse
from pathlib import Path
from time import perf_counter

import pico2d
from sdl2 import SDL_GetKeyboardFocus

try:
    from .player import Player
except ImportError:
    from player import Player


WIDTH, HEIGHT = 1280, 720
ROOT = Path(__file__).resolve().parents[1]


def main(frame_limit=None):
    pico2d.open_canvas(WIDTH, HEIGHT)
    try:
        background = pico2d.load_image(str(ROOT / 'assets/backgrounds/training-yard.png'))
        player = Player()
        player.load_image()
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
                    running = False
                else:
                    player.handle_event(event)
            # 다른 창으로 전환할 때 키 해제 이벤트를 놓쳐도 계속 걷지 않는다.
            if not SDL_GetKeyboardFocus():
                player.clear_input()
            if not running:
                break
            player.update(dt, WIDTH)
            pico2d.clear_canvas()
            background.draw(WIDTH / 2, HEIGHT / 2, WIDTH, HEIGHT)
            player.draw()
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
