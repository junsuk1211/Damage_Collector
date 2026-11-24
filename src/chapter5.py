"""성당 복도와 최종 성기사 전투."""

from dataclasses import dataclass
from pathlib import Path
from random import random
from math import cos, sin, tau

import pico2d as p
from sdl2 import SDL_ScaleModeLinear, SDL_SetTextureScaleMode

try:
    from .chapter1 import ChapterOne
    from .selectscreen import fade_to_black, fill
    from .trainingcenter import Dummy
except ImportError:
    from chapter1 import ChapterOne
    from selectscreen import fade_to_black, fill
    from trainingcenter import Dummy


@dataclass
class Paladin(Dummy):
    MAX_HP = 60
    hp: int = MAX_HP


class ChapterFive(ChapterOne):
    TITLE = '챕터 5  |  성기사의 대성당'
    NEXT_STAGE = None
    SCREENS_WIDE = 1
    GUARD_POSITIONS = BOXES = STONE_PLATFORMS = SCAFFOLDS = FIRE_VENTS = ()
    ARROW_PLATFORM = None
    ARENA_ENTRANCE = 490
    LUNGE_REACH = 390
    LUNGE_SPEED = 680
    SWORD_REACH = 102
    WAVE_SPEED = 380
    VICTORY_TIME = 2.8
    PARRY_CHANCE = .30
    INTRO_TIME = 3.6
    INTRO_BELL_AT = 1.35
    PALADIN_DRAW_SIZE = (224, 192)

    def __init__(self, width):
        super().__init__(width)
        path = Path(__file__).resolve().parents[1] / 'assets/characters/cathedral-paladin.png'
        self.paladin_image = p.load_image(str(path))
        SDL_SetTextureScaleMode(self.paladin_image.texture, SDL_ScaleModeLinear)
        self.wave_image = p.load_image(str(path.with_name("crossbow-effects.png")))

    def reset(self):
        super().reset()
        self.paladin = Paladin(self.width - 300, self.FLOOR_Y)
        self.dummies.append(self.paladin)
        self.phase = 'corridor'
        self.timer = 0.0
        self.facing = -1
        self.next_attack = 'thrust'
        self.lunge_target = self.paladin.x
        self.wave_x = self.paladin.x
        self.parry_time = 0.0
        self.parry_value = 0
        self.attack_hit = False

    @property
    def victory(self):
        return self.phase == 'victory' and self.timer <= 0

    def can_start_action(self, event, player):
        return self.phase not in ('intro', 'victory') and super().can_start_action(event, player)

    def handle_event(self, event, player):
        if self.phase not in ('intro', 'victory'):
            super().handle_event(event, player)

    def damage(self, enemy, amount):
        if enemy is not self.paladin or self.phase not in ('corridor', 'intro', 'victory'):
            super().damage(enemy, amount)

    def on_direct_hit(self, enemy, x, y, value):
        if enemy is self.paladin and random() < self.PARRY_CHANCE:
            self.parry_time = .42
            self.parry_value = value
            self.parry_direction = -1 if x < enemy.x else 1
            if self.audio:
                self.audio.play_effect('hit')
            return
        super().on_direct_hit(enemy, x, y, value)

    def update(self, dt, player, previous_attack_time, previous_action_time):
        if self.phase == 'corridor':
            if player.x >= self.ARENA_ENTRANCE:
                self.phase, self.timer = 'intro', self.INTRO_TIME
                player.clear_input()
                self.cancel_aim()
            return
        if self.phase == 'intro':
            bell_remaining = self.INTRO_TIME - self.INTRO_BELL_AT
            if self.audio and self.timer > bell_remaining >= self.timer - dt:
                self.audio.play_effect('cathedral_bell')
            self.timer -= dt
            if self.timer <= 0:
                self.phase, self.timer = 'ready', .45
            return
        if self.phase == 'victory':
            self.timer -= dt
            return
        self.parry_time = max(0, self.parry_time - dt)
        super().update(dt, player, previous_attack_time, previous_action_time)
        if not self.paladin.hp:
            self.phase, self.timer = 'victory', self.VICTORY_TIME
            player.clear_input()
            return
        if not self.health:
            return
        self.update_attack(dt, player)

    def update_attack(self, dt, player):
        boss = self.paladin
        self.timer -= dt
        if self.phase == 'ready':
            self.facing = -1 if player.x < boss.x else 1
            if self.timer > 0:
                return
            if self.next_attack == 'thrust' and abs(player.x - boss.x) > 260:
                boss.x += self.facing * 135 * dt
                return
            self.attack_hit = False
            if self.next_attack == 'thrust':
                self.lunge_target = min(self.width - 65, max(65, boss.x + self.facing * self.LUNGE_REACH))
                self.phase, self.timer = 'thrust_aim', .72
            else:
                self.phase, self.timer = 'wave_aim', .9
            if self.audio:
                self.audio.play_effect('heavy_inhale')
        elif self.phase == 'thrust_aim' and self.timer <= 0:
            self.phase = 'thrust'
        elif self.phase == 'thrust':
            before = boss.x
            boss.x += self.facing * min(abs(self.lunge_target - boss.x), self.LUNGE_SPEED * dt)
            self.hit_sweep(player, before, boss.x + self.facing * self.SWORD_REACH, 43, 2)
            if boss.x == self.lunge_target:
                self.next_attack = 'wave'
                self.phase, self.timer = 'ready', .4
        elif self.phase == 'wave_aim' and self.timer <= 0:
            self.wave_x = boss.x + self.facing * 24
            self.phase, self.timer = 'wave', .95
            if self.audio:
                self.audio.play_effect('burst')
        elif self.phase == 'wave':
            before = self.wave_x
            self.wave_x += self.facing * self.WAVE_SPEED * dt
            self.hit_sweep(player, before, self.wave_x, 28, 1)
            if self.timer <= 0:
                self.next_attack = 'thrust'
                self.phase, self.timer = 'ready', .45

    def hit_sweep(self, player, start, end, height, damage):
        feet = player.ground_y + player.jump_lift
        rolling = player.ground_action is not None and player.ground_action[0] == 3
        if (not rolling and not self.attack_hit and feet - self.FLOOR_Y <= height
                and min(start, end) - 16 <= player.x <= max(start, end) + 16):
            self.attack_hit = True
            self.hurt_player(player, damage)

    def draw_dummy(self):
        boss = self.paladin
        x = boss.x - self.camera_x
        if self.phase in ('thrust_aim', 'wave_aim'):
            reach = self.lunge_target + self.facing * self.SWORD_REACH if self.phase == 'thrust_aim' else boss.x + self.facing * 385
            left = max(0, round(min(boss.x, reach)))
            right = min(self.width, round(max(boss.x, reach)))
            for dash in range(left, right, 18):
                fill(dash, boss.y + 3, min(11, right - dash), 3, (244, 83, 71))
        if self.phase == 'wave':
            self.wave_image.clip_composite_draw(
                384, 160, 192, 160, 0, 'h' if self.facing > 0 else '',
                self.wave_x - self.camera_x - self.facing * 17, self.FLOOR_Y + 16, 72, 32,
            )
        frame = {'thrust_aim': 1, 'thrust': 2, 'wave_aim': 3, 'wave': 4, 'victory': 5}.get(self.phase, 0)
        if self.phase == 'intro':
            elapsed = self.INTRO_TIME - self.timer
            if elapsed < 0.72:
                frame = 5
            elif self.INTRO_BELL_AT <= elapsed < 2.65:
                frame = 3
        if self.parry_time > .24 and self.phase == 'ready':
            frame = 4
        row, column = divmod(frame, 3)
        cell_width, cell_height = self.paladin_image.w // 3, self.paladin_image.h // 2
        draw_width, draw_height = self.PALADIN_DRAW_SIZE
        self.paladin_image.clip_composite_draw(
            column * cell_width, (1 - row) * cell_height, cell_width, cell_height,
            0, 'h' if self.facing > 0 else '',
            x, boss.y + draw_height / 2, draw_width, draw_height,
        )
        if self.phase == 'intro':
            age = self.INTRO_TIME - self.timer - self.INTRO_BELL_AT
            if 0 <= age < 1.15:
                for index in range(10):
                    angle = index * tau / 10
                    radius = 5 + age * (26 + 8 * (index % 3))
                    size = 3 if age < .5 else 2
                    fill(x + cos(angle) * radius, boss.y + 144 + sin(angle) * radius - age * 34,
                         size, size, (255, 223, 151))
            return
        if self.phase == 'victory':
            elapsed = self.VICTORY_TIME - self.timer
            for i in range(14):
                age = elapsed - i * 0.055
                if 0 < age < 1.4:
                    angle = i * tau / 14
                    dx = cos(angle) * (9 + age * 36)
                    dy = sin(angle) * 12 + age * 51
                    fill(x + dx, boss.y + 74 + dy, 2, 4, (255, 219, 133))
            return
        if self.phase != 'corridor':
            self.draw_target_health(boss, boss.y + 188)
        if self.parry_time > 0:
            age = .42 - self.parry_time
            self.spark_font.draw(x + self.parry_direction * (48 + age * 220),
                                 boss.y + 80 + age * 260 - age * age * 360,
                                 str(self.parry_value), (255, 223, 150))
            self.spark_font.draw(x - 30, boss.y + 161, '쳐내기!', (255, 223, 150))

    def draw_banner(self, width, height, player):
        if self.phase == 'intro':
            self.draw_intro(width, height)
            return
        if self.phase == 'victory':
            if self.timer < self.VICTORY_TIME - 0.45:
                self.font.draw(width / 2 - 60, height - 105, '성기사 격파', (255, 230, 177))
            fade_to_black(1 - self.timer / 0.75)
            return
        super().draw_banner(width, height, player)
        message = {
            'corridor': '오른쪽 성당 안으로 이동하세요.',
        }.get(self.phase, '성기사는 날아오는 숫자를 쳐냅니다. 발밑의 폭발을 노리세요.')
        fill(24, height - 110, 540, 34, (19, 25, 42))
        self.spark_font.draw(38, height - 93, message, (235, 220, 184))

    def draw_intro(self, width, height):
        elapsed = self.INTRO_TIME - self.timer
        transition = min(1, elapsed / .38, self.timer / .48)
        fade_to_black(.21 * transition)
        bar = round(60 * transition)
        if bar > 0:
            fill(0, 0, width, bar, (8, 10, 16))
            fill(0, height - bar, width, bar, (8, 10, 16))
        if self.INTRO_BELL_AT <= elapsed < self.INTRO_TIME - .38:
            left = width // 2 - 169
            fill(left, 97, 338, 1, (190, 148, 79))
            self.spark_font.draw(left, 151, '뱀파이어 슬레이어', (229, 212, 177))
            self.font.draw(left, 119, '태양 문장의 성기사', (255, 225, 163))
