"""허수아비와 숫자 회수·투척을 시험하는 훈련장."""

from dataclasses import dataclass
from random import randint

import pico2d as p

try:
    from .selectscreen import fill, korean_font
except ImportError:
    from selectscreen import fill, korean_font


@dataclass
class Dummy:
    x: float
    y: float
    hp: int = 10
    flash: float = 0.0


@dataclass
class DroppedNumber:
    x: float
    y: float
    value: int
    time_left: float = 2.0


@dataclass
class Projectile:
    x: float
    y: float
    direction: int
    value: int


class TrainingCenter:
    ATTACK_REACH = 92
    PICKUP_REACH = 84
    CAPACITY = 3
    HOLD_TIME = 6.0
    THROW_COOLDOWN = 2.5
    PROJECTILE_SPEED = 680

    def __init__(self, width):
        self.width = width
        self.font = korean_font(22)
        self.reset()

    def reset(self):
        self.dummies = []
        self.drops = []
        self.stored = []
        self.projectiles = []
        self.cooldown = 0.0

    def handle_event(self, event, player):
        if event.type == p.SDL_KEYDOWN and event.key == p.SDLK_i:
            self.dummies.append(Dummy(player.x, player.ground_y))

    def can_start_action(self, event, player):
        if event.type != p.SDL_KEYDOWN:
            return True
        if event.key == p.SDLK_c:
            return len(self.stored) < self.CAPACITY and self.nearest_drop(player) is not None
        if event.key == p.SDLK_v:
            return bool(self.stored) and self.cooldown <= 0
        return True

    def nearest_drop(self, player):
        nearby = (drop for drop in self.drops if abs(drop.x - player.x) <= self.PICKUP_REACH)
        return min(nearby, key=lambda drop: abs(drop.x - player.x), default=None)

    def damage(self, dummy, amount):
        dummy.hp = max(0, dummy.hp - amount)
        dummy.flash = 0.16

    def update(self, dt, player, previous_attack_time, previous_action_time):
        self.cooldown = max(0.0, self.cooldown - dt)
        self.stored = [(value, ttl - dt) for value, ttl in self.stored if ttl > dt]
        for drop in self.drops:
            drop.time_left -= dt
        self.drops = [drop for drop in self.drops if drop.time_left > 0]
        for dummy in self.dummies:
            dummy.flash = max(0.0, dummy.flash - dt)

        if (previous_attack_time is not None and player.attack_time is not None
                and previous_attack_time < 0.10 <= player.attack_time):
            targets = (dummy for dummy in self.dummies if dummy.hp > 0
                       and -18 <= (dummy.x - player.x) * player.facing <= self.ATTACK_REACH)
            dummy = min(targets, key=lambda target: abs(target.x - player.x), default=None)
            if dummy is not None:
                damage = randint(1, 3)
                self.damage(dummy, damage)
                self.drops.append(DroppedNumber(dummy.x, dummy.y + 22, damage))

        if player.ground_action is not None and previous_action_time < 0.19 <= player.action_time:
            row, _ = player.ground_action
            if row == 1 and len(self.stored) < self.CAPACITY:
                drop = self.nearest_drop(player)
                if drop is not None:
                    self.drops.remove(drop)
                    self.stored.append((drop.value, self.HOLD_TIME))
            elif row == 2 and self.stored and self.cooldown <= 0:
                total = sum(value for value, _ in self.stored)
                self.projectiles.append(Projectile(player.x, player.ground_y + 54, player.facing, total))
                self.stored.clear()
                self.cooldown = self.THROW_COOLDOWN

        active = []
        for shot in self.projectiles:
            next_x = shot.x + shot.direction * self.PROJECTILE_SPEED * dt
            left, right = sorted((shot.x, next_x))
            targets = (dummy for dummy in self.dummies if dummy.hp > 0
                       and left <= dummy.x + 19 and right >= dummy.x - 19
                       and dummy.y + 29 <= shot.y <= dummy.y + 88)
            target = min(targets, key=lambda dummy: dummy.x * shot.direction, default=None)
            if target is not None:
                self.damage(target, shot.value)
            elif 0 <= next_x <= self.width:
                shot.x = next_x
                active.append(shot)
        self.projectiles = active
        self.dummies = [dummy for dummy in self.dummies if dummy.hp > 0]

    def draw_dummy(self):
        for dummy in self.dummies:
            x, y = dummy.x, dummy.y
            straw = (255, 225, 164) if dummy.flash else (213, 167, 81)
            fill(x - 4, y, 8, 74, (109, 67, 43))
            fill(x - 35, y + 48, 70, 8, (142, 93, 53))
            fill(x - 19, y + 29, 38, 37, straw)
            fill(x - 12, y + 65, 24, 23, straw)
            fill(x - 18, y + 81, 36, 5, (83, 54, 44))
            fill(x - 19, y + 41, 38, 4, (114, 71, 46))
            fill(x - 28, y + 99, 56, 6, (77, 34, 41))
            fill(x - 28, y + 99, 56 * dummy.hp / 10, 6, (240, 105, 80))

    def draw_banner(self, width, height):
        for drop in self.drops:
            self.font.draw(drop.x - 6, drop.y, str(drop.value), (120, 238, 255))
        for shot in self.projectiles:
            fill(shot.x - 15, shot.y - 13, 30, 26, (25, 89, 117))
            self.font.draw(shot.x - 7, shot.y, str(shot.value), (196, 250, 255))
        fill(0, height - 82, width, 82, (19, 25, 42))
        self.font.draw(24, height - 22, '훈련장  |  I키를 누를 시 허수아비 더미를 생성합니다', (255, 230, 177))
        held = ' + '.join(str(value) for value, _ in self.stored) or '없음'
        cooldown = f'{self.cooldown:.1f}초' if self.cooldown else '준비'
        self.font.draw(24, height - 56, f'X 공격   C 회수   V 투척     보관 {held}     투척 {cooldown}', (120, 238, 255))
