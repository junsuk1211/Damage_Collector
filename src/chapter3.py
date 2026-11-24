"""증강을 적용해 진입할 수 있는 성 내부 후속 구간."""

from pathlib import Path
from math import sin

import pico2d as p

try:
    from .arrowman import Arrowman
    from .chapter1 import ChapterOne
    from .tower_fire import TowerBolt
    from .trainingcenter import Dummy
    from .verysheidman import Verysheidman
    from .selectscreen import fill
except ImportError:
    from arrowman import Arrowman
    from chapter1 import ChapterOne
    from tower_fire import TowerBolt
    from trainingcenter import Dummy
    from verysheidman import Verysheidman
    from selectscreen import fill


class Watchtower(Dummy):
    MAX_HP = 10
    DROPS_NUMBERS = False


class ChapterThree(ChapterOne):
    TITLE = '챕터 3  |  성벽 순찰로'
    SCREENS_WIDE = 1
    NEXT_STAGE = 'chapter4'
    ARROW_PLATFORM = None
    GUARD_POSITIONS = (470, 630)
    HEAVY_POSITIONS = (1090,)
    STONE_PLATFORMS = ()
    SCAFFOLDS = ()
    FIRE_VENTS = ()
    TOWER_ARCHER_POSITION = (85, 545)
    TOWER_AIM_TIME = 1.15
    TOWER_RELOAD_TIME = 3.4
    TOWER_COLLAPSE_TIME = 1.55

    def __init__(self, width):
        super().__init__(width)
        path = Path(__file__).resolve().parents[1] / 'assets/characters/chapter3-heavy.png'
        self.heavy_image = p.load_image(str(path))
        self.thrust_image = p.load_image(str(path.with_name("chapter3-thrust.png")))
        self.crossbow_image = p.load_image(str(path.with_name('chapter2-crossbow.png')))
        ruined_path = path.parents[1] / 'backgrounds/castle-rampart-ruined.png'
        self.ruined_rampart = p.load_image(str(ruined_path))
        self.tower_masonry = p.load_image(str(ruined_path.with_name('castle-rampart-tower.png')))

    def reset(self):
        super().reset()
        self.dummies.extend(Verysheidman(x, self.FLOOR_Y) for x in self.HEAVY_POSITIONS)
        self.tower_archer = Arrowman(*self.TOWER_ARCHER_POSITION, facing=1, reload=1.1)
        self.watchtower = Watchtower(53, self.FLOOR_Y)
        self.dummies.append(self.watchtower)
        self.tower_warning = None
        self.tower_bolts = []
        self.tower_collapse_age = None
        self.show_intro = True

    def can_start_action(self, event, player):
        return not self.show_intro and super().can_start_action(event, player)

    def handle_event(self, event, player):
        if self.show_intro:
            if (event.type == p.SDL_KEYDOWN and event.key in (p.SDLK_RETURN, p.SDLK_KP_ENTER)
                    and not getattr(event, 'repeat', False)):
                self.show_intro = False
            return
        super().handle_event(event, player)

    def update(self, dt, player, previous_attack_time, previous_action_time):
        if not self.show_intro:
            super().update(dt, player, previous_attack_time, previous_action_time)
            self.update_tower(dt, player)
            if self.tower_collapse_age is not None:
                self.tower_collapse_age += dt

    @property
    def remaining_enemies(self):
        return sum(enemy.hp > 0 for enemy in self.dummies)

    def draw_props(self):
        if not self.watchtower.hp:
            width, height = self.viewport_width, p.get_canvas_height()
            self.ruined_rampart.draw(width / 2, height / 2, width, height)
            if self.tower_collapse_age is not None and self.tower_collapse_age < self.TOWER_COLLAPSE_TIME:
                self.draw_tower_collapse(width, height)
        super().draw_props()

    def draw_tower_collapse(self, width, height):
        age = self.tower_collapse_age
        stone = self.tower_masonry
        scale_x, scale_y = width / 1672, height / 941
        for bottom, section_height, speed, drift in (
            (0, 154, 360, 16), (154, 172, 325, 42), (326, 202, 290, 68),
        ):
            drop = int(speed * age ** 2 / scale_y)
            hidden = max(0, drop - bottom)
            visible = section_height - hidden
            if visible > 0:
                y = self.FLOOR_Y + (bottom - drop + hidden + visible / 2) * scale_y
                x = stone.w * scale_x / 2 + drift * age ** 2
                stone.clip_draw(0, bottom + hidden, stone.w, visible, x, y,
                                stone.w * scale_x, visible * scale_y)

        for index in range(28):
            elapsed = age - (index % 7) * 0.065
            if not 0 <= elapsed < 0.95:
                continue
            x = 8 + index * 27 % 100 + elapsed * (40 + index % 8 * 18)
            lift = elapsed * (84 + index % 6 * 37) - 240 * elapsed ** 2
            size = max(2, int((6 + index % 9) * (1 - elapsed)))
            shade = 55 + index % 5 * 8
            fill(x, self.FLOOR_Y + max(0, lift) + 5, size, size, (shade, shade, shade + 9))

        for index in range(48):
            elapsed = age - (index % 8) * 0.085
            if not 0 <= elapsed < 0.9:
                continue
            x = index * 29 % 88 + elapsed * (35 + index % 9 * 22)
            y = self.FLOOR_Y + 7 + index * 13 % 37 + elapsed * (14 + index % 6 * 12)
            size = max(1, int((4 + index % 4) * (1 - elapsed)))
            shade = 54 + index % 4 * 7
            fill(x, y, size, size, (shade, shade + 3, shade + 12))

    def update_tower(self, dt, player):
        archer = self.tower_archer
        if not self.watchtower.hp or not self.health:
            archer.aim = archer.reload = 0
            self.tower_warning = None
            self.tower_bolts.clear()
            return

        if self.tower_warning is not None:
            archer.aim = max(0.0, archer.aim - dt)
            if not archer.aim:
                self.tower_bolts.append(self.tower_warning)
                self.tower_warning = None
                archer.reload = self.TOWER_RELOAD_TIME
        else:
            archer.reload = max(0.0, archer.reload - dt)
            if not archer.reload:
                archer.facing = 1 if player.x >= archer.x else -1
                archer.aim = self.TOWER_AIM_TIME
                self.tower_warning = TowerBolt.aimed_at(
                    archer.x + 37 * archer.facing, archer.y + 6, player, self.FLOOR_Y,
                )
                if self.audio is not None:
                    self.audio.play_effect('crossbow_draw')
        self.tower_bolts = [bolt for bolt in self.tower_bolts
                            if bolt.advance(dt, player, self.hurt_player)]

    def draw_banner(self, width, height, player):
        super().draw_banner(width, height, player)
        if not self.show_intro:
            return

        left, bottom = (width - 660) // 2, (height - 292) // 2
        fill(left, bottom, 660, 292, (79, 188, 233))
        fill(left + 2, bottom + 2, 656, 288, (19, 25, 42))
        self.font.draw(left + 30, bottom + 251, '챕터 3   중갑병의 방벽', (255, 230, 177))
        self.font.draw(left + 30, bottom + 207, '방벽이 남아 있으면 단검으로 체력을 깎을 수 없어.', (224, 233, 242))
        self.font.draw(left + 30, bottom + 170, '[X] 적을 때려 숫자를 떨어뜨리고 [C]로 주워.', (224, 233, 242))
        self.font.draw(left + 30, bottom + 133, '[V]를 눌러 조준하고 떼면 숫자를 던져 방벽을 깎아.', (224, 233, 242))
        self.font.draw(left + 30, bottom + 96, '방벽을 깨면 중갑병이 비틀거려. 그때 단검으로 공격해!', (133, 242, 255))
        self.spark_font.draw(left + 30, bottom + 65, '왼쪽 석궁 성탑도 부숴야 오른쪽 출구가 열려.', (255, 230, 177))
        self.font.draw(left + 30, bottom + 38, '[Enter] 전투 시작', (255, 230, 177))

    def damage(self, enemy, amount):
        if isinstance(enemy, Verysheidman):
            enemy.take_number_damage(amount)
        else:
            tower_was_standing = enemy is self.watchtower and enemy.hp > 0
            super().damage(enemy, amount)
            if tower_was_standing and not enemy.hp:
                self.tower_collapse_age = 0.0
                if self.audio is not None:
                    self.audio.play_effect('tower_collapse')

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
                if self.audio is not None:
                    self.audio.play_effect('heavy_inhale')
            return

        super().advance_guard(guard, dt, player)

    def draw_dummy(self):
        super().draw_dummy()
        self.draw_tower_archer()
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

    def draw_tower_archer(self):
        if not self.watchtower.hp:
            return
        self.draw_target_health(self.watchtower, self.FLOOR_Y + 125)
        self.spark_font.draw(27, self.FLOOR_Y + 153, '석궁 성탑', (255, 230, 177))
        archer = self.tower_archer
        # 장전 때 난간 뒤로 숙이고, 조준 때만 석궁을 수평으로 내민다.
        recoil = max(0.0, 1 - (self.TOWER_RELOAD_TIME - archer.reload) / 0.18)
        if archer.aim or recoil:
            left, top, width, height = 772, 78, 442, 190
            offset = 13 - 6 * recoil
        elif archer.reload > 0.8:
            left, top, width, height = 1650, 80, 320, 210
            offset = 1
        else:
            left, top, width, height = 300, 60, 190, 180
            offset = 0
        scale = 0.17
        self.crossbow_image.clip_composite_draw(
            left, self.crossbow_image.h - top - height, width, height,
            0, 'h' if archer.facing > 0 else '',
            archer.x + offset * archer.facing - self.camera_x,
            archer.y + height * scale / 2, width * scale, height * scale,
        )
        if self.tower_warning is not None:
            self.tower_warning.draw_warning(self.camera_x)
        for bolt in self.tower_bolts:
            bolt.draw(self.camera_x)

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
        fill(x - 44, enemy.y + 158, 88, 21, (17, 34, 51))
        fill(x - 42, enemy.y + 160, 84 * enemy.barrier / enemy.MAX_BARRIER, 3, color)
        self.spark_font.draw(x - 37, enemy.y + 169,
                             f'방벽 {enemy.barrier}/{enemy.MAX_BARRIER}', color)
