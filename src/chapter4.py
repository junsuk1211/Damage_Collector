"""중갑 석궁병이 배치된 챕터 4 초소."""

from math import hypot
from pathlib import Path

import pico2d as p

try:
    from .chapter1 import ChapterOne
    from .selectscreen import fill
    from .tower_fire import TowerBolt
    from .trainingcenter import Burst, Dummy
except ImportError:
    from chapter1 import ChapterOne
    from selectscreen import fill
    from tower_fire import TowerBolt
    from trainingcenter import Burst, Dummy


class HeavyCrossbowman(Dummy):
    MAX_HP = 18


class HeavyBolt(TowerBolt):
    SPEED = 460


class ChapterFour(ChapterOne):
    TITLE = '챕터 4  |  성 내부 초소'
    SCREENS_WIDE = 1
    NEXT_STAGE = None
    GUARD_POSITIONS = ()
    STONE_PLATFORMS = ()
    ARROW_PLATFORM = None
    SCAFFOLDS = ()
    FIRE_VENTS = ()
    CHAIN_INTERVAL = 0.24
    ANCHOR_FLIGHT_TIME = 0.48

    def __init__(self, width):
        super().__init__(width)
        path = Path(__file__).resolve().parents[1] / 'assets/characters/chapter4-heavy-crossbow.png'
        self.crossbow_image = p.load_image(str(path))

    def reset(self):
        super().reset()
        self.archer = HeavyCrossbowman(900, self.FLOOR_Y, hp=HeavyCrossbowman.MAX_HP)
        self.dummies.append(self.archer)
        self.facing = -1
        self.phase = 'ready'
        self.time_left = 1.4
        self.warning = None
        self.bolts = []
        self.anchors = []
        self.chain = []
        self.chain_value = 0

    @property
    def barrier_active(self):
        return self.phase != 'exposed'

    def damage(self, enemy, amount):
        if enemy is self.archer and self.barrier_active:
            enemy.flash = 0.16
            return
        super().damage(enemy, amount)

    def draw_archer_barrier(self, enemy, x):
        color = (178, 250, 255) if enemy.flash else (71, 174, 194)
        for dx, dy, direction in ((-48, 10, 1), (48, 10, -1),
                                  (-48, 100, 1), (48, 100, -1)):
            fill(x + min(dx, dx + direction * 12), enemy.y + dy, 12, 2, color)
            fill(x + dx, enemy.y + dy - (10 if dy == 100 else 0), 2, 12, color)
        self.spark_font.draw(x - 26, enemy.y + 109, '방벽 활성', color)

    def explode(self, x, y, value, *, hit_environment=False):
        near = [anchor for anchor in self.anchors
                if hypot(anchor - x, self.FLOOR_Y + 14 - y) <= 80]
        triggered = self.phase == 'armed' and bool(near)
        super().explode(x, y, value, hit_environment=hit_environment or triggered)
        if triggered and self.archer.hp > 0:
            first = min(near, key=lambda anchor: abs(anchor - x))
            self.chain = [first, *(anchor for anchor in self.anchors if anchor != first)]
            self.anchors.clear()
            self.chain_value = min(6, value + 2)
            self.phase = 'chain'
            self.time_left = self.CHAIN_INTERVAL

    def update(self, dt, player, previous_attack_time, previous_action_time):
        super().update(dt, player, previous_attack_time, previous_action_time)
        if not self.health or not self.archer.hp:
            self.warning = None
            self.bolts.clear()
            self.anchors.clear()
            return

        self.time_left -= dt
        if self.time_left <= 0:
            self.advance_attack(player)
        self.bolts = [bolt for bolt in self.bolts if bolt.advance(dt, player, self.hurt_player)]

    def advance_attack(self, player):
        enemy = self.archer
        if self.phase == 'ready':
            self.facing = 1 if player.x >= enemy.x else -1
            muzzle_x = enemy.x + self.facing * 31
            reach = self.width - muzzle_x if self.facing > 0 else muzzle_x
            self.warning = HeavyBolt(muzzle_x, enemy.y + 53, self.facing, 0, reach)
            self.phase, self.time_left = 'aimed_shot', 0.85
            self.play_draw_sound()
        elif self.phase == 'aimed_shot':
            self.bolts.append(self.warning)
            self.warning = None
            self.phase, self.time_left = 'before_skill', 1.1
        elif self.phase == 'before_skill':
            self.facing = 1 if player.x >= enemy.x else -1
            self.anchors = [enemy.x + self.facing * distance for distance in (150, 310)]
            self.phase, self.time_left = 'aimed_anchors', 1.05
            self.play_draw_sound()
        elif self.phase == 'aimed_anchors':
            self.phase, self.time_left = 'anchor_flight', self.ANCHOR_FLIGHT_TIME
        elif self.phase == 'anchor_flight':
            feet = player.ground_y + player.jump_lift
            if feet <= self.FLOOR_Y + 40 and any(abs(player.x - x) <= 35 for x in self.anchors):
                self.hurt_player(player)
            self.phase, self.time_left = 'armed', 8.0
        elif self.phase == 'chain':
            if self.chain:
                x = self.chain.pop(0)
                self.bursts.append(Burst(x, self.FLOOR_Y + 16, self.chain_value))
                self.time_left = self.CHAIN_INTERVAL
            else:
                self.bursts.append(Burst(enemy.x, enemy.y + 56, self.chain_value))
                self.phase, self.time_left = 'exposed', 3.0
                self.damage(enemy, self.chain_value)
            if self.audio is not None:
                self.audio.play_effect('burst')
        else:
            self.anchors.clear()
            self.phase, self.time_left = 'ready', 1.2

    def play_draw_sound(self):
        if self.audio is not None:
            self.audio.play_effect('crossbow_draw')

    def draw_banner(self, width, height, player):
        super().draw_banner(width, height, player)
        if self.archer.hp:
            fill(16, height - 105, 416, 30, (19, 25, 42))
            self.spark_font.draw(26, height - 90, '박힌 화살에 숫자를 던져 방벽을 깨세요.', (152, 242, 255))

    def draw_dummy(self):
        image = self.crossbow_image
        for enemy in self.dummies:
            x = enemy.x - self.camera_x
            image.composite_draw(0, 'h' if self.facing > 0 else '', x + 20 * self.facing,
                                 enemy.y + 68, round(146 * image.w / image.h), 146)
            self.draw_target_health(enemy, enemy.y + 150)
            if self.phase == 'exposed':
                self.spark_font.draw(x - 32, enemy.y + 132, '방벽 파괴', (135, 240, 255))
            else:
                self.draw_archer_barrier(enemy, x)
        if self.warning is not None:
            self.warning.draw_warning(self.camera_x)
        for bolt in self.bolts:
            bolt.draw(self.camera_x)
        for x in self.anchors:
            self.draw_anchor(x)

    def draw_anchor(self, x):
        y = self.FLOOR_Y
        screen_x = x - self.camera_x
        if self.phase in ('aimed_anchors', 'anchor_flight'):
            fill(screen_x - 33, y + 1, 66, 4, (244, 74, 66))
            self.spark_font.draw(screen_x - 4, y + 21, '!', (255, 150, 100))
            if self.phase == 'anchor_flight':
                start_x = self.archer.x + self.facing * 31
                dx = x - start_x
                dy = -50
                length = hypot(dx, dy)
                progress = 1 - self.time_left / self.ANCHOR_FLIGHT_TIME
                HeavyBolt(start_x + dx * progress, y + 50 + dy * progress,
                          dx / length, dy / length, 0).draw(self.camera_x)
        elif self.phase == 'armed':
            fill(screen_x - 22, y + 1, 44, 4, (64, 198, 207))
            HeavyBolt(x, y + 2, 0, -1, 0).draw(self.camera_x)
            self.spark_font.draw(screen_x - 27, y + 37, '숫자 투척', (152, 242, 255))
