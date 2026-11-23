"""중갑 석궁병이 배치된 챕터 4 초소."""

from pathlib import Path

import pico2d as p

try:
    from .chapter1 import ChapterOne
    from .trainingcenter import Dummy
except ImportError:
    from chapter1 import ChapterOne
    from trainingcenter import Dummy


class HeavyCrossbowman(Dummy):
    MAX_HP = 18


class ChapterFour(ChapterOne):
    TITLE = '챕터 4  |  성 내부 초소'
    SCREENS_WIDE = 1
    NEXT_STAGE = None
    GUARD_POSITIONS = ()
    STONE_PLATFORMS = ()
    ARROW_PLATFORM = None
    SCAFFOLDS = ()
    FIRE_VENTS = ()

    def __init__(self, width):
        super().__init__(width)
        path = Path(__file__).resolve().parents[1] / 'assets/characters/chapter4-heavy-crossbow.png'
        self.crossbow_image = p.load_image(str(path))

    def reset(self):
        super().reset()
        self.dummies.append(HeavyCrossbowman(900, self.FLOOR_Y, hp=HeavyCrossbowman.MAX_HP))

    def draw_dummy(self):
        image = self.crossbow_image
        for enemy in self.dummies:
            x = enemy.x - self.camera_x
            image.draw(x - 20, enemy.y + 68, round(146 * image.w / image.h), 146)
            self.draw_target_health(enemy, enemy.y + 150)
