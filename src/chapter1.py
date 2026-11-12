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
    # 첫 상자를 넘은 뒤 평지 전투, 후반은 석단과 발판을 잇는 위쪽 경로.
    GUARD_POSITIONS = (930, 1950)
    STONE_PLATFORMS = ((1270, 1408, 193),)
    SCAFFOLDS = ((1468, 1718, 225), (1785, 1925, 192))
    BOXES = (
        (385, 428, 173),     # 작은 상자
        (1145, 1216, 188),   # 중간 보급 상자
    )
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
        # Image crops use top-left coordinates, while pico2d clips from the bottom.
        stone = (743, 362, 685, 277)
        scaffold = (1464, 252, 694, 392)
        for left, right, top in self.BOXES:
            x, width = left - self.camera_x, right - left
            if x < self.viewport_width and x + width > 0:
                height = top - self.FLOOR_Y
                self.crate.clip_draw(98, self.crate.h - 1100, 1120, 1000,
                                     x + width / 2, self.FLOOR_Y + height / 2, width, height)
        props = [(platform, stone) for platform in self.STONE_PLATFORMS]
        props.extend((platform, scaffold) for platform in self.SCAFFOLDS)
        for (left, right, top), (source_x, source_y, source_width, source_height) in props:
            x, width = left - self.camera_x, right - left
            if x >= self.viewport_width or x + width <= 0:
                continue
            height = top - self.FLOOR_Y
            self.props.clip_draw(
                source_x, self.props.h - source_y - source_height, source_width, source_height,
                x + width / 2, self.FLOOR_Y + height / 2, width, height,
            )
        if self.NEXT_STAGE:
            self.draw_exit_marker()
        for pillar in self.fire_pillars:
            pillar.draw(self.camera_x, self.viewport_width)

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
