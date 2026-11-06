"""패배 배경과 다시 플레이하기 메뉴."""

try:
    from .selectscreen import SelectScreen
except ImportError:
    from selectscreen import SelectScreen


class GameOverScreen(SelectScreen):
    COVER_FILE = 'chapter1-defeat.png'
    BUTTONS = (
        ('chapter1', '다시 플레이하기', 350),
        ('menu', '메인 화면', 270),
    )

    def draw(self):
        self.cover.draw(self.width / 2, self.height / 2, self.width, self.height)
        self.title_font.draw(self.left, 490, '전투 패배', (255, 210, 112))
        self.draw_buttons()
