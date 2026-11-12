"""주인공의 이동, 단검 공격 동작, 화면 표시."""

from bisect import bisect_right
from pathlib import Path

import pico2d

try:
    from .terrain import stop_at_boxes
except ImportError:
    from terrain import stop_at_boxes


ASSET_PATH = Path(__file__).resolve().parents[1] / 'assets' / 'characters' / 'player-motion.png'
WALK_FRAME_TIME = 0.085
ATTACK_FRAME_ENDS = (0.10, 0.18, 0.28, 0.40)
ABILITY_PATH = ASSET_PATH.with_name('player-abilities.png')
NUMBER_MOTION_PATH = ASSET_PATH.with_name('number-motion.png')
JUMP_FRAME_ENDS = (0.08, 0.34, 0.60, 0.70)
JUMP_HEIGHT = 112
GROUND_ACTIONS = {
    pico2d.SDLK_c: (1, (0.09, 0.22, 0.34, 0.46)),
    pico2d.SDLK_v: (2, (0.12, 0.19, 0.28, 0.42)),
    pico2d.SDLK_LSHIFT: (3, (0.07, 0.16, 0.25, 0.36)),
}
DODGE_SPEED = 460
BODY_HALF_WIDTH = 14


class Player:
    def __init__(self, x=240.0, ground_y=144.0, height=96, speed=260.0):
        self.x = float(x)
        self.ground_y = ground_y
        self.floor_y = ground_y
        self.fall_speed = 0.0
        self.camera_x = 0.0
        self.height = height
        self.speed = speed  # 초당 이동 거리(픽셀)
        self.facing = 1
        self._pressed = set()
        self.image = None
        self.abilities = None
        self.number_motion = None
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
        self.number_motion = pico2d.load_image(str(NUMBER_MOTION_PATH))
        self.width = self.height * (self.image.w // 4) / (self.image.h // 2)

    def handle_event(self, event):
        if event.type == pico2d.SDL_KEYDOWN:
            if event.key in (pico2d.SDLK_LEFT, pico2d.SDLK_RIGHT):
                self._pressed.add(event.key)
            elif self.attack_time is None and self.jump_time is None and self.ground_action is None:
                if event.key == pico2d.SDLK_x:
                    self.attack_time = 0.0
                    self.walk_time = 0.0
                elif event.key == pico2d.SDLK_UP and not self.fall_speed:
                    self.jump_time = 0.0
                    self.walk_time = 0.0
                elif event.key in GROUND_ACTIONS:
                    self.start_ground_action(event.key)
        elif event.type == pico2d.SDL_KEYUP:
            self._pressed.discard(event.key)

    def start_ground_action(self, key):
        if (self.attack_time is not None or self.ground_action is not None
                or (self.jump_time is not None and key != pico2d.SDLK_v)):
            return False
        self.ground_action = GROUND_ACTIONS[key]
        self.action_time = 0.0
        self.walk_time = 0.0
        return True

    def clear_input(self):
        self._pressed.clear()

    def update(self, dt, world_width, platforms=(), boxes=()):
        previous_feet = self.ground_y + self.jump_lift
        self.update_motion(dt, world_width, boxes)
        if not platforms and not boxes:
            return
        box_tops = ((left - BODY_HALF_WIDTH, right + BODY_HALF_WIDTH, top)
                    for left, right, top in boxes)
        support = max((top for left, right, top in (*platforms, *box_tops)
                       if left < self.x < right and top <= previous_feet),
                      default=self.floor_y)
        if self.jump_time is not None:
            feet = self.ground_y + self.jump_lift
            if self.jump_time >= JUMP_FRAME_ENDS[1] and feet <= support <= previous_feet:
                self.ground_y = support
                self.jump_time = None
                self.walk_time = 0.0
        elif self.ground_y > support:
            self.fall_speed += 900 * dt
            self.ground_y = max(support, self.ground_y - self.fall_speed * dt)
        if self.ground_y == support:
            self.fall_speed = 0.0

    def update_motion(self, dt, world_width, boxes=()):
        dt = max(0.0, dt)
        if self.jump_time is not None:
            self.jump_time += dt
            if self.jump_time >= JUMP_FRAME_ENDS[-1]:
                self.jump_time = None
        if self.ground_action is not None:
            row, ends = self.ground_action
            if row == 3:
                self.move_horizontal(
                    self.facing * DODGE_SPEED * min(dt, ends[-1] - self.action_time),
                    world_width, boxes,
                )
            self.action_time += dt
            if self.action_time >= ends[-1]:
                self.ground_action = None
            return
        if self.attack_time is not None:
            self.attack_time += dt
            if self.attack_time >= ATTACK_FRAME_ENDS[-1]:
                self.attack_time = None
            return
        direction = int(pico2d.SDLK_RIGHT in self._pressed) - int(
            pico2d.SDLK_LEFT in self._pressed
        )
        if direction:
            self.facing = direction
        previous_x = self.x
        self.move_horizontal(direction * self.speed * dt, world_width, boxes)
        self.walk_time = self.walk_time + dt if self.x != previous_x else 0.0

    def move_horizontal(self, distance, world_width, boxes=()):
        half_width = min(self.width / 2, world_width / 2)
        next_x = max(half_width, min(world_width - half_width, self.x + distance))
        feet = self.ground_y + self.jump_lift
        self.x = stop_at_boxes(self.x, next_x, feet, BODY_HALF_WIDTH, boxes)

    def draw_motion(self, frame, row, *, ability=False, lift=0, number_motion=False):
        image, rows = (self.abilities, 4) if ability else (self.image, 2)
        if number_motion:
            image = self.number_motion
            row -= 1
        cell_width = image.w // 4
        cell_height = image.h // rows
        # 셀 아래의 투명 여백을 빼서 발을 바닥선에 맞춘다.
        foot_padding = self.height * (0.13 if ability else 0.095)
        if number_motion:
            foot_padding = self.height * 0.055
        image.clip_composite_draw(
            frame * cell_width, (rows - 1 - row) * cell_height, cell_width, cell_height,
            0, 'h' if self.facing < 0 else '',
            self.x - self.camera_x, self.ground_y + self.height / 2 - foot_padding + lift,
            self.height * cell_width / cell_height, self.height,
        )

    @property
    def jump_lift(self):
        if self.jump_time is None:
            return 0.0
        takeoff, _, landing, _ = JUMP_FRAME_ENDS
        progress = min(1.0, max(0.0, (self.jump_time - takeoff) / (landing - takeoff)))
        return 4 * JUMP_HEIGHT * progress * (1 - progress)

    def draw(self):
        if self.image is None:
            raise RuntimeError('캔버스를 연 뒤 load_image()를 먼저 호출하세요.')
        if self.ground_action is not None:
            row, ends = self.ground_action
            self.draw_motion(bisect_right(ends, self.action_time), row, ability=True, lift=self.jump_lift,
                             number_motion=row in (1, 2))
            return
        if self.attack_time is not None:
            self.draw_motion(bisect_right(ATTACK_FRAME_ENDS, self.attack_time), row=1)
            return
        if self.jump_time is not None:
            frame = bisect_right(JUMP_FRAME_ENDS, self.jump_time)
            self.draw_motion(frame, row=0, ability=True, lift=self.jump_lift)
            return
        if self.walk_time:
            self.draw_motion(int(self.walk_time / WALK_FRAME_TIME) % 4, row=0)
            return
        self.draw_motion(3, row=1)
