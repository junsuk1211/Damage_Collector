"""시작 메뉴와 공용 화면 요소."""

import ctypes
import os
from collections import OrderedDict
from pathlib import Path

import pico2d as p
from pico2d import pico2d as canvas
from sdl2 import SDL_BUTTON_LEFT, SDL_Rect, SDL_RenderFillRect, SDL_SetRenderDrawColor
from sdl2 import SDL_SetTextureColorMod


def fill(x, y, width, height, color):
    rect = SDL_Rect(int(x), int(canvas.get_canvas_height() - y - height), int(width), int(height))
    SDL_SetRenderDrawColor(canvas.renderer, *color, 255)
    SDL_RenderFillRect(canvas.renderer, ctypes.byref(rect))


class CachedFont:
    def __init__(self, font):
        self.font = font
        self.images = OrderedDict()

    def draw(self, x, y, label, color=(0, 0, 0)):
        image = self.images.get(label)
        if image is None:
            surface = canvas.TTF_RenderUTF8_Blended(
                self.font.font, label.encode('utf-8'), canvas.SDL_Color(255, 255, 255),
            )
            if not surface:
                return
            try:
                texture = canvas.SDL_CreateTextureFromSurface(canvas.renderer, surface)
            finally:
                canvas.SDL_FreeSurface(surface)
            if not texture:
                return
            image = self.images[label] = canvas.Image(texture)
            if len(self.images) > 96:
                self.images.popitem(last=False)
        else:
            self.images.move_to_end(label)
        SDL_SetTextureColorMod(image.texture, *color)
        image.draw(x + image.w / 2, y)


def korean_font(size):
    path = Path(os.environ.get('WINDIR', 'C:/Windows')) / 'Fonts/malgun.ttf'
    return CachedFont(p.load_font(str(path), size))


class SelectScreen:
    BUTTONS = (
        ('chapter1', '플레이', 350),
        ('instructions', '설명', 270),
        ('training', '훈련장', 190),
    )
    COVER_FILE = 'title-cover.png'

    def __init__(self, width, height):
        self.width, self.height = width, height
        self.left = 72
        cover_path = Path(__file__).resolve().parents[1] / 'assets/backgrounds' / self.COVER_FILE
        self.cover = p.load_image(str(cover_path))
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
        white = (255, 255, 255)
        gold = (255, 210, 112)
        self.cover.draw(self.width / 2, self.height / 2, self.width, self.height)
        fill(0, 0, self.width, 2, white)
        fill(0, self.height - 2, self.width, 2, white)
        fill(0, 0, 2, self.height, white)
        fill(self.width - 2, 0, 2, self.height, white)
        self.title_font.draw(self.left, 539, '데미지 콜렉터', gold)
        self.font.draw(self.left + 2, 480, 'DAMAGE COLLECTOR', gold)
        self.draw_buttons()

    def draw_buttons(self):
        for _, label, bottom in self.BUTTONS:
            fill(self.left, bottom, 300, 58, (255, 255, 255))
            fill(self.left + 2, bottom + 2, 296, 54, (18, 25, 41))
            label_width = sum(26 if ord(char) > 127 else 8 for char in label)
            self.font.draw(self.left + (300 - label_width) / 2, bottom + 29, label, (255, 210, 112))
