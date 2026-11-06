"""챕터 1 경비병의 이동과 전투."""

from pathlib import Path

import pico2d as p

try:
    from .selectscreen import fill
    from .trainingcenter import TrainingCenter
    from .shieldman import Shieldman
except ImportError:
    from selectscreen import fill
    from trainingcenter import TrainingCenter
    from shieldman import Shieldman


class ChapterOne(TrainingCenter):
    MAX_HEALTH = 5

    def __init__(self, width):
        super().__init__(width)
        path = Path(__file__).resolve().parents[1] / 'assets/characters/chapter1-guard.png'
        self.guard_image = p.load_image(str(path))

    def reset(self):
        super().reset()
        self.dummies = [Shieldman(735, 144)]
        self.health = self.MAX_HEALTH
        self.hurt_time = 0.0

    def handle_event(self, event, player):
        if self.health and not (event.type == p.SDL_KEYDOWN and event.key == p.SDLK_i):
            super().handle_event(event, player)

    def damage(self, dummy, amount):
        super().damage(dummy, amount)
        if dummy.attack_age is not None:
            dummy.attack_age = None
            dummy.cooldown = 0.45

    def update(self, dt, player, previous_attack_time, previous_action_time):
        if not self.health:
            return
        super().update(dt, player, previous_attack_time, previous_action_time)
        self.hurt_time = max(0.0, self.hurt_time - dt)
        for guard in self.dummies:
            if guard.advance(dt, player):
                distance = (player.x - guard.x) * guard.facing
                rolling = player.ground_action is not None and player.ground_action[0] == 3
                if not self.hurt_time and not rolling and player.jump_lift < 45 and -12 <= distance <= 87:
                    self.health -= 1
                    self.hurt_time = 0.65
                    self.stored.clear()
                    self.cancel_aim()

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
                guard.x - guard.facing * offset, guard.y + 47, 116 * (right - left) / width, 116,
            )
            self.draw_target_health(guard, guard.y + 108)

    def draw_banner(self, width, height, player):
        self.draw_number_effects(player)
        fill(0, height - 62, width, 62, (19, 25, 42))
        self.font.draw(24, height - 30, '챕터 1  |  성문 경비병', (255, 230, 177))
        for index in range(self.MAX_HEALTH):
            color = (226, 87, 79) if index < self.health else (73, 42, 52)
            fill(310 + index * 26, height - 40, 20, 20, color)
        held = ' + '.join(str(value) for value, _ in self.stored) or '없음'
        self.font.draw(465, height - 30, f'보관 {held}    Esc 시작 화면', (153, 227, 245))
        if not self.dummies:
            fill(width // 2 - 170, height // 2 - 34, 340, 68, (19, 25, 42))
            self.font.draw(width // 2 - 130, height // 2, '경비병을 쓰러뜨렸다   [Esc]', (255, 230, 177))
