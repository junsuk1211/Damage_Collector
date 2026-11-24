"""허수아비와 숫자 회수·투척을 시험하는 훈련장."""

from dataclasses import dataclass, field
from math import ceil, cos, prod, sin, tau
from pathlib import Path
from random import choice, randint

import pico2d as p

try:
    from .selectscreen import fill, korean_font
    from .terrain import melee_path_clear
except ImportError:
    from selectscreen import fill, korean_font
    from terrain import melee_path_clear


@dataclass
class Dummy:
    MAX_HP = 10
    DROPS_NUMBERS = True

    x: float
    y: float
    hp: int = MAX_HP
    flash: float = 0.0


@dataclass
class DroppedNumber:
    FLIGHT_TIME = 0.58
    GROUND_TIME = 4.0

    x: float
    y: float
    value: int
    landing_x: float
    grounded: bool = False
    ground_time: float = GROUND_TIME
    time_left: float = field(init=False)

    def __post_init__(self):
        self.time_left = self.ground_time if self.grounded else self.FLIGHT_TIME + self.ground_time

    @property
    def flight_progress(self):
        if self.grounded:
            return 1.0
        return min(1.0, (self.FLIGHT_TIME + self.ground_time - self.time_left) / self.FLIGHT_TIME)

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
    straight: bool = False

    def point(self, progress):
        distance = abs(self.landing_x - self.x)
        lift = 0 if self.straight else 55 + distance * 0.20
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


@dataclass
class EmberPatch:
    x: float
    y: float
    hit_ids: set = field(default_factory=set)
    time_left: float = 1.0


class TrainingCenter:
    ATTACK_REACH = 92
    solid_obstacles = ()
    PICKUP_REACH = 84
    CAPACITY = 3
    HOLD_TIME = 12.0
    THROW_COOLDOWN = 2.5
    QUICK_THROW_COOLDOWN = 1.5
    MIN_THROW_RANGE = 95
    MAX_THROW_RANGE = 460
    FULL_CHARGE_TIME = 0.95
    BLAST_RADIUS = 103
    BURST_DURATION = 0.72

    def __init__(self, width):
        self.width = width
        self.audio = None
        self.viewport_width = width
        self.camera_x = 0.0
        self.font = korean_font(22)
        self.spark_font = korean_font(16)
        self.dummy_image = p.load_image(str(Path(__file__).resolve().parents[1]
                                           / 'assets/characters/number-motion.png'))
        self.reset()

    def reset(self):
        self.upgrades = set()
        self.embers = []
        self.dummies = []
        self.drops = []
        self.stored = []
        self.projectiles = []
        self.bursts = []
        self.pickup = None
        self.cooldown = 0.0
        self.aim_time = None
        self.pending_arc = None

    @property
    def capacity(self):
        return 2 if 'multiply' in self.upgrades else self.CAPACITY

    def held_label(self):
        separator = ' × ' if 'multiply' in self.upgrades else ' + '
        return separator.join(str(value) for value, _ in self.stored) or '없음'

    def cancel_aim(self):
        self.aim_time = None

    def aim_arc(self, player):
        charge = min(1.0, self.aim_time / self.FULL_CHARGE_TIME)
        distance = self.MIN_THROW_RANGE + charge * (self.MAX_THROW_RANGE - self.MIN_THROW_RANGE)
        landing_x = min(self.width - 12, max(12, player.x + player.facing * distance))
        y = player.ground_y + player.jump_lift + 54
        straight = 'straight' in self.upgrades
        return ThrowArc(player.x, y, landing_x, y if straight else player.ground_y + 8, straight)

    def handle_event(self, event, player):
        if event.type == p.SDL_KEYUP and event.key == p.SDLK_v:
            if self.aim_time is not None and self.stored and player.start_ground_action(p.SDLK_v):
                self.pending_arc = self.aim_arc(player)
            self.cancel_aim()
            return
        if event.type != p.SDL_KEYDOWN:
            return
        if event.key == p.SDLK_i:
            self.dummies.append(Dummy(player.x, player.ground_y))
        elif event.key == p.SDLK_v:
            if (self.aim_time is None and self.stored and self.cooldown <= 0
                    and player.attack_time is None
                    and player.ground_action is None):
                self.aim_time = 0.0

    def can_start_action(self, event, player):
        if event.type != p.SDL_KEYDOWN:
            return True
        if event.key == p.SDLK_v:
            return False
        if self.aim_time is not None:
            return event.key in (p.SDLK_LEFT, p.SDLK_RIGHT, p.SDLK_UP)
        if event.key == p.SDLK_c:
            return len(self.stored) < self.capacity and self.nearest_drop(player) is not None
        return True

    def nearest_drop(self, player):
        reach = self.PICKUP_REACH * (1.5 if 'reach' in self.upgrades else 1)
        nearby = (drop for drop in self.drops if abs(drop.display_x - player.x) <= reach
                  and abs(drop.display_y - (player.ground_y + 32)) <= 75)
        return min(nearby, key=lambda drop: abs(drop.display_x - player.x), default=None)

    def damage(self, dummy, amount):
        dummy.hp = max(0, dummy.hp - amount)
        dummy.flash = 0.16

    def dagger_hit(self, dummy, amount, player):
        self.damage(dummy, amount)

    def drop_number(self, x, y, value, landing_x, *, grounded=False):
        ground_time = DroppedNumber.GROUND_TIME + (3 if 'linger' in self.upgrades else 0)
        self.drops.append(DroppedNumber(x, y, value, landing_x, grounded, ground_time))

    def lose_stored_numbers(self, player):
        if 'recover' in self.upgrades and self.stored:
            value = max(value for value, _ in self.stored)
            self.drop_number(player.x, player.ground_y + 16, value, player.x, grounded=True)
        self.stored.clear()
        self.cancel_aim()

    def throw_damage(self, values):
        if 'multiply' in self.upgrades:
            return prod(values)
        if 'sequence' in self.upgrades and values == [1, 2, 3]:
            return 9
        return sum(values)

    def update(self, dt, player, previous_attack_time, previous_action_time):
        for patch in self.embers:
            patch.time_left -= dt
            if patch.time_left > 0:
                for dummy in self.dummies:
                    if (dummy.hp > 0 and id(dummy) not in patch.hit_ids
                            and abs(dummy.x - patch.x) <= 48 and abs(dummy.y - patch.y) <= 36):
                        self.damage(dummy, 1)
                        patch.hit_ids.add(id(dummy))
        self.embers = [patch for patch in self.embers if patch.time_left > 0]
        for burst in self.bursts:
            burst.age += dt
        self.bursts = [burst for burst in self.bursts if burst.age < self.BURST_DURATION]
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
            feet = player.ground_y + player.jump_lift
            obstacles = self.solid_obstacles
            targets = (dummy for dummy in self.dummies if dummy.hp > 0
                       and -18 <= (dummy.x - player.x) * player.facing <= self.ATTACK_REACH
                       and melee_path_clear(player.x, feet, dummy.x, dummy.y, obstacles))
            dummy = min(targets, key=lambda target: abs(target.x - player.x), default=None)
            if dummy is not None:
                damage = 3 if 'blade' in self.upgrades else randint(1, 3)
                self.dagger_hit(dummy, damage, player)
                if self.audio is not None:
                    self.audio.play_effect('hit')
                if dummy.DROPS_NUMBERS:
                    landings = [dummy.x + offset for offset in (-randint(28, 62), randint(28, 62))
                                if 12 <= dummy.x + offset <= self.width - 12]
                    landing_x = choice(landings) if landings else dummy.x
                    self.drop_number(dummy.x, dummy.y + 16, damage, landing_x)

        if player.ground_action is not None and previous_action_time < 0.19 <= player.action_time:
            row, _ = player.ground_action
            if row == 1 and len(self.stored) < self.capacity:
                drop = self.nearest_drop(player)
                if drop is not None:
                    self.drops.remove(drop)
                    self.stored.append((drop.value, self.HOLD_TIME))
                    self.pickup = drop
                    if self.audio is not None:
                        self.audio.play_effect('pickup')
            elif row == 2 and self.pending_arc is not None:
                if self.stored:
                    values = [value for value, _ in self.stored]
                    total = self.throw_damage(values)
                    self.pending_arc.y = player.ground_y + player.jump_lift + 54
                    if self.pending_arc.straight:
                        self.pending_arc.ground_y = self.pending_arc.y
                    self.projectiles.append(Projectile(self.pending_arc, total))
                    self.stored.clear()
                    self.cooldown = (self.QUICK_THROW_COOLDOWN
                                     if 'quick_throw' in self.upgrades and len(values) == 2
                                     else self.THROW_COOLDOWN)
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
                    self.on_direct_hit(dummy, x, y, shot.value)
                    return False
        shot.progress = end
        if end == 1.0:
            self.explode(*shot.arc.point(end), shot.value)
            return False
        return True

    def on_direct_hit(self, dummy, x, y, value):
        self.explode(x, y, value)

    def explode(self, x, y, value, *, hit_environment=False):
        self.bursts.append(Burst(x, y, value))
        hits = set()
        for dummy in self.dummies:
            distance_squared = (dummy.x - x) ** 2 + (dummy.y + 54 - y) ** 2
            if dummy.hp > 0 and distance_squared <= self.BLAST_RADIUS ** 2:
                self.damage(dummy, value)
                hits.add(id(dummy))
        if self.audio is not None:
            self.audio.play_effect('burst' if hits or hit_environment else 'burst_miss')
        ground = self.floor_at(x, y)
        if 'embers' in self.upgrades:
            self.embers.append(EmberPatch(x, ground, hits))
        if 'refund' in self.upgrades and not (hits or hit_environment):
            self.drop_number(x, ground + 16, 1, x, grounded=True)

    def floor_at(self, x, y):
        return 170

    def draw_dummy(self):
        for dummy in self.dummies:
            x, y = dummy.x, dummy.y
            cell_width, cell_height = self.dummy_image.w // 4, self.dummy_image.h // 4
            self.dummy_image.clip_draw(0, cell_height, cell_width, cell_height,
                                       x, y + 54, 116, 116)
            self.draw_target_health(dummy, y + 109)

    def draw_target_health(self, target, y):
        width, height = 88, 24
        center = target.x - self.camera_x
        if not 0 <= center <= self.viewport_width:
            return
        left = max(2, min(self.viewport_width - width - 2, center - width / 2))
        fill(left, y, width, height, (233, 218, 191))
        fill(left + 2, y + 2, width - 4, height - 4, (12, 12, 16))
        if target.hp > 0:
            fill(left + 2, y + 2, (width - 4) * target.hp / target.MAX_HP,
                 height - 4, (166, 32, 49))
        label = f'{target.hp}/{target.MAX_HP}'
        self.spark_font.draw(left + width / 2 - 4.5 * len(label), y + height / 2,
                             label, (255, 255, 255))

    def draw_number_effects(self, player):
        for patch in self.embers:
            self.draw_blue_embers(patch)
        for drop in self.drops:
            self.font.draw(drop.display_x - self.camera_x - 6, drop.display_y, str(drop.value), (120, 238, 255))
        if self.pickup is not None:
            drop = self.pickup
            progress = min(1.0, (player.action_time - 0.19) / 0.15)
            x = drop.display_x + (player.x + 25 * player.facing - drop.display_x) * progress
            x -= self.camera_x
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
            x -= self.camera_x
            self.font.draw(x - 6, y - 1, str(shot.value), (15, 55, 75))
            self.font.draw(x - 7, y, str(shot.value), (196, 250, 255))
        if self.aim_time is not None:
            arc = self.aim_arc(player)
            for dot in range(1, 24):
                x, y = arc.point(dot / 24)
                fill(x - self.camera_x - 2, y - 2, 4, 4, (145, 242, 255))
            fill(arc.landing_x - self.camera_x - 13, arc.ground_y - 2, 26, 4, (255, 217, 125))

    def draw_blue_embers(self, patch):
        x = patch.x - self.camera_x
        y = patch.y
        age = 1 - patch.time_left
        spread = 1 - (1 - min(1, age / 0.24)) ** 3
        fade = min(1, patch.time_left / 0.32)
        fill(x - 48 * spread, y, 96 * spread, 3, (24, 70, 144))
        for index in range(-4, 5):
            root = x + index * 11 * spread
            pulse = sin(index * 2.1 + age * 24) ** 2
            height = int((11 + 19 * pulse) * fade * (1 - abs(index) * 0.10))
            for row in range(0, height, 3):
                progress = row / height
                center = root + 5 * sin(index + age * 17 + progress * 4) * progress
                width = max(2, int(11 * (1 - progress)))
                fill(center - width / 2, y + row, width, 3, (43, 100, 236))
                if progress < 0.78:
                    fill(center - width / 4, y + row, max(1, width / 2), 3, (94, 210, 255))
                if progress < 0.32:
                    fill(center, y + row, 2, 3, (221, 252, 255))
        for index in range(12):
            life = (age * 1.9 + index * 0.17) % 1
            dx = (index - 5.5) * (5 + 3 * life) * spread
            lift = life * (24 + index % 4 * 7) * fade
            fill(x + dx, y + lift, 2, 3, (83, int(215 - 105 * life), 255))

    def draw_banner(self, width, height, player):
        self.draw_number_effects(player)
        fill(0, height - 82, width, 82, (19, 25, 42))
        self.font.draw(24, height - 22, '훈련장  |  I키를 누를 시 허수아비 더미를 생성합니다  |  Esc 시작 화면으로', (255, 230, 177))
        held = self.held_label()
        cooldown = f'{self.cooldown:.1f}초' if self.cooldown else '준비'
        self.font.draw(24, height - 56, f'X 공격   C 회수   V 누르기 조준 / 놓기 투척     보관 {held}     투척 {cooldown}', (120, 238, 255))

    def draw_burst(self, burst):
        screen_x = burst.x - self.camera_x
        progress = burst.age / self.BURST_DURATION
        expansion = 1 - (1 - progress) ** 4
        radius = 8 + (self.BLAST_RADIUS - 8) * expansion
        fade = (1 - progress) ** 1.35
        cyan = (int(85 * fade), int(229 * fade), int(255 * fade))

        # 충격파는 초반에 빠르게 퍼지고 숫자 불꽃보다 먼저 사라진다.
        if progress < 0.52:
            ring_fade = (1 - progress / 0.52) ** 0.8
            ring_color = (int(155 * ring_fade), int(244 * ring_fade), int(255 * ring_fade))
            for index in range(64):
                angle = tau * index / 64
                x = screen_x + cos(angle) * radius
                y = burst.y + sin(angle) * radius
                size = 4 if index % 4 else 6
                fill(x - size / 2, y - size / 2, size, size, ring_color)

        if progress < 0.22:
            flash = 1 - progress / 0.22
            size = 14 + 24 * flash
            x, y = screen_x, burst.y
            fill(x - size / 2, y - size / 2, size, size, (49, 181, 234))
            fill(x - size, y - 3, size * 2, 6, (184, 253, 255))
            fill(x - 3, y - size * 0.72, 6, size * 1.44, (184, 253, 255))
            fill(x - size / 4, y - size / 4, size / 2, size / 2, (249, 255, 255))

        for index in range(16):
            angle = tau * index / 16 + 0.12
            spread = radius * (0.66 + 0.17 * (index % 3))
            dx, dy = cos(angle), sin(angle)
            x = screen_x + dx * spread
            y = burst.y + dy * spread - 32 * progress ** 2
            for trail in (8, 14, 20):
                size = max(1, 5 - trail // 5)
                fill(x - dx * trail - size / 2, y - dy * trail - size / 2, size, size, cyan)
            if index % 2:
                gold = (int(255 * fade), int(211 * fade), int(131 * fade))
                fill(x - 2, y - 2, 5, 5, gold)
            else:
                color = (int(203 * fade), int(249 * fade), int(255 * fade))
                self.font.draw(x - 7, y, str(burst.value), color)
