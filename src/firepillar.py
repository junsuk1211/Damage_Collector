"""예고가 먼저 나타나는 주기적인 불기둥."""

from math import sin

try:
    from .selectscreen import fill
except ImportError:
    from selectscreen import fill


class FirePillar:
    PERIOD = 4.2
    WARNING = 0.85
    RISE = 0.65
    ACTIVE_END = 2.45
    MAX_HEIGHT = 92
    HALF_WIDTH = 20

    def __init__(self, x, ground_y, delay):
        self.x = x
        self.ground_y = ground_y
        self.phase = -delay

    def update(self, dt):
        self.phase += dt
        if self.phase >= self.PERIOD:
            self.phase %= self.PERIOD

    @property
    def height(self):
        if not self.WARNING <= self.phase < self.ACTIVE_END:
            return 0.0
        rise = min(1.0, (self.phase - self.WARNING) / self.RISE)
        fade = min(1.0, (self.ACTIVE_END - self.phase) / 0.28)
        return self.MAX_HEIGHT * rise * fade

    def hits(self, player):
        feet = player.ground_y + player.jump_lift
        return (self.height >= 8 and abs(player.x - self.x) <= self.HALF_WIDTH + 12
                and self.ground_y <= feet < self.ground_y + self.height)

    def draw(self, camera_x, viewport_width):
        x = self.x - camera_x
        if x < -40 or x > viewport_width + 40:
            return
        y = self.ground_y
        fill(x - 23, y - 4, 46, 8, (32, 28, 35))
        for offset in (-16, -8, 0, 8, 16):
            fill(x + offset - 1, y - 3, 3, 6, (108, 92, 86))
        if 0 <= self.phase < self.WARNING:
            color = (255, 169, 55) if int(self.phase * 12) % 2 else (180, 67, 36)
            fill(x - 21, y + 2, 42, 3, color)
            for offset in (-12, 0, 12):
                fill(x + offset, y + 9 + int(self.phase * 18), 3, 5, color)
        height = self.height
        if height >= 1:
            for index in range(-4, 5):
                tip = height * (0.68 + 0.16 * sin(index * 2 + self.phase * 23)
                                + 0.16 * (1 - abs(index) / 4))
                fill(x + index * 4 - 2, y, 5, tip, (220, 63, 30))
                fill(x + index * 4 - 1, y, 3, tip * 0.75, (255, 155, 42))
            fill(x - 7, y, 14, height * 0.52, (255, 232, 139))
