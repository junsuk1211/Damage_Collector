"""수비병의 이동, 검 공격, 애니메이션 상태."""

from dataclasses import dataclass

try:
    from .trainingcenter import Dummy
    from .terrain import stop_at_boxes
except ImportError:
    from trainingcenter import Dummy
    from terrain import stop_at_boxes


@dataclass
class ObstacleJump:
    start_x: float
    end_x: float
    start_y: float
    top_y: float
    age: float = -0.12


@dataclass
class Shieldman(Dummy):
    MAX_HP = 12
    hp: int = MAX_HP
    facing: int = -1
    walk_time: float = 0.0
    attack_age: float | None = None
    cooldown: float = 0.0
    obstacle_jump: ObstacleJump | None = None
    fall_speed: float = 0.0

    def advance(self, dt, player, boxes=(), floor_y=144):
        self.cooldown = max(0.0, self.cooldown - dt)
        if self.obstacle_jump is not None:
            jump = self.obstacle_jump
            jump.age += dt
            progress = min(1.0, max(0.0, jump.age / 0.38))
            rise = min(1.0, progress / 0.46)
            across = max(0.0, (progress - 0.46) / 0.54)
            self.x = jump.start_x + (jump.end_x - jump.start_x) * across
            self.y = (jump.start_y + (jump.top_y - jump.start_y) * rise
                      + 4 * 14 * progress * (1 - progress))
            if progress == 1:
                self.obstacle_jump = None
                self.cooldown = max(self.cooldown, 0.18)
            return False
        support = max((top for left, right, top in boxes
                       if left - 19 < self.x < right + 19 and top <= self.y), default=floor_y)
        if self.y > support:
            self.fall_speed += 850 * dt
            self.y = max(support, self.y - self.fall_speed * dt)
            return False
        self.fall_speed = 0.0
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
        blocked = stop_at_boxes(self.x, player.x, self.y, 0, boxes) != player.x
        different_level = abs(player.ground_y + player.jump_lift - self.y) >= 45
        if abs(offset) > 62 or blocked or different_level:
            distance = abs(offset) if blocked or different_level else abs(offset) - 62
            next_x = self.x + self.facing * min(108 * dt, distance)
            stopped_x = stop_at_boxes(self.x, next_x, self.y, 19, boxes)
            self.walk_time = self.walk_time + dt if stopped_x != self.x else 0.0
            self.x = stopped_x
            if stopped_x != next_x:
                for left, right, top in boxes:
                    edge = left - 19 if self.facing > 0 else right + 19
                    if self.x == edge and self.y < top:
                        landing = left + 13 if self.facing > 0 else right - 13
                        self.obstacle_jump = ObstacleJump(self.x, landing, self.y, top)
                        break
        else:
            self.walk_time = 0.0
            if not self.cooldown:
                self.attack_age = 0.0
        return False

    def sprite_cell(self):
        if self.flash > 0:
            return 3, 1
        if self.obstacle_jump is not None:
            return (2 if self.obstacle_jump.age > 0 else 0), 0
        if self.attack_age is not None:
            return (0 if self.attack_age < 0.38 else 1 if self.attack_age < 0.49 else 2), 1
        if self.walk_time:
            return 1 + int(self.walk_time / 0.12) % 3, 0
        return 0, 0

