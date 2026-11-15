"""챕터 2의 전투와 지형 배치."""

from pathlib import Path

import pico2d as p

try:
    from .chapter1 import ChapterOne
    from .arrowman import Arrowman, Bolt
    from .selectscreen import fill
    from .terrain import stop_at_boxes
except ImportError:
    from chapter1 import ChapterOne
    from arrowman import Arrowman, Bolt
    from selectscreen import fill
    from terrain import stop_at_boxes


class ChapterTwo(ChapterOne):
    ARROW_PLATFORM = None
    USE_GATE_MASONRY = False
    TITLE = '챕터 2  |  성 안쪽 통로'
    NEXT_STAGE = 'chapter3'
    GUARD_POSITIONS = (850, 975)
    STONE_PLATFORMS = ((580, 705, 194), (1810, 1930, 193))
    SCAFFOLDS = ((765, 980, 224), (1560, 1750, 220))
    BOXES = ((465, 524, 182), (1420, 1505, 204))
    FIRE_VENTS = ((1065, 1.0), (1980, 2.0), (2280, 2.8))

    def __init__(self, width):
        super().__init__(width)
        path = Path(__file__).resolve().parents[1] / 'assets/characters/chapter2-crossbow.png'
        self.crossbow = p.load_image(str(path))

    def reset(self):
        super().reset()
        self.archer_spawned = False
        self.bolts = []

    @property
    def remaining_enemies(self):
        return super().remaining_enemies + int(not self.archer_spawned)

    def update(self, dt, player, previous_attack_time, previous_action_time):
        super().update(dt, player, previous_attack_time, previous_action_time)
        if not self.health:
            return
        if not self.archer_spawned and not self.dummies and player.x >= 1660:
            self.dummies.append(Arrowman(2150, self.FLOOR_Y))
            self.archer_spawned = True
        for enemy in self.dummies:
            if isinstance(enemy, Arrowman) and enemy.advance(dt, player):
                self.bolts.append(Bolt(enemy.x + 22 * enemy.facing, enemy.y + 53, enemy.facing))
        self.bolts = [bolt for bolt in self.bolts if self.advance_bolt(bolt, dt, player)]

    def advance_bolt(self, bolt, dt, player):
        travel = min(bolt.remaining, 530 * dt)
        next_x = bolt.x + bolt.facing * travel
        end_x = stop_at_boxes(bolt.x, next_x, bolt.y, 0, self.solid_obstacles)
        feet = player.ground_y + player.jump_lift
        rolling = player.ground_action is not None and player.ground_action[0] == 3
        if (not rolling and feet + 6 <= bolt.y <= feet + 75
                and min(bolt.x, end_x) - 14 <= player.x <= max(bolt.x, end_x) + 14):
            self.hurt_player(player)
            return False
        bolt.x = end_x
        bolt.remaining -= travel
        return end_x == next_x and bolt.remaining > 0 and 0 <= bolt.x <= self.width

    def draw_dummy(self):
        super().draw_dummy()
        for enemy in self.dummies:
            if isinstance(enemy, Arrowman):
                cell = self.crossbow.w // 3
                self.crossbow.clip_composite_draw(
                    cell * enemy.pose, 0, cell, self.crossbow.h,
                    0, 'h' if enemy.facing > 0 else '',
                    enemy.x - self.camera_x, enemy.y + 55, 120, 110,
                )
                self.draw_target_health(enemy, enemy.y + 108)
        for bolt in self.bolts:
            x = bolt.x - self.camera_x
            fill(min(x, x - 22 * bolt.facing), bolt.y, 22, 2, (209, 159, 103))
            fill(x - 2, bolt.y - 1, 4, 4, (248, 223, 174))
