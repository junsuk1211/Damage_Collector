"""허수아비와 숫자 회수·투척을 시험하는 훈련장."""

from dataclasses import dataclass
from math import ceil, cos, sin, tau
from pathlib import Path
from random import choice, randint

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
    landing_x: float
    time_left: float = 2.0

    @property
    def flight_progress(self):
        return min(1.0, (2.0 - self.time_left) / 0.58)

    @property
    def display_x(self):
        return self.x + (self.landing_x - self.x) * self.flight_progress

    @property
    def display_y(self):
        progress = self.flight_progress
        return self.y + 44 * (1 - progress) + 260 * progress * (1 - progress)


@dataclass
class ThrowArc:
    x: float
    y: float
    landing_x: float
    ground_y: float

    def point(self, progress):
        distance = abs(self.landing_x - self.x)
        lift = 55 + distance * 0.20
        x = self.x + (self.landing_x - self.x) * progress
        y = self.y + (self.ground_y - self.y) * progress + 4 * lift * progress * (1 - progress)
        return x, y


@dataclass
class Projectile:
    arc: ThrowArc
    value: int
    progress: float = 0.0


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
    MIN_THROW_RANGE = 95
    MAX_THROW_RANGE = 460
    FULL_CHARGE_TIME = 0.95
    BLAST_RADIUS = 103

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
        self.aim_time = None
        self.pending_arc = None

    def cancel_aim(self):
        self.aim_time = None

    def aim_arc(self, player):
        charge = min(1.0, self.aim_time / self.FULL_CHARGE_TIME)
        distance = self.MIN_THROW_RANGE + charge * (self.MAX_THROW_RANGE - self.MIN_THROW_RANGE)
        landing_x = min(self.width - 12, max(12, player.x + player.facing * distance))
        return ThrowArc(player.x, player.ground_y + 54, landing_x, player.ground_y + 8)

    def handle_event(self, event, player):
        if event.type == p.SDL_KEYDOWN and event.key == p.SDLK_i:
            self.dummies.append(Dummy(player.x, player.ground_y))
        if event.type == p.SDL_KEYDOWN and event.key == p.SDLK_v:
            if (self.aim_time is None and self.stored and self.cooldown <= 0
                    and player.attack_time is None and player.jump_time is None
                    and player.ground_action is None):
                self.aim_time = 0.0
        elif event.type == p.SDL_KEYUP and event.key == p.SDLK_v and self.aim_time is not None:
            if self.stored and player.start_ground_action(p.SDLK_v):
                self.pending_arc = self.aim_arc(player)
            self.cancel_aim()

    def can_start_action(self, event, player):
        if event.type != p.SDL_KEYDOWN:
            return True
        if event.key == p.SDLK_c:
            return len(self.stored) < self.CAPACITY and self.nearest_drop(player) is not None
        if event.key == p.SDLK_v:
            return False
        if self.aim_time is not None:
            return event.key in (p.SDLK_LEFT, p.SDLK_RIGHT)
        return True

    def nearest_drop(self, player):
        nearby = (drop for drop in self.drops if abs(drop.display_x - player.x) <= self.PICKUP_REACH)
        return min(nearby, key=lambda drop: abs(drop.display_x - player.x), default=None)

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
        if not self.stored:
            self.cancel_aim()
        if self.aim_time is not None:
            self.aim_time = min(self.FULL_CHARGE_TIME, self.aim_time + dt)
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
                landings = [dummy.x + offset for offset in (-randint(28, 62), randint(28, 62))
                            if 12 <= dummy.x + offset <= self.width - 12]
                landing_x = choice(landings) if landings else dummy.x
                self.drops.append(DroppedNumber(dummy.x, dummy.y + 16, damage, landing_x))

        if player.ground_action is not None and previous_action_time < 0.19 <= player.action_time:
            row, _ = player.ground_action
            if row == 1 and len(self.stored) < self.CAPACITY:
                drop = self.nearest_drop(player)
                if drop is not None:
                    self.drops.remove(drop)
                    self.stored.append((drop.value, self.HOLD_TIME))
                    self.pickup = drop
            elif row == 2 and self.pending_arc is not None:
                if self.stored:
                    total = sum(value for value, _ in self.stored)
                    self.projectiles.append(Projectile(self.pending_arc, total))
                    self.stored.clear()
                    self.cooldown = self.THROW_COOLDOWN
                self.pending_arc = None

        self.projectiles = [shot for shot in self.projectiles if self.advance_shot(shot, dt)]
        self.dummies = [dummy for dummy in self.dummies if dummy.hp > 0]

    def advance_shot(self, shot, dt):
        distance = abs(shot.arc.landing_x - shot.arc.x)
        duration = 0.36 + distance / 1100
        end = min(1.0, shot.progress + dt / duration)
        # 프레임 사이의 궤적도 검사해 얇은 표적을 건너뛰지 않게 한다.
        steps = max(1, ceil((end - shot.progress) * 100))
        for step in range(steps + 1):
            progress = shot.progress + (end - shot.progress) * step / steps
            x, y = shot.arc.point(progress)
            for dummy in self.dummies:
                if dummy.hp > 0 and abs(x - dummy.x) <= 22 and dummy.y + 8 <= y <= dummy.y + 88:
                    self.explode(x, y, shot.value)
                    return False
        shot.progress = end
        if end == 1.0:
            self.explode(*shot.arc.point(end), shot.value)
            return False
        return True

    def explode(self, x, y, value):
        self.bursts.append(Burst(x, y, value))
        for dummy in self.dummies:
            distance_squared = (dummy.x - x) ** 2 + (dummy.y + 54 - y) ** 2
            if dummy.hp > 0 and distance_squared <= self.BLAST_RADIUS ** 2:
                self.damage(dummy, value)

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
            self.font.draw(drop.display_x - 6, drop.display_y, str(drop.value), (120, 238, 255))
        if self.pickup is not None:
            drop = self.pickup
            progress = min(1.0, (player.action_time - 0.19) / 0.15)
            x = drop.display_x + (player.x + 25 * player.facing - drop.display_x) * progress
            y = drop.display_y + (player.ground_y + 61 - drop.display_y) * progress
            y += 4 * (drop.value - 1) * 7 * progress * (1 - progress)
            color = ((120, 238, 255), (160, 255, 181), (255, 219, 116))[drop.value - 1]
            for index in range(1, drop.value):
                fill(x - player.facing * index * 8, y - index * 5, 3, 3, color)
            self.font.draw(x - 6, y, str(drop.value), color)
        for burst in self.bursts:
            self.draw_burst(burst)
        for shot in self.projectiles:
            x, y = shot.arc.point(shot.progress)
            self.font.draw(x - 6, y - 1, str(shot.value), (15, 55, 75))
            self.font.draw(x - 7, y, str(shot.value), (196, 250, 255))
        if self.aim_time is not None:
            arc = self.aim_arc(player)
            for dot in range(1, 24):
                x, y = arc.point(dot / 24)
                fill(x - 2, y - 2, 4, 4, (145, 242, 255))
            fill(arc.landing_x - 13, arc.ground_y - 2, 26, 4, (255, 217, 125))
        fill(0, height - 82, width, 82, (19, 25, 42))
        self.font.draw(24, height - 22, '훈련장  |  I키를 누를 시 허수아비 더미를 생성합니다  |  Esc 시작 화면으로', (255, 230, 177))
        held = ' + '.join(str(value) for value, _ in self.stored) or '없음'
        cooldown = f'{self.cooldown:.1f}초' if self.cooldown else '준비'
        self.font.draw(24, height - 56, f'X 공격   C 회수   V 누르기 조준 / 놓기 투척     보관 {held}     투척 {cooldown}', (120, 238, 255))

    def draw_burst(self, burst):
        progress = burst.age / 0.60
        radius = 8 + (self.BLAST_RADIUS - 8) * (1 - (1 - progress) ** 2)
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
