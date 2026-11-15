"""석궁병의 기본 전투 데이터."""

from dataclasses import dataclass

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

    def advance(self, dt, player):
        self.reload = max(0, self.reload - dt)
        if self.aim:
            self.aim -= dt
            if self.aim <= 0:
                self.aim = 0
                self.reload = 1.15
                return True
        elif not self.reload and abs(player.x - self.x) <= 470:
            self.facing = -1 if player.x < self.x else 1
            self.aim = 0.65
        return False

    @property
    def pose(self):
        return 1 if self.aim else 2 if self.reload else 0


@dataclass
class Bolt:
    x: float
    y: float
    facing: int
    remaining: float = 520.0
