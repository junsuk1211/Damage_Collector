"""훈련장에서 허수아비를 생성하고 단검 공격을 시험한다."""

import pico2d as p

try:
    from .selectscreen import fill, korean_font
except ImportError:
    from selectscreen import fill, korean_font


class TrainingCenter:
    MAX_HP = 10
    HIT_TIME = 0.10
    ATTACK_REACH = 92

    def __init__(self):
        self.font = korean_font(22)
        self.reset()

    def reset(self):
        self.x = self.y = 0
        self.hp = 0
        self.flash = 0.0

    def handle_event(self, event, player):
        if event.type == p.SDL_KEYDOWN and event.key == p.SDLK_i:
            self.x, self.y = player.x, player.ground_y
            self.hp = self.MAX_HP
            self.flash = 0.0

    def update(self, dt, player, previous_attack_time):
        self.flash = max(0.0, self.flash - dt)
        if previous_attack_time is None or player.attack_time is None or not self.hp:
            return
        if previous_attack_time < self.HIT_TIME <= player.attack_time:
            distance = (self.x - player.x) * player.facing
            if -18 <= distance <= self.ATTACK_REACH:
                self.hp -= 1
                self.flash = 0.16

    def draw_dummy(self):
        if not self.hp:
            return
        x, y = self.x, self.y
        straw = (255, 225, 164) if self.flash else (213, 167, 81)
        fill(x - 4, y, 8, 74, (109, 67, 43))
        fill(x - 35, y + 48, 70, 8, (142, 93, 53))
        fill(x - 19, y + 29, 38, 37, straw)
        fill(x - 12, y + 65, 24, 23, straw)
        fill(x - 18, y + 81, 36, 5, (83, 54, 44))
        fill(x - 19, y + 41, 38, 4, (114, 71, 46))
        fill(x - 28, y + 99, 56, 6, (77, 34, 41))
        fill(x - 28, y + 99, 56 * self.hp / self.MAX_HP, 6, (240, 105, 80))

    def draw_banner(self, width, height):
        fill(0, height - 52, width, 52, (19, 25, 42))
        self.font.draw(24, height - 26, '훈련장  |  I키를 누를 시 허수아비 더미를 생성합니다', (255, 230, 177))
