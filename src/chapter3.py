"""증강을 적용해 진입할 수 있는 성 내부 후속 구간."""

from pathlib import Path
from math import sin

import pico2d as p

try:
    from .chapter1 import ChapterOne
    from .verysheidman import Verysheidman
    from .selectscreen import fill
except ImportError:
    from chapter1 import ChapterOne
    from verysheidman import Verysheidman
    from selectscreen import fill


class ChapterThree(ChapterOne):
    TITLE = '챕터 3  |  성벽 순찰로'
    SCREENS_WIDE = 1
    NEXT_STAGE = None
    ARROW_PLATFORM = None
    GUARD_POSITIONS = (470, 630)
    HEAVY_POSITIONS = (1090,)
    STONE_PLATFORMS = ()
    SCAFFOLDS = ()
    FIRE_VENTS = ()

    def __init__(self, width):
        super().__init__(width)
        path = Path(__file__).resolve().parents[1] / 'assets/characters/chapter3-heavy.png'
        self.heavy_image = p.load_image(str(path))
        self.thrust_image = p.load_image(str(path.with_name("chapter3-thrust.png")))

    def reset(self):
        super().reset()
        self.dummies.extend(Verysheidman(x, self.FLOOR_Y) for x in self.HEAVY_POSITIONS)

    def damage(self, enemy, amount):
        if isinstance(enemy, Verysheidman):
            enemy.take_number_damage(amount)
        else:
            super().damage(enemy, amount)

    def dagger_hit(self, enemy, amount, player):
        if isinstance(enemy, Verysheidman):
            if enemy.barrier:
                enemy.flash = 0.12
            else:
                enemy.take_number_damage(amount)
        else:
            super().dagger_hit(enemy, amount, player)

    def advance_guard(self, guard, dt, player):
        if not isinstance(guard, Verysheidman):
            super().advance_guard(guard, dt, player)
            return

        if guard.lunge_end is not None or guard.lunge_recovery:
            if guard.advance_lunge(dt, player):
                self.hurt_player(player, damage=2)
            return

        if guard.stagger:
            guard.advance(dt, player)
            if not guard.stagger:
                guard.prepare_lunge(player.x, self.width)
            return

        super().advance_guard(guard, dt, player)

    def draw_dummy(self):
        super().draw_dummy()
        cell_w, cell_h = self.heavy_image.w // 4, self.heavy_image.h // 2
        for enemy in self.dummies:
            if not isinstance(enemy, Verysheidman):
                continue
            x = enemy.x - self.camera_x
            if not -85 <= x <= self.viewport_width + 85:
                continue
            frame = enemy.thrust_frame()
            flip = 'h' if enemy.facing > 0 else ''
            if frame is None:
                column, row = enemy.sprite_cell()
                # 각 줄에서 장화 밑의 투명 여백을 제외한다.
                bottom = (1 - row) * cell_h + (35 if row == 0 else 18)
                height = cell_h - (35 if row == 0 else 18)
                draw_h = round(148 * height / cell_h)
                self.heavy_image.clip_composite_draw(
                    column * cell_w, bottom, cell_w, height, 0, flip,
                    x, enemy.y + draw_h / 2, 148, draw_h,
                )
            else:
                tile_w, tile_h = self.thrust_image.w // 3, self.thrust_image.h // 2
                row, col = divmod(frame, 3)
                # 여섯 자세 모두 장화 밑창이 셀 하단에서 13픽셀 위에 있다.
                self.thrust_image.clip_composite_draw(
                    col * tile_w, (1 - row) * tile_h + 13, tile_w, tile_h - 13,
                    0, flip, x, enemy.y + 64, round(128 * tile_w / (tile_h - 13)), 128,
                )
            self.draw_target_health(enemy, enemy.y + 131)
            if enemy.barrier:
                self.draw_barrier(enemy, x)
            elif enemy.stagger:
                self.spark_font.draw(x - 32, enemy.y + 112, '방벽 파괴', (133, 242, 255))
            elif enemy.lunge_end is not None and enemy.lunge_windup:
                self.draw_lunge_warning(enemy, x)
            if enemy.attack_age is not None and enemy.attack_age < enemy.ATTACK_HIT_TIME:
                progress = enemy.attack_age / enemy.ATTACK_HIT_TIME
                left = x if enemy.facing > 0 else x - enemy.ATTACK_REACH
                fill(left, enemy.y + 1, enemy.ATTACK_REACH, 4, (248, 81, 64))
                self.spark_font.draw(x - 5, enemy.y + 106, '!', (255, 167 - int(progress * 100), 83))

    def draw_lunge_warning(self, enemy, x):
        tip = enemy.lunge_end + enemy.facing * enemy.LUNGE_BLADE_REACH - self.camera_x
        left = int(max(0, min(x, tip)))
        right = int(min(self.viewport_width, max(x, tip)))
        y = enemy.y + enemy.LUNGE_HEIGHT
        red = (255, 105, 105) if enemy.lunge_windup < 0.22 else (255, 65, 75)
        for start in range(left, right, 22):
            length = min(13, right - start)
            fill(start, y - 3, length, 6, (100, 18, 31))
            fill(start, y - 1, length, 2, red)
        text_x = max(12, min(x - 72, self.viewport_width - 175))
        self.spark_font.draw(text_x, enemy.y + 111, '찌르기  ↑ 점프 / Shift 구르기', (255, 116, 116))

    def draw_barrier(self, enemy, x):
        edge = x + enemy.facing * 40
        color = (200, 244, 255) if enemy.flash else (79, 188, 233)
        for y in range(10, 102, 8):
            curve = 8 * sin((y - 10) / 92 * 3.14159)
            fill(edge + enemy.facing * curve - 2, enemy.y + y, 4, 6, color)
        fill(x - 44, enemy.y + 106, 88, 21, (17, 34, 51))
        fill(x - 42, enemy.y + 108, 84 * enemy.barrier / enemy.MAX_BARRIER, 3, color)
        self.spark_font.draw(x - 37, enemy.y + 117,
                             f'방벽 {enemy.barrier}/{enemy.MAX_BARRIER}', color)
