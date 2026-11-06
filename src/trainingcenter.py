"""허수아비와 숫자 회수·투척을 시험하는 훈련장."""

from dataclasses import dataclass
from math import cos, sin, tau
from pathlib import Path
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

    @property
    def display_y(self):
        progress = min(1.0, (2.0 - self.time_left) / 0.58)
        return self.y + 44 * (1 - progress) + 260 * progress * (1 - progress)


@dataclass
class Projectile:
    x: float
    y: float
    direction: int
    value: int


@dataclass
class Burst:
    x: float
    y: float
    value: int
    age: float = 0.0


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
        self.spark_font = korean_font(16)
        self.dummy_image = p.load_image(str(Path(__file__).resolve().parents[1]
                                           / 'assets/characters/number-motion.png'))
        self.reset()

    def reset(self):
        self.dummies = []
        self.drops = []
        self.stored = []
        self.projectiles = []
        self.bursts = []
        self.pickup = None
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
        for burst in self.bursts:
            burst.age += dt
        self.bursts = [burst for burst in self.bursts if burst.age < 0.60]
        if player.ground_action is None or player.ground_action[0] != 1:
            self.pickup = None
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
                self.drops.append(DroppedNumber(dummy.x, dummy.y + 16, damage))

        if player.ground_action is not None and previous_action_time < 0.19 <= player.action_time:
            row, _ = player.ground_action
            if row == 1 and len(self.stored) < self.CAPACITY:
                drop = self.nearest_drop(player)
                if drop is not None:
                    self.drops.remove(drop)
                    self.stored.append((drop.value, self.HOLD_TIME))
                    self.pickup = drop
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
                self.bursts.append(Burst(target.x, shot.y, shot.value))
            elif 0 <= next_x <= self.width:
                shot.x = next_x
                active.append(shot)
        self.projectiles = active
        self.dummies = [dummy for dummy in self.dummies if dummy.hp > 0]

    def draw_dummy(self):
        for dummy in self.dummies:
            x, y = dummy.x, dummy.y
            cell_width, cell_height = self.dummy_image.w // 4, self.dummy_image.h // 4
            self.dummy_image.clip_draw(0, cell_height, cell_width, cell_height,
                                       x, y + 54, 116, 116)
            fill(x - 28, y + 109, 56, 6, (77, 34, 41))
            fill(x - 28, y + 109, 56 * dummy.hp / 10, 6,
                 (255, 233, 165) if dummy.flash else (240, 105, 80))

    def draw_banner(self, width, height, player):
        for drop in self.drops:
            self.font.draw(drop.x - 6, drop.display_y, str(drop.value), (120, 238, 255))
        if self.pickup is not None:
            drop = self.pickup
            progress = min(1.0, (player.action_time - 0.19) / 0.15)
            x = drop.x + (player.x + 25 * player.facing - drop.x) * progress
            y = drop.display_y + (player.ground_y + 61 - drop.display_y) * progress
            y += 4 * (drop.value - 1) * 7 * progress * (1 - progress)
            color = ((120, 238, 255), (160, 255, 181), (255, 219, 116))[drop.value - 1]
            for index in range(1, drop.value):
                fill(x - player.facing * index * 8, y - index * 5, 3, 3, color)
            self.font.draw(x - 6, y, str(drop.value), color)
        for burst in self.bursts:
            self.draw_burst(burst)
        for shot in self.projectiles:
            fill(shot.x - 15, shot.y - 13, 30, 26, (25, 89, 117))
            self.font.draw(shot.x - 7, shot.y, str(shot.value), (196, 250, 255))
        fill(0, height - 82, width, 82, (19, 25, 42))
        self.font.draw(24, height - 22, '훈련장  |  I키를 누를 시 허수아비 더미를 생성합니다', (255, 230, 177))
        held = ' + '.join(str(value) for value, _ in self.stored) or '없음'
        cooldown = f'{self.cooldown:.1f}초' if self.cooldown else '준비'
        self.font.draw(24, height - 56, f'X 공격   C 회수   V 투척     보관 {held}     투척 {cooldown}', (120, 238, 255))

    def draw_burst(self, burst):
        progress = burst.age / 0.60
        radius = 8 + 95 * (1 - (1 - progress) ** 2)
        fade = 1 - progress
        if progress < 0.30:
            size = 20 * (1 - progress / 0.30)
            fill(burst.x - size / 2, burst.y - size / 2, size, size, (228, 252, 255))
        for index in range(10):
            angle = tau * index / 10 + 0.12
            spread = radius * (1.0 if index % 2 == 0 else 0.76)
            dx, dy = cos(angle), sin(angle)
            x = burst.x + dx * spread
            y = burst.y + dy * spread - 27 * progress ** 2
            color = (int(125 * fade), int(235 * fade), int(255 * fade))
            for trail in (8, 15):
                fill(x - dx * trail, y - dy * trail, 3, 3, color)
            self.spark_font.draw(x - 5, y, str(burst.value), color)
