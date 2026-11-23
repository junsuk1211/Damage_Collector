"""시작 메뉴와 게임 화면을 전환한다."""

import argparse
import faulthandler
import os
from pathlib import Path
import sys
from time import perf_counter

ROOT = Path(__file__).resolve().parents[1]
startup_log = None
if __name__ == '__main__':
    log_path = ROOT / f'startup-{os.getpid()}.log'
    startup_log = log_path.open('w', encoding='utf-8', buffering=1)
    startup_log.write(f'Python {sys.version}\nImporting pico2d and game modules\n')
    faulthandler.enable(file=startup_log)
    faulthandler.dump_traceback_later(15, file=startup_log, exit=True)
    print(f'시작 진단 파일: {log_path.name}', flush=True)

import pico2d
from sdl2 import SDL_GetKeyboardFocus

try:
    from .player import Player
    from .selectscreen import SelectScreen
    from .manual import Manual
    from .trainingcenter import TrainingCenter
    from .chapter1 import ChapterOne
    from .chapter2 import ChapterTwo
    from .chapter3 import ChapterThree
    from .gameover import GameOverScreen
    from .upgrades import UpgradeScreen
except ImportError:
    from player import Player
    from selectscreen import SelectScreen
    from manual import Manual
    from trainingcenter import TrainingCenter
    from chapter1 import ChapterOne
    from chapter2 import ChapterTwo
    from chapter3 import ChapterThree
    from gameover import GameOverScreen
    from upgrades import UpgradeScreen


WIDTH, HEIGHT = 1280, 720
FRAME_INTERVAL = 1 / 60
TRAINING_GROUND_Y = 170


def main(frame_limit=None):
    # 게임에서 소리를 재생하지 않으므로 Windows 오디오 장치를 열지 않는다.
    if sys.platform == 'win32':
        os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')
    if startup_log:
        startup_log.write('Opening SDL window\n')
    pico2d.open_canvas(WIDTH, HEIGHT)
    try:
        if startup_log:
            startup_log.write('Loading game assets\n')
        backgrounds = {
            'chapter1': pico2d.load_image(str(ROOT / 'assets/backgrounds/training-yard.png')),
            'chapter2': pico2d.load_image(str(ROOT / 'assets/backgrounds/castle-corridor.png')),
            'chapter3': pico2d.load_image(str(ROOT / 'assets/backgrounds/castle-rampart.png')),
        }
        mountains = pico2d.load_image(str(ROOT / 'assets/backgrounds/mountain-training.png'))
        book = Manual(ROOT / 'assets/backgrounds/underground-library.png')
        player = Player()
        player.load_image()
        menu = SelectScreen(WIDTH, HEIGHT)
        game_over = GameOverScreen(WIDTH, HEIGHT)
        menus = {'menu': menu, 'gameover': game_over}
        training = TrainingCenter(WIDTH)
        stages = {'chapter1': ChapterOne(WIDTH), 'chapter2': ChapterTwo(WIDTH),
                  'chapter3': ChapterThree(WIDTH)}
        rooms = {'training': training, **stages}
        retry_stage = 'chapter1'
        upgrade_screen = None
        next_stage = None
        used_upgrades = set()
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
                        if screen == 'chapter1':
                            used_upgrades.clear()
                        if screen in rooms:
                            player = Player(ground_y=TRAINING_GROUND_Y) if screen == 'training' else Player()
                            player.load_image()
                            rooms[screen].reset()
                            if screen == next_stage and upgrade_screen is not None:
                                upgrade_screen.apply(stages[screen])
                elif screen == 'upgrades':
                    if upgrade_screen.handle_event(event):
                        screen = next_stage
                        stages[screen].reset()
                        upgrade_screen.apply(stages[screen])
                        used_upgrades.update(upgrade_screen.cards)
                        player = Player()
                        player.load_image()
                elif screen in rooms:
                    room = rooms[screen]
                    if (screen in stages and event.type == pico2d.SDL_KEYDOWN
                            and event.key == pico2d.SDLK_z and room.can_advance(player)):
                        next_stage = room.NEXT_STAGE
                        upgrade_screen = UpgradeScreen(HEIGHT, room.health, room.MAX_HEALTH, used_upgrades)
                        screen = 'upgrades'
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
            elif screen == 'upgrades':
                upgrade_screen.draw()
            elif screen == 'instructions':
                book.draw(WIDTH, HEIGHT)
            elif screen in rooms:
                room = rooms[screen]
                room.camera_x = max(0.0, min(room.width - WIDTH, player.x - WIDTH / 2))
                player.camera_x = room.camera_x
                if screen == 'training':
                    mountains.draw(WIDTH / 2, HEIGHT / 2, WIDTH, HEIGHT)
                else:
                    background = backgrounds[screen]
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
            frames += 1
            if frames == 1:
                if startup_log:
                    faulthandler.cancel_dump_traceback_later()
                    startup_log.write('First frame displayed\n')
                print('데미지 콜렉터 시작 화면을 열었습니다.', flush=True)
            if frame_limit is not None and frames >= frame_limit:
                break
            remaining = FRAME_INTERVAL - (perf_counter() - now)
            pico2d.delay(max(0.001, remaining))
    finally:
        pico2d.close_canvas()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--frames', type=int, help='실행 확인 후 지정 프레임에 종료')
    args = parser.parse_args()
    try:
        main(args.frames)
    finally:
        faulthandler.cancel_dump_traceback_later()
        faulthandler.disable()
        startup_log.close()
