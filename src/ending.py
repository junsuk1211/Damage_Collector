"""성기사 격파 후 표시하는 에필로그."""

try:
    from .selectscreen import SelectScreen, fade_to_black
except ImportError:
    from selectscreen import SelectScreen, fade_to_black


class EndingScreen(SelectScreen):
    COVER_FILE = 'cathedral-ending.png'
    BUTTONS = (('menu', '메인 화면', 190),)

    elapsed = 0.0

    def handle_event(self, event):
        if self.elapsed >= 2.6:
            return super().handle_event(event)
        return None

    def draw(self):
        self.cover.draw(self.width / 2, self.height / 2, self.width, self.height)
        if self.elapsed >= 0.65:
            self.title_font.draw(self.left, 515, '새벽의 정착지', (255, 223, 163))
        if self.elapsed >= 1.25:
            self.subtitle.draw(self.left, 438, '성기사를 쓰러뜨린 그는 밤이 걷히기 전에 성을 떠났다.', (240, 233, 215))
        if self.elapsed >= 2.0:
            self.subtitle.draw(self.left, 398, '먼 산 아래 작은 마을에서 그는 새 삶을 시작했다.', (240, 233, 215))
        if self.elapsed >= 2.6:
            self.draw_buttons()
        fade_to_black(1 - self.elapsed / 0.65)
