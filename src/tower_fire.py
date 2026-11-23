"""성탑에서 내려오는 석궁 사격과 조준 표시."""

from dataclasses import dataclass
from math import hypot

from pico2d import pico2d as canvas
from sdl2 import SDL_RenderDrawLine, SDL_SetRenderDrawColor


try:
    from .terrain import bolt_hit_distance
except ImportError:
    from terrain import bolt_hit_distance


@dataclass
class TowerBolt:
    SPEED = 345

    x: float
    y: float
    dx: float
    dy: float
    remaining: float

    @classmethod
    def aimed_at(cls, x, y, player, floor):
        dx = player.x - x
        dy = player.ground_y + player.jump_lift + 42 - y
        length = hypot(dx, dy)
        return cls(x, y, dx / length, dy / length, (floor - y) * length / dy)

    def advance(self, dt, player, hurt_player):
        reach = min(self.remaining, self.SPEED * dt)
        feet = player.ground_y + player.jump_lift
        rolling = player.ground_action is not None and player.ground_action[0] == 3
        if not rolling and bolt_hit_distance(
            self, reach, player.x - 14, feet + 6, player.x + 14, feet + 75,
        ) is not None:
            hurt_player(player)
            return False
        self.x += self.dx * reach
        self.y += self.dy * reach
        self.remaining -= reach
        return self.remaining > 0

    def draw_line(self, start, end, color, camera_x):
        x = self.x - camera_x
        y = canvas.get_canvas_height() - 1 - self.y
        SDL_SetRenderDrawColor(canvas.renderer, *color, 255)
        for offset in (-1, 0, 1):
            ox, oy = offset * self.dy, offset * self.dx
            SDL_RenderDrawLine(
                canvas.renderer,
                round(x + start * self.dx + ox), round(y - start * self.dy + oy),
                round(x + end * self.dx + ox), round(y - end * self.dy + oy),
            )

    def draw_warning(self, camera_x):
        for start in range(0, int(self.remaining), 22):
            self.draw_line(start, min(start + 13, self.remaining), (255, 65, 75), camera_x)
