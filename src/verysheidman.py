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
    LUNGE_RANGE = 300
    LUNGE_SPEED = 440
    LUNGE_WARNING = 0.85
    LUNGE_RECOVERY = 0.32
    LUNGE_BLADE_REACH = 36
    LUNGE_HEIGHT = 44
    USE_GUARD_SPRITE = False
    hp: int = MAX_HP
    barrier: int = MAX_BARRIER
    stagger: float = 0.0
    lunge_end: float | None = None
    lunge_windup: float = 0.0
    lunge_hit: bool = False
    lunge_recovery: float = 0.0
    lunge_elapsed: float = 0.0

    def prepare_lunge(self, player_x, width):
        self.facing = 1 if player_x >= self.x else -1
        self.lunge_end = max(19, min(width - 19, self.x + self.facing * self.LUNGE_RANGE))
        self.lunge_windup = self.LUNGE_WARNING
        self.lunge_hit = False
        self.lunge_elapsed = 0.0

    def advance_lunge(self, dt, player):
        if self.lunge_recovery > 0:
            self.lunge_recovery = max(0.0, self.lunge_recovery - dt)
            return False
        if self.lunge_windup > 0:
            self.lunge_windup = max(0.0, self.lunge_windup - dt)
            return False

        previous_x = self.x
        self.lunge_elapsed += dt
        self.x += self.facing * min(abs(self.lunge_end - self.x), self.LUNGE_SPEED * dt)
        if abs(self.lunge_end - self.x) < 0.001:
            self.x = self.lunge_end
            self.lunge_end = None
            self.lunge_recovery = self.LUNGE_RECOVERY
            self.cooldown = self.ATTACK_COOLDOWN

        feet = player.ground_y + player.jump_lift
        passed = (player.x - previous_x) * self.facing
        traveled = abs(self.x - previous_x)
        if (not self.lunge_hit and abs(feet - self.y) <= self.LUNGE_HEIGHT
                and -14 <= passed <= traveled + self.LUNGE_BLADE_REACH):
            self.lunge_hit = True
            return True
        return False

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

    def thrust_frame(self):
        if self.lunge_windup:
            return 0 if self.lunge_windup > 0.55 else 1
        if self.lunge_end is not None:
            if self.lunge_elapsed < 0.10:
                return 2
            return 3 if self.lunge_elapsed < 0.44 else 4
        if self.lunge_recovery:
            return 4 if self.lunge_recovery > 0.24 else 5
        return None

    def sprite_cell(self):
        if self.stagger or self.flash:
            return 3, 1
        if self.attack_age is not None:
            return (0 if self.attack_age < self.ATTACK_HIT_TIME
                    else 1 if self.attack_age < 0.88 else 2), 1
        return super().sprite_cell()
