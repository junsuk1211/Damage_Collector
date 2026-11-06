"""주인공의 좌우 이동과 화면 표시."""

from pathlib import Path

import pico2d


ASSET_PATH = Path(__file__).resolve().parents[1] / 'assets' / 'characters' / 'player.png'


class Player:
    def __init__(self, x=240.0, ground_y=144.0, height=96, speed=260.0):
        self.x = float(x)
        self.ground_y = ground_y
        self.height = height
        self.speed = speed  # 초당 이동 거리(픽셀)
        self.facing = 1
        self._pressed = set()
        self.image = None
        self.width = float(height)

    def load_image(self):
        # 캔버스를 연 다음 호출한다.
        self.image = pico2d.load_image(str(ASSET_PATH))
        self.width = self.height * self.image.w / self.image.h

    def handle_event(self, event):
        if event.type == pico2d.SDL_KEYDOWN:
            if event.key in (pico2d.SDLK_LEFT, pico2d.SDLK_RIGHT):
                self._pressed.add(event.key)
        elif event.type == pico2d.SDL_KEYUP:
            self._pressed.discard(event.key)

    def clear_input(self):
        self._pressed.clear()

    def update(self, dt, world_width):
        direction = int(pico2d.SDLK_RIGHT in self._pressed) - int(
            pico2d.SDLK_LEFT in self._pressed
        )
        if direction:
            self.facing = direction
        self.x += direction * self.speed * max(0.0, dt)
        half_width = min(self.width / 2, world_width / 2)
        self.x = max(half_width, min(world_width - half_width, self.x))

    def draw(self):
        if self.image is None:
            raise RuntimeError('캔버스를 연 뒤 load_image()를 먼저 호출하세요.')
        self.image.composite_draw(
            0, 'h' if self.facing < 0 else '',
            self.x, self.ground_y + self.height / 2,
            self.width, self.height,
        )
