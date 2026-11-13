"""챕터 1 경비병의 이동과 전투."""

from pathlib import Path

import pico2d as p

try:
    from .selectscreen import fill
    from .trainingcenter import TrainingCenter
    from .shieldman import Shieldman
    from .terrain import stop_at_boxes
    from .firepillar import FirePillar
except ImportError:
    from selectscreen import fill
    from trainingcenter import TrainingCenter
    from shieldman import Shieldman
    from terrain import stop_at_boxes
    from firepillar import FirePillar


class ChapterOne(TrainingCenter):
    MAX_HEALTH = 5
    FLOOR_Y = 144
    TITLE = '챕터 1  |  성문 경비병'
    NEXT_STAGE = 'chapter2'
    # 성문 앞의 낮은 석단으로 점프를 익히고, 후반에는 돌기둥 사이의 통로를 건넌다.
    GUARD_POSITIONS = (930, 1950)
    STONE_PLATFORMS = ((445, 513, 176), (1290, 1398, 194))
    SCAFFOLDS = ((1468, 1688, 223), (1760, 1892, 191))
    BOXES = ()
    USE_GATE_MASONRY = True
    FIRE_VENTS = ((1035, 1.2), (2090, 2.3))

    @property
    def platforms(self):
        return self.SCAFFOLDS

    @property
    def solid_obstacles(self):
        return (*self.BOXES, *self.STONE_PLATFORMS)

    @property
    def exit_x(self):
        return self.width - 110

    def can_advance(self, player):
        return bool(self.NEXT_STAGE and not self.dummies and player.x >= self.exit_x)

    def __init__(self, width):
        super().__init__(width * 2)
        self.viewport_width = width
        path = Path(__file__).resolve().parents[1] / 'assets/characters/chapter1-guard.png'
        self.guard_image = p.load_image(str(path))
        if not self.USE_GATE_MASONRY:
            props_path = path.parents[1] / 'props/chapter1-props.png'
            self.props = p.load_image(str(props_path))
            self.crate = p.load_image(str(props_path.with_name('ironbound-crate.png')))

    def reset(self):
        super().reset()
        self.dummies = [Shieldman(x, self.FLOOR_Y) for x in self.GUARD_POSITIONS]
        self.health = self.MAX_HEALTH
        self.hurt_time = 0.0
        self.fire_pillars = [FirePillar(x, self.FLOOR_Y, delay) for x, delay in self.FIRE_VENTS]

    def handle_event(self, event, player):
        if self.health and not (event.type == p.SDL_KEYDOWN and event.key == p.SDLK_i):
            super().handle_event(event, player)

    def damage(self, dummy, amount):
        super().damage(dummy, amount)
        if dummy.attack_age is not None:
            dummy.attack_age = None
            dummy.cooldown = 0.45

    def aim_arc(self, player):
        arc = super().aim_arc(player)
        arc.ground_y = max((top for left, right, top in (*self.platforms, *self.solid_obstacles)
                            if left <= arc.landing_x <= right), default=self.FLOOR_Y) + 8
        return arc

    def update(self, dt, player, previous_attack_time, previous_action_time):
        if not self.health:
            return
        super().update(dt, player, previous_attack_time, previous_action_time)
        self.hurt_time = max(0.0, self.hurt_time - dt)
        for pillar in self.fire_pillars:
            pillar.update(dt)
            if pillar.hits(player):
                self.hurt_player(player)
        for guard in self.dummies:
            if (guard.attack_age is None and guard.obstacle_jump is None
                    and guard.y == self.FLOOR_Y and abs(player.x - guard.x) > 520):
                guard.walk_time = 0.0
                guard.speed = 0.0
                continue
            if guard.advance(dt, player, self.solid_obstacles, self.FLOOR_Y, self.platforms):
                distance = (player.x - guard.x) * guard.facing
                if (abs(player.ground_y + player.jump_lift - guard.y) < 45
                        and stop_at_boxes(guard.x, player.x, guard.y, 0, self.solid_obstacles) == player.x
                        and -12 <= distance <= 87):
                    self.hurt_player(player)

    def hurt_player(self, player):
        rolling = player.ground_action is not None and player.ground_action[0] == 3
        if self.health and not self.hurt_time and not rolling:
            self.health -= 1
            self.hurt_time = 0.65
            self.stored.clear()
            self.cancel_aim()

    def draw_props(self):
        if self.USE_GATE_MASONRY:
            for left, right, top in self.STONE_PLATFORMS:
                self.draw_gate_masonry(left, right, top, raised=False)
            for left, right, top in self.SCAFFOLDS:
                self.draw_gate_masonry(left, right, top, raised=True)
        else:
            self.draw_furniture()
        if self.NEXT_STAGE:
            self.draw_exit_marker()
        for pillar in self.fire_pillars:
            pillar.draw(self.camera_x, self.viewport_width)

    def draw_gate_masonry(self, left, right, top, *, raised):
        x, width = int(left - self.camera_x), right - left
        if x >= self.viewport_width or x + width <= 0:
            return
        floor = self.FLOOR_Y
        shadow = (30, 29, 42)
        stone = (91, 98, 116)
        lit_stone = (147, 152, 159)
        bevel = (57, 62, 81)
        bronze = (174, 136, 91)

        # 발판 아래는 열린 통로로 보여 줘 아래로도 지나갈 수 있음을 드러낸다.
        cap_height = 13 if raised else 11
        cap_bottom = top - cap_height
        self.draw_prop_shadow(x, width, floor)
        supports = ((x + 10, 19), (x + width - 29, 19)) if raised else ((x + 4, width - 8),)
        for base_x, base_width in supports:
            fill(base_x, floor, base_width, cap_bottom - floor, shadow)
            for row, y in enumerate(range(floor + 3, cap_bottom, 10)):
                height = min(8, cap_bottom - y)
                fill(base_x + 2, y, base_width - 4, height, stone)
                fill(base_x + base_width - 5, y, 3, height, bevel)
                fill(base_x + 2, y + height - 1, base_width - 4, 1, lit_stone)
                if not raised:
                    seam = base_x + base_width // 2 + (6 if row % 2 else -7)
                    fill(seam, y, 2, height, shadow)
                if height >= 5:
                    nick = base_x + 4 + (row * 7) % (base_width - 10)
                    fill(nick, y + 2, 4, 1, bevel)
            if raised:
                # 돌기둥의 주춧돌과 받침돌이 위쪽 석판의 무게를 받는다.
                fill(base_x - 3, floor, base_width + 6, 6, bevel)
                fill(base_x - 3, floor + 5, base_width + 6, 1, lit_stone)
                fill(base_x - 2, cap_bottom - 5, base_width + 4, 5, bevel)
                fill(base_x - 2, cap_bottom - 5, base_width + 4, 1, stone)

        fill(x, cap_bottom, width, cap_height, shadow)
        fill(x + 1, cap_bottom + 2, width - 2, 2, bevel)
        fill(x + 1, cap_bottom + 4, width - 2, cap_height - 6, (115, 120, 135))
        for joint in range(x + 27, x + width - 4, 30):
            fill(joint, cap_bottom + 2, 2, cap_height - 3, (66, 68, 87))
            fill(joint + 3, cap_bottom + 5, 5, 1, lit_stone)
        fill(x, top - 2, width, 2, (191, 185, 171))
        for end in (x + 3, x + width - 8):
            fill(end, cap_bottom + 2, 5, cap_height - 4, (78, 67, 62))
            fill(end + 1, top - 6, 2, 2, bronze)
        if raised:
            # 성문 깃발의 마름모 문양을 석판 중앙에 작게 새긴다.
            center = x + width // 2
            fill(center - 5, cap_bottom + 2, 11, 9, bevel)
            for offset, span in enumerate((1, 3, 5, 7, 5, 3, 1)):
                fill(center - span // 2, cap_bottom + 3 + offset, span, 1, bronze)
            fill(center, cap_bottom + 6, 1, 1, shadow)

    def draw_furniture(self):
        # Image crops use top-left coordinates, while pico2d clips from the bottom.
        stone = (743, 362, 685, 277)
        scaffold = (1464, 252, 694, 392)
        for left, right, top in self.BOXES:
            x, width = left - self.camera_x, right - left
            if x < self.viewport_width and x + width > 0:
                height = top - self.FLOOR_Y
                self.draw_prop_shadow(x, width, self.FLOOR_Y)
                fill(x - 2, self.FLOOR_Y, width + 4, height, (25, 19, 24))
                self.crate.clip_draw(98, self.crate.h - 1100, 1120, 1000,
                                     x + width / 2, self.FLOOR_Y + height / 2, width, height)
                fill(x, self.FLOOR_Y + 1, 2, height - 3, (171, 108, 59))
                fill(x + width - 2, self.FLOOR_Y + 1, 2, height - 3, (117, 70, 48))
                self.draw_prop_edge(x, width, top, (255, 205, 125), (145, 84, 47))
                for corner in (x + 3, x + width - 7):
                    fill(corner, top - 13, 4, 7, (178, 121, 68))
                    fill(corner, top - 10, 2, 2, (255, 224, 157))
        props = [(platform, stone) for platform in self.STONE_PLATFORMS]
        props.extend((platform, scaffold) for platform in self.SCAFFOLDS)
        for (left, right, top), (source_x, source_y, source_width, source_height) in props:
            x, width = left - self.camera_x, right - left
            if x >= self.viewport_width or x + width <= 0:
                continue
            height = top - self.FLOOR_Y
            self.draw_prop_shadow(x, width, self.FLOOR_Y)
            self.props.clip_draw(
                source_x, self.props.h - source_y - source_height, source_width, source_height,
                x + width / 2, self.FLOOR_Y + height / 2, width, height,
            )
            if source_x == stone[0]:
                self.draw_prop_edge(x, width, top, (208, 220, 204), (104, 128, 120))
            else:
                self.draw_prop_edge(x, width, top, (244, 189, 116), (135, 82, 54))

    @staticmethod
    def draw_prop_shadow(x, width, floor):
        fill(x - 4, floor - 3, width + 8, 4, (22, 18, 29))

    @staticmethod
    def draw_prop_edge(x, width, top, highlight, face):
        # 물리 판정의 윗면에 맞춰 밝은 모서리를 그린다.
        fill(x - 2, top - 8, width + 4, 9, (35, 28, 35))
        fill(x, top - 6, width, 4, face)
        fill(x, top - 2, width, 2, highlight)

    def draw_exit_marker(self):
        x = self.exit_x - self.camera_x
        if x > self.viewport_width + 42:
            return
        y = self.FLOOR_Y
        ready = not self.dummies
        border = (255, 210, 112) if ready else (146, 130, 113)
        fill(x + 30, y, 6, 66, (88, 60, 49))
        fill(x - 12, y + 53, 90, 30, border)
        fill(x - 10, y + 55, 86, 26, (31, 29, 43))
        self.spark_font.draw(x, y + 68, '출구  →', border)

    def draw_dummy(self):
        width, height = self.guard_image.w // 4, self.guard_image.h // 2
        for guard in self.dummies:
            column, row = guard.sprite_cell()
            left, right = column * width, (column + 1) * width
            if row == 1 and column in (0, 1):
                # 베기 잔상이 첫 번째 셀의 오른쪽 여백까지 뻗는다.
                split = round(width * 0.83)
                if column == 0:
                    right = split
                else:
                    left = split
            offset = ((left + right) / 2 - (column + 0.5) * width) * 116 / width
            self.guard_image.clip_composite_draw(
                left, (1 - row) * height, right - left, height,
                0, 'h' if guard.facing > 0 else '',
                guard.x - self.camera_x - guard.facing * offset,
                guard.y + 47, 116 * (right - left) / width, 116,
            )
            self.draw_target_health(guard, guard.y + 108)

    def draw_banner(self, width, height, player):
        self.draw_number_effects(player)
        fill(0, height - 62, width, 62, (19, 25, 42))
        self.font.draw(24, height - 30, self.TITLE, (255, 230, 177))
        for index in range(self.MAX_HEALTH):
            color = (226, 87, 79) if index < self.health else (73, 42, 52)
            fill(310 + index * 26, height - 40, 20, 20, color)
        held = ' + '.join(str(value) for value, _ in self.stored) or '없음'
        remaining = len(self.dummies)
        self.font.draw(465, height - 30, f'보관 {held}    남은 경비병 {remaining}    Esc 시작 화면', (153, 227, 245))
        if not self.dummies:
            if self.NEXT_STAGE:
                message = '[Z] 다음 스테이지' if self.can_advance(player) else '클리어 · 오른쪽 출구로 이동'
            else:
                message = '챕터 2 클리어 · [Esc] 시작 화면'
            fill(width - 325, height - 110, 305, 36, (19, 25, 42))
            self.font.draw(width - 311, height - 92, message, (255, 230, 177))
