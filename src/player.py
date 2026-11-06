"""주인공의 이동, 단검 공격 동작, 화면 표시."""

from bisect import bisect_right
from pathlib import Path

import pico2d


ASSET_PATH = Path(__file__).resolve().parents[1] / 'assets' / 'characters' / 'player-motion.png'
WALK_FRAME_TIME = 0.085
ATTACK_FRAME_ENDS = (0.10, 0.18, 0.28, 0.40)
ABILITY_PATH = ASSET_PATH.with_name('player-abilities.png')
JUMP_FRAME_ENDS = (0.08, 0.34, 0.60, 0.70)
JUMP_HEIGHT = 112
GROUND_ACTIONS = {
    pico2d.SDLK_c: (1, (0.09, 0.22, 0.34, 0.46)),
    pico2d.SDLK_v: (2, (0.12, 0.19, 0.28, 0.42)),
}


class Player:
    def __init__(self, x=240.0, ground_y=144.0, height=96, speed=260.0):
        self.x = float(x)
        self.ground_y = ground_y
        self.height = height
        self.speed = speed  # 초당 이동 거리(픽셀)
        self.facing = 1
        self._pressed = set()
        self.image = None
        self.abilities = None
        self.walk_time = 0.0
        self.attack_time = None
        self.jump_time = None
        self.ground_action = None
        self.action_time = 0.0
        self.width = float(height)

    def load_image(self):
        # 캔버스를 연 다음 호출한다.
        self.image = pico2d.load_image(str(ASSET_PATH))
        self.abilities = pico2d.load_image(str(ABILITY_PATH))
        self.width = self.height * (self.image.w // 4) / (self.image.h // 2)

    def handle_event(self, event):
        if event.type == pico2d.SDL_KEYDOWN:
            if event.key in (pico2d.SDLK_LEFT, pico2d.SDLK_RIGHT):
                self._pressed.add(event.key)
            elif self.attack_time is None and self.jump_time is None and self.ground_action is None:
                if event.key == pico2d.SDLK_x:
                    self.attack_time = 0.0
                    self.walk_time = 0.0
                elif event.key == pico2d.SDLK_SPACE:
                    self.jump_time = 0.0
                    self.walk_time = 0.0
                elif event.key in GROUND_ACTIONS:
                    self.ground_action = GROUND_ACTIONS[event.key]
                    self.action_time = 0.0
                    self.walk_time = 0.0
        elif event.type == pico2d.SDL_KEYUP:
            self._pressed.discard(event.key)

    def clear_input(self):
        self._pressed.clear()

    def update(self, dt, world_width):
        dt = max(0.0, dt)
        if self.ground_action is not None:
            _, ends = self.ground_action
            self.action_time += dt
            if self.action_time >= ends[-1]:
                self.ground_action = None
            return
        if self.attack_time is not None:
            self.attack_time += dt
            if self.attack_time >= ATTACK_FRAME_ENDS[-1]:
                self.attack_time = None
            return
        if self.jump_time is not None:
            self.jump_time += dt
            if self.jump_time >= JUMP_FRAME_ENDS[-1]:
                self.jump_time = None
        direction = int(pico2d.SDLK_RIGHT in self._pressed) - int(
            pico2d.SDLK_LEFT in self._pressed
        )
        if direction:
            self.facing = direction
        previous_x = self.x
        self.x += direction * self.speed * dt
        half_width = min(self.width / 2, world_width / 2)
        self.x = max(half_width, min(world_width - half_width, self.x))
        self.walk_time = self.walk_time + dt if self.x != previous_x else 0.0

    def draw_motion(self, frame, row, *, ability=False, lift=0):
        image, rows = (self.abilities, 4) if ability else (self.image, 2)
        cell_width = image.w // 4
        cell_height = image.h // rows
        # 셀 아래의 투명 여백을 빼서 발을 바닥선에 맞춘다.
        foot_padding = self.height * (0.13 if ability else 0.095)
        image.clip_composite_draw(
            frame * cell_width, (rows - 1 - row) * cell_height, cell_width, cell_height,
            0, 'h' if self.facing < 0 else '',
            self.x, self.ground_y + self.height / 2 - foot_padding + lift,
            self.height * cell_width / cell_height, self.height,
        )

    def draw(self):
        if self.image is None:
            raise RuntimeError('캔버스를 연 뒤 load_image()를 먼저 호출하세요.')
        if self.ground_action is not None:
            row, ends = self.ground_action
            self.draw_motion(bisect_right(ends, self.action_time), row, ability=True)
            return
        if self.attack_time is not None:
            self.draw_motion(bisect_right(ATTACK_FRAME_ENDS, self.attack_time), row=1)
            return
        if self.jump_time is not None:
            frame = bisect_right(JUMP_FRAME_ENDS, self.jump_time)
            takeoff, _, landing, _ = JUMP_FRAME_ENDS
            progress = min(1.0, max(0.0, (self.jump_time - takeoff) / (landing - takeoff)))
            lift = 4 * JUMP_HEIGHT * progress * (1 - progress)
            self.draw_motion(frame, row=0, ability=True, lift=lift)
            return
        if self.walk_time:
            self.draw_motion(int(self.walk_time / WALK_FRAME_TIME) % 4, row=0)
            return
        self.draw_motion(3, row=1)
