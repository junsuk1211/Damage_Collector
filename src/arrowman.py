"""석궁병의 기본 전투 데이터."""

from dataclasses import dataclass
from math import hypot

try:
    from .trainingcenter import Dummy
except ImportError:
    from trainingcenter import Dummy


@dataclass
class Arrowman(Dummy):
    MAX_HP = 9
    hp: int = MAX_HP
    facing: int = -1
    aim: float = 0.0
    reload: float = 0.0
    aim_dx: float = -1.0
    aim_dy: float = 0.0

    def advance(self, dt, player):
        self.reload = max(0, self.reload - dt)
        if self.aim:
            self.track(player)
            self.aim -= dt
            if self.aim <= 0:
                self.aim = 0
                self.reload = 1.15
                return True
        elif not self.reload and abs(player.x - self.x) <= 470:
            self.track(player)
            self.aim = 0.65
        return False

    def track(self, player):
        self.facing = -1 if player.x < self.x else 1
        x, y = self.muzzle
        dx = player.x - x
        dy = player.ground_y + player.jump_lift + 42 - y
        length = hypot(dx, dy)
        if length:
            self.aim_dx, self.aim_dy = dx / length, dy / length

    @property
    def muzzle(self):
        # 가까이 붙은 플레이어에게도 조준할 수 있도록 석궁 몸통에서 시작한다.
        return self.x, self.y + 53

    @property
    def pose(self):
        return 1 if self.aim else 2 if self.reload else 0

    def create_bolt(self):
        x, y = self.muzzle
        return Bolt(x, y, self.aim_dx, self.aim_dy)


@dataclass
class Bolt:
    x: float
    y: float
    dx: float
    dy: float
    remaining: float = 520.0
