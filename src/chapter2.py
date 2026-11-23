"""챕터 2의 전투와 지형 배치."""

from pathlib import Path

import pico2d as p
from pico2d import pico2d as canvas
from sdl2 import SDL_RenderDrawLine, SDL_SetRenderDrawColor

try:
    from .chapter1 import ChapterOne
    from .arrowman import Arrowman
    from .selectscreen import fill
    from .terrain import bolt_hit_distance
except ImportError:
    from chapter1 import ChapterOne
    from arrowman import Arrowman
    from selectscreen import fill
    from terrain import bolt_hit_distance


class ChapterTwo(ChapterOne):
    ARROW_PLATFORM = None
    USE_GATE_MASONRY = False
    TITLE = '챕터 2  |  성 안쪽 통로'
    NEXT_STAGE = 'chapter3'
    GUARD_POSITIONS = (850, 975)
    STONE_PLATFORMS = ((580, 705, 194), (1810, 1930, 193))
    SCAFFOLDS = ((765, 980, 224), (1560, 1750, 220))
    BOXES = ((465, 524, 182), (1420, 1505, 204))
    FIRE_VENTS = ((1065, 1.0), (1980, 2.0), (2280, 2.8))

    def __init__(self, width):
        super().__init__(width)
        path = Path(__file__).resolve().parents[1] / 'assets/characters/chapter2-crossbow.png'
        self.crossbow = p.load_image(str(path))

    def reset(self):
        super().reset()
        self.dummies.append(Arrowman(2150, self.FLOOR_Y))
        self.bolts = []

    def update(self, dt, player, previous_attack_time, previous_action_time):
        super().update(dt, player, previous_attack_time, previous_action_time)
        if not self.health:
            return
        for enemy in self.dummies:
            if not isinstance(enemy, Arrowman):
                continue
            was_aiming = bool(enemy.aim)
            if enemy.advance(dt, player):
                self.bolts.append(enemy.create_bolt())
            if not was_aiming and enemy.aim and self.audio is not None:
                self.audio.play_effect('crossbow_draw')
        self.bolts = [bolt for bolt in self.bolts if self.advance_bolt(bolt, dt, player)]

    def bolt_travel_limit(self, bolt, reach):
        if bolt.dx:
            wall = self.width if bolt.dx > 0 else 0
            reach = min(reach, (wall - bolt.x) / bolt.dx)
        if bolt.dy < 0:
            reach = min(reach, (self.FLOOR_Y - bolt.y) / bolt.dy)
        for left, right, top in self.solid_obstacles:
            hit = bolt_hit_distance(bolt, reach, left, self.FLOOR_Y, right, top)
            if hit is not None:
                reach = hit
        return max(0, reach)

    def draw_bolt_line(self, bolt, start, end, color, thickness):
        x = bolt.x - self.camera_x
        y = canvas.get_canvas_height() - 1 - bolt.y
        x1, x2 = x + start * bolt.dx, x + end * bolt.dx
        y1, y2 = y - start * bolt.dy, y - end * bolt.dy
        SDL_SetRenderDrawColor(canvas.renderer, *color, 255)
        for offset in range(-thickness, thickness + 1):
            ox, oy = offset * bolt.dy, offset * bolt.dx
            SDL_RenderDrawLine(canvas.renderer, round(x1 + ox), round(y1 + oy),
                               round(x2 + ox), round(y2 + oy))

    def draw_bolt_warning(self, bolt):
        reach = self.bolt_travel_limit(bolt, bolt.remaining)
        for start in range(0, int(reach), 22):
            end = min(start + 14, reach)
            self.draw_bolt_line(bolt, start, end, (100, 18, 31), 2)
            self.draw_bolt_line(bolt, start, end, (255, 65, 75), 1)

    def advance_bolt(self, bolt, dt, player):
        travel = min(bolt.remaining, 530 * dt)
        reach = self.bolt_travel_limit(bolt, travel)
        feet = player.ground_y + player.jump_lift
        rolling = player.ground_action is not None and player.ground_action[0] == 3
        if not rolling and bolt_hit_distance(
            bolt, reach, player.x - 14, feet + 6, player.x + 14, feet + 75,
        ) is not None:
            self.hurt_player(player)
            return False
        bolt.x += bolt.dx * reach
        bolt.y += bolt.dy * reach
        bolt.remaining -= travel
        return reach == travel and bolt.remaining > 0

    def draw_dummy(self):
        super().draw_dummy()
        for enemy in self.dummies:
            if isinstance(enemy, Arrowman):
                if enemy.aim:
                    self.draw_bolt_warning(enemy.create_bolt())
                x = enemy.x - self.camera_x
                if not -64 <= x <= self.viewport_width + 64:
                    continue
                cell = self.crossbow.w // 3
                self.crossbow.clip_composite_draw(
                    cell * enemy.pose, 0, cell, self.crossbow.h,
                    0, 'h' if enemy.facing > 0 else '',
                    x, enemy.y + 55, 120, 110,
                )
                self.draw_target_health(enemy, enemy.y + 108)
        for bolt in self.bolts:
            x = bolt.x - self.camera_x
            if not -24 <= x <= self.viewport_width + 24:
                continue
            self.draw_bolt_line(bolt, -22, 0, (209, 159, 103), 1)
            fill(x - 2, bolt.y - 1, 4, 4, (248, 223, 174))
