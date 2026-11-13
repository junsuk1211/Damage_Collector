"""예고가 먼저 나타나는 주기적인 불기둥."""

from math import cos, sin, tau

try:
    from .selectscreen import fill
except ImportError:
    from selectscreen import fill


class FirePillar:
    PERIOD = 4.2
    WARNING = 0.85
    RISE = 0.65
    ACTIVE_END = 2.45
    MAX_HEIGHT = 52
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
            charge = self.phase / self.WARNING
            pulse = 0.65 + 0.35 * sin(self.phase * 24) ** 2
            color = (int(255 * pulse), int((115 + 65 * charge) * pulse), 42)
            fill(x - 21, y + 2, 42, 3, color)
            for index in range(8):
                angle = tau * index / 8 + self.phase * 2
                fill(x + cos(angle) * (26 - 10 * charge), y + sin(angle) * 6 + 4,
                     3, 3, color)
        height = self.height
        if height >= 1:
            self.draw_flame(x, y, height)
        if self.WARNING <= self.phase < self.ACTIVE_END + 0.35:
            self.draw_embers(x, y)

    def draw_flame(self, x, y, height):
        elapsed = self.phase - self.WARNING
        fill(x - 27, y - 2, 54, 5, (125, 43, 34))
        fill(x - 20, y, 40, 3, (255, 167, 59))
        if elapsed < 0.24:
            radius = 15 + elapsed * 135
            for index in range(16):
                angle = tau * index / 16
                fill(x + cos(angle) * radius, y + sin(angle) * radius * 0.22 + 5,
                     4, 2, (255, 194, 85))
        for row in range(0, int(height), 4):
            ratio = row / height
            center = x + sin(ratio * 10 - elapsed * 21) * 5 * ratio
            width = (35 - 24 * ratio) * (0.84 + 0.16 * sin(ratio * 19 - elapsed * 26))
            band = min(4, height - row)
            fill(center - width / 2 - 3, y + row, width + 6, band, (176, 44, 34))
            fill(center - width / 2, y + row, width, band, (255, 102, 28))
            if ratio < 0.84:
                core = width * (0.76 - ratio * 0.46)
                fill(center - core / 2, y + row, core, band, (255, 189, 55))
            if ratio < 0.56:
                core = width * (0.38 - ratio * 0.34)
                fill(center - core / 2, y + row, core, band, (255, 246, 167))

    def draw_embers(self, x, y):
        elapsed = self.phase - self.WARNING
        for index in range(14):
            lifetime = 0.32 + 0.035 * (index % 6)
            age = elapsed - index * 0.035
            if age < 0:
                continue
            emission = elapsed - age % lifetime
            if emission >= self.ACTIVE_END - self.WARNING:
                continue
            progress = (age % lifetime) / lifetime
            direction = -1 if index % 2 else 1
            spread = 14 + (index % 5) * 8
            ember_x = x + direction * (4 + spread * progress)
            ember_y = y + (self.MAX_HEIGHT + 15 + (index % 4) * 7) * progress - 25 * progress ** 2
            color = (255, int(226 - 142 * progress), int(110 - 70 * progress))
            size = 4 if progress < 0.55 else 2
            fill(ember_x, ember_y - 5, 2, 4, (153, 60, 28))
            fill(ember_x, ember_y, size, size, color)
