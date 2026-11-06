"""지하 책방에서 펼쳐 보는 조작 안내서."""

import pico2d

try:
    from .selectscreen import korean_font
except ImportError:
    from selectscreen import korean_font


class Manual:
    def __init__(self, background_path):
        self.background = pico2d.load_image(str(background_path))
        self.heading = korean_font(27)
        self.body = korean_font(19)

    def draw(self, width, height):
        self.background.draw(width / 2, height / 2, width, height)
        self.draw_page(308, '기본 조작', (
            '← / →   좌우 이동',
            '↑   점프',
            '왼쪽 Shift   구르기',
            'X   단검 공격',
            'Esc   시작 화면으로',
        ))
        self.draw_page(675, '숫자 다루기', (
            'I   훈련장 허수아비 생성',
            'X로 때려 숫자를 떨어뜨린다.',
            'C로 가까운 숫자를 줍는다.',
            'V를 누른 채 착지점을 조준한다.',
            'V를 놓으면 모은 합계를 던진다.',
            '폭발 범위 안의 표적에 피해를 준다.',
        ))

    def draw_page(self, x, title, lines):
        self.heading.draw(x, 493, title, (95, 48, 25))
        for index, line in enumerate(lines):
            self.body.draw(x, 446 - index * 37, line, (53, 36, 24))
