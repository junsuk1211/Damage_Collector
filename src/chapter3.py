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
    TITLE = '챕터 3  |  성 내부 초소'
    NEXT_STAGE = None
    ARROW_PLATFORM = None
    GUARD_POSITIONS = (820, 1520)
    HEAVY_POSITIONS = (1290, 2180)
    STONE_PLATFORMS = ((530, 630, 181), (1740, 1840, 196))
    SCAFFOLDS = ((1050, 1250, 211),)
    FIRE_VENTS = ((960, 1.1), (1910, 2.2))

    def __init__(self, width):
        super().__init__(width)
        path = Path(__file__).resolve().parents[1] / 'assets/characters/chapter3-heavy.png'
        self.heavy_image = p.load_image(str(path))

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

    def draw_dummy(self):
        super().draw_dummy()
        cell_w, cell_h = self.heavy_image.w // 4, self.heavy_image.h // 2
        for enemy in self.dummies:
            if not isinstance(enemy, Verysheidman):
                continue
            x = enemy.x - self.camera_x
            if not -85 <= x <= self.viewport_width + 85:
                continue
            column, row = enemy.sprite_cell()
            self.heavy_image.clip_composite_draw(
                column * cell_w, (1 - row) * cell_h, cell_w, cell_h,
                0, 'h' if enemy.facing > 0 else '', x, enemy.y + 58, 148, 148,
            )
            self.draw_target_health(enemy, enemy.y + 131)
            if enemy.barrier:
                self.draw_barrier(enemy, x)
            elif enemy.stagger:
                self.spark_font.draw(x - 32, enemy.y + 112, '방벽 파괴', (133, 242, 255))
            if enemy.attack_age is not None and enemy.attack_age < enemy.ATTACK_HIT_TIME:
                progress = enemy.attack_age / enemy.ATTACK_HIT_TIME
                left = x if enemy.facing > 0 else x - enemy.ATTACK_REACH
                fill(left, enemy.y + 1, enemy.ATTACK_REACH, 4, (248, 81, 64))
                self.spark_font.draw(x - 5, enemy.y + 106, '!', (255, 167 - int(progress * 100), 83))

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
