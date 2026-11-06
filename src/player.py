"""주인공의 좌우 이동과 화면 표시."""

from pathlib import Path

import pico2d


ASSET_PATH = Path(__file__).resolve().parents[1] / 'assets' / 'characters' / 'player-motion.png'
WALK_FRAME_TIME = 0.085


class Player:
    def __init__(self, x=240.0, ground_y=144.0, height=96, speed=260.0):
        self.x = float(x)
        self.ground_y = ground_y
        self.height = height
        self.speed = speed  # 초당 이동 거리(픽셀)
        self.facing = 1
        self._pressed = set()
        self.image = None
        self.walk_time = 0.0
        self.width = float(height)

    def load_image(self):
        # 캔버스를 연 다음 호출한다.
        self.image = pico2d.load_image(str(ASSET_PATH))
        self.width = self.height * (self.image.w // 4) / (self.image.h // 2)

    def handle_event(self, event):
        if event.type == pico2d.SDL_KEYDOWN:
            if event.key in (pico2d.SDLK_LEFT, pico2d.SDLK_RIGHT):
                self._pressed.add(event.key)
        elif event.type == pico2d.SDL_KEYUP:
            self._pressed.discard(event.key)

    def clear_input(self):
        self._pressed.clear()

    def update(self, dt, world_width):
        dt = max(0.0, dt)
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

    def draw_motion(self, frame, row):
        cell_width = self.image.w // 4
        cell_height = self.image.h // 2
        # 셀 아래의 투명 여백을 빼서 발을 바닥선에 맞춘다.
        foot_padding = self.height * 0.095
        self.image.clip_composite_draw(
            frame * cell_width, (1 - row) * cell_height, cell_width, cell_height,
            0, 'h' if self.facing < 0 else '',
            self.x, self.ground_y + self.height / 2 - foot_padding,
            self.width, self.height,
        )

    def draw(self):
        if self.image is None:
            raise RuntimeError('캔버스를 연 뒤 load_image()를 먼저 호출하세요.')
        if self.walk_time:
            self.draw_motion(int(self.walk_time / WALK_FRAME_TIME) % 4, row=0)
            return
        self.draw_motion(3, row=1)
