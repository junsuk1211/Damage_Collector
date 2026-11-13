"""발판을 밟으면 해당 석판 위로 떨어지는 화살 함정."""

try:
    from .selectscreen import fill
except ImportError:
    from selectscreen import fill


class ArrowRain:
    WARNING = 0.45
    SPEED = 700
    DROP_HEIGHT = 360
    WAVE_INTERVAL = 0.23

    def __init__(self, platform):
        self.left, self.right, self.top = platform
        self.center = (self.left + self.right) / 2
        self.elapsed = None
        self.spent = False
        self.arrows = tuple(
            (self.left + 12 + (self.right - self.left - 24) * (lane + offset) / 7,
             wave * self.WAVE_INTERVAL + lane % 3 * 0.04)
            for wave, offset in enumerate((0.0, 0.5, 0.2))
            for lane in range(8 if wave == 0 else 7)
        )

    def update(self, dt, player):
        if self.spent:
            return False
        feet = player.ground_y + player.jump_lift
        pressed = abs(player.x - self.center) <= 20 and abs(feet - self.top) < 1
        if pressed and self.elapsed is None:
            self.elapsed = 0.0
        if self.elapsed is None:
            return False

        previous = self.elapsed
        self.elapsed += dt
        end = self.WARNING + max(delay for _, delay in self.arrows) + self.DROP_HEIGHT / self.SPEED
        if self.elapsed >= end:
            self.spent = True
        if feet < self.top or not self.left <= player.x <= self.right:
            return False
        for x, delay in self.arrows:
            start = self.WARNING + delay
            impact = start + self.DROP_HEIGHT / self.SPEED
            if self.elapsed < start or previous >= impact or abs(player.x - x) > 14:
                continue
            tip = self.arrow_y(self.elapsed, start)
            previous_tip = self.arrow_y(previous, start)
            if tip <= feet + 70 and previous_tip + 22 >= feet:
                return True
        return False

    def arrow_y(self, elapsed, start):
        age = max(0.0, elapsed - start)
        return max(self.top, self.top + self.DROP_HEIGHT - age * self.SPEED)

    def draw(self, camera_x):
        center = self.center - camera_x
        y = self.top
        plate = (85, 57, 64) if self.spent else (172, 48, 52)
        marking = (137, 107, 111) if self.spent else (255, 80, 71)
        fill(center - 21, y - 9, 42, 9, (41, 22, 33))
        fill(center - 19, y - 7, 38, 7, plate)
        fill(center - 19, y - 2, 38, 2, marking)
        fill(center - 2, y + 5, 4, 10, marking)
        fill(center - 2, y, 4, 3, marking)
        if self.elapsed is None or self.spent:
            return
        if self.elapsed < self.WARNING:
            for x in range(self.left + 4, self.right - 4, 14):
                fill(x - camera_x, y + 2, 7, 2, (245, 85, 70))
        for x, delay in self.arrows:
            start = self.WARNING + delay
            age = self.elapsed - start
            if 0 <= age < self.DROP_HEIGHT / self.SPEED:
                x -= camera_x
                tip = self.arrow_y(self.elapsed, start)
                fill(x - 1, tip + 5, 2, 17, (183, 137, 91))
                fill(x - 3, tip + 17, 6, 5, (200, 203, 214))
                fill(x - 3, tip + 3, 6, 4, (222, 226, 235))
                fill(x - 1, tip, 2, 3, (247, 224, 181))
