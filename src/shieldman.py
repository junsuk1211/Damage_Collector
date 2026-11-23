"""수비병의 이동, 검 공격, 애니메이션 상태."""

from dataclasses import dataclass

try:
    from .trainingcenter import Dummy
    from .terrain import melee_path_clear, stop_at_boxes
except ImportError:
    from trainingcenter import Dummy
    from terrain import melee_path_clear, stop_at_boxes


@dataclass
class ObstacleJump:
    start_x: float
    end_x: float
    start_y: float
    top_y: float
    age: float = -0.07


@dataclass
class Shieldman(Dummy):
    MAX_HP = 12
    MAX_SPEED = 108.0
    ATTACK_DISTANCE = 62
    ATTACK_REACH = 87
    ATTACK_HIT_TIME = 0.38
    ATTACK_END = 0.72
    ATTACK_COOLDOWN = 0.65
    USE_GUARD_SPRITE = True
    hp: int = MAX_HP
    facing: int = -1
    walk_time: float = 0.0
    attack_age: float | None = None
    dagger_streak: int = 0
    dagger_window: float = 0.0
    cooldown: float = 0.0
    obstacle_jump: ObstacleJump | None = None
    fall_speed: float = 0.0
    speed: float = 0.0

    def advance(self, dt, player, boxes=(), floor_y=144, platforms=()):
        self.dagger_window = max(0.0, self.dagger_window - dt)
        if not self.dagger_window:
            self.dagger_streak = 0
        self.cooldown = max(0.0, self.cooldown - dt)
        if self.obstacle_jump is not None:
            jump = self.obstacle_jump
            jump.age += dt
            progress = min(1.0, max(0.0, jump.age / 0.43))
            rise = min(1.0, progress / 0.56)
            rise = rise * rise * (3 - 2 * rise)
            across = progress * progress * (3 - 2 * progress)
            self.x = jump.start_x + (jump.end_x - jump.start_x) * across
            self.y = (jump.start_y + (jump.top_y - jump.start_y) * rise
                      + 4 * 10 * progress * (1 - progress))
            if progress == 1:
                self.obstacle_jump = None
                self.cooldown = max(self.cooldown, 0.18)
                self.speed = 0.0
            return False
        ledge = max(((left, right, top) for left, right, top in (*boxes, *platforms)
                     if left - 19 < self.x < right + 19 and top <= self.y),
                    key=lambda surface: surface[2], default=None)
        support = ledge[2] if ledge else floor_y
        if self.y > support:
            self.fall_speed += 850 * dt
            self.y = max(support, self.y - self.fall_speed * dt)
            offset = player.x - self.x
            if offset * self.facing > 18:
                next_x = self.x + self.facing * min(abs(offset) - 18, self.speed * dt)
                self.x = stop_at_boxes(self.x, next_x, self.y, 19, boxes)
            return False
        self.fall_speed = 0.0
        if self.flash > 0:
            self.speed = 0.0
            return False
        if self.attack_age is not None:
            before = self.attack_age
            self.attack_age += dt
            if self.attack_age >= self.ATTACK_END:
                self.attack_age = None
                self.cooldown = self.ATTACK_COOLDOWN
                return False
            return before < self.ATTACK_HIT_TIME <= self.attack_age
        player_feet = player.ground_y + player.jump_lift
        clear = melee_path_clear(self.x, self.y, player.x, player_feet, boxes)
        target_x = player.x
        stepping_down = not clear and player_feet < self.y and ledge is not None
        if stepping_down:
            left, right, _ = ledge
            if left <= target_x <= right:
                target_x = left - 20 if self.x - left < right - self.x else right + 20
            else:
                target_x = min(target_x, left - 20) if target_x < left else max(target_x, right + 20)
        offset = target_x - self.x
        if abs(offset) > 8 or (stepping_down and offset):
            direction = -1 if offset < 0 else 1
            if direction != self.facing:
                self.speed = 0.0
                self.facing = direction
        # 높은 나무 발판 밑은 통과하고, 플레이어가 위에 있을 때만 올라간다.
        boxes = (*boxes, *(platform for platform in platforms
                           if platform[0] <= player.x <= platform[1]
                           and player.ground_y >= platform[2]))
        if abs(offset) > self.ATTACK_DISTANCE or not clear:
            distance = abs(offset) if not clear else abs(offset) - self.ATTACK_DISTANCE
            target_speed = min(self.MAX_SPEED, 45 + distance * 4)
            self.speed = min(target_speed, self.speed + 480 * dt)
            next_x = self.x + self.facing * min(self.speed * dt, distance)
            stopped_x = stop_at_boxes(self.x, next_x, self.y, 19, boxes)
            moved = abs(stopped_x - self.x)
            self.walk_time = self.walk_time + moved / self.MAX_SPEED if moved else 0.0
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
            self.speed = 0.0
            if not self.cooldown:
                self.attack_age = 0.0
        return False

    def sprite_cell(self):
        if self.flash > 0:
            return 3, 1
        if self.obstacle_jump is not None:
            age = self.obstacle_jump.age
            return (0 if age <= 0 else 2 if age < 0.28 else 3), 0
        if self.fall_speed:
            return 3, 0
        if self.attack_age is not None:
            return (0 if self.attack_age < 0.38 else 1 if self.attack_age < 0.49 else 2), 1
        if self.walk_time:
            return 1 + int(self.walk_time / 0.12) % 3, 0
        return 0, 0

