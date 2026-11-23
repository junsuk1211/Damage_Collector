"""숫자 방벽을 두른 중갑병의 이동과 내려찍기."""

from dataclasses import dataclass

try:
    from .shieldman import Shieldman
except ImportError:
    from shieldman import Shieldman


@dataclass
class Verysheidman(Shieldman):
    MAX_HP = 18
    MAX_BARRIER = 6
    MAX_SPEED = 64.0
    ATTACK_DISTANCE = 78
    ATTACK_REACH = 112
    ATTACK_HIT_TIME = 0.70
    ATTACK_END = 1.18
    ATTACK_COOLDOWN = 1.0
    USE_GUARD_SPRITE = False
    hp: int = MAX_HP
    barrier: int = MAX_BARRIER
    stagger: float = 0.0

    def take_number_damage(self, amount):
        self.flash = 0.16
        if self.barrier:
            self.barrier = max(0, self.barrier - amount)
            if not self.barrier:
                self.attack_age = None
                self.stagger = 1.4
                self.speed = 0.0
                self.obstacle_jump = None
            return
        self.hp = max(0, self.hp - amount)
        self.attack_age = None
        self.cooldown = max(self.cooldown, 0.45)

    def advance(self, dt, player, boxes=(), floor_y=144, platforms=()):
        if self.stagger:
            self.stagger = max(0.0, self.stagger - dt)
            self.speed = 0.0
            self.walk_time = 0.0
            self.cooldown = 0.4
            return False
        return super().advance(dt, player, boxes, floor_y, platforms)

    def sprite_cell(self):
        if self.stagger or self.flash:
            return 3, 1
        if self.attack_age is not None:
            return (0 if self.attack_age < self.ATTACK_HIT_TIME
                    else 1 if self.attack_age < 0.88 else 2), 1
        return super().sprite_cell()
