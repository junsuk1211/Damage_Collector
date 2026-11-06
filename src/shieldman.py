"""수비병의 이동, 검 공격, 애니메이션 상태."""

from dataclasses import dataclass

try:
    from .trainingcenter import Dummy
except ImportError:
    from trainingcenter import Dummy


@dataclass
class Shieldman(Dummy):
    MAX_HP = 12
    hp: int = MAX_HP
    facing: int = -1
    walk_time: float = 0.0
    attack_age: float | None = None
    cooldown: float = 0.0

    def advance(self, dt, player):
        self.cooldown = max(0.0, self.cooldown - dt)
        if self.flash > 0:
            return False
        if self.attack_age is not None:
            before = self.attack_age
            self.attack_age += dt
            if self.attack_age >= 0.72:
                self.attack_age = None
                self.cooldown = 0.65
                return False
            return before < 0.38 <= self.attack_age
        offset = player.x - self.x
        self.facing = -1 if offset < 0 else 1
        if abs(offset) > 62:
            self.x += self.facing * min(108 * dt, abs(offset) - 62)
            self.walk_time += dt
        else:
            self.walk_time = 0.0
            if not self.cooldown:
                self.attack_age = 0.0
        return False

    def sprite_cell(self):
        if self.flash > 0:
            return 3, 1
        if self.attack_age is not None:
            return (0 if self.attack_age < 0.38 else 1 if self.attack_age < 0.49 else 2), 1
        if self.walk_time:
            return 1 + int(self.walk_time / 0.12) % 3, 0
        return 0, 0

