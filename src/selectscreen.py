"""시작 메뉴와 공용 화면 요소."""

import ctypes
import os
from pathlib import Path

import pico2d as p
from pico2d import pico2d as canvas
from sdl2 import SDL_BUTTON_LEFT, SDL_Rect, SDL_RenderFillRect, SDL_SetRenderDrawColor


def fill(x, y, width, height, color):
    rect = SDL_Rect(int(x), int(canvas.get_canvas_height() - y - height), int(width), int(height))
    SDL_SetRenderDrawColor(canvas.renderer, *color, 255)
    SDL_RenderFillRect(canvas.renderer, ctypes.byref(rect))


def korean_font(size):
    path = Path(os.environ.get('WINDIR', 'C:/Windows')) / 'Fonts/malgun.ttf'
    return p.load_font(str(path), size)


class SelectScreen:
    BUTTONS = (
        ('chapter1', '플레이', 350),
        ('instructions', '설명', 270),
        ('training', '훈련장', 190),
    )

    def __init__(self, width, height):
        self.width, self.height = width, height
        self.left = width // 2 - 150
        self.title_font = korean_font(46)
        self.font = korean_font(26)

    def handle_event(self, event):
        if event.type == p.SDL_MOUSEBUTTONDOWN and event.button == SDL_BUTTON_LEFT:
            y = self.height - 1 - event.y
            for destination, _, bottom in self.BUTTONS:
                if self.left <= event.x < self.left + 300 and bottom <= y < bottom + 58:
                    return destination
        return None

    def draw(self):
        fill(self.left - 65, 147, 430, 416, (19, 25, 42))
        self.title_font.draw(self.left - 45, 502, 'Damage Collector', (255, 218, 144))
        for _, label, bottom in self.BUTTONS:
            fill(self.left, bottom, 300, 58, (195, 152, 82))
            fill(self.left + 2, bottom + 2, 296, 54, (39, 50, 74))
            self.font.draw(self.left + (110 if label == '설명' else 98), bottom + 29, label, (251, 238, 210))
