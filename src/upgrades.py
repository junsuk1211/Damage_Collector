"""챕터 사이에 고르는 강화 카드와 효과."""

from random import sample, choice

import pico2d as p

try:
    from .selectscreen import fill, korean_font
except ImportError:
    from selectscreen import fill, korean_font


CARDS = {
    'heal': ('완전 회복', '체력을 최대치까지 회복합니다.'),
    'blade': ('피의 단검', '체력 2를 내고 단검 피해를 3으로 고정합니다.'),
    'straight': ('직선 투척', '숫자를 바라보는 방향으로 곧게 던집니다.'),
    'multiply': ('곱셈 보관함', '두 개만 보관하고, 투척할 때 서로 곱합니다.'),
    'embers': ('잔불 폭발', '1초간 남는 잔불이 뒤늦게 들어온 적에게 피해 1을 줍니다.'),
    'reach': ('빠른 손', '숫자 회수 범위가 50% 늘어납니다.'),
    'shield': ('깨지는 방패', '첫 피격 때 보관한 숫자를 지킵니다.'),
    'refund': ('되돌아온 숫자', '투척이 빗나가면 폭발 지점에 1이 떨어집니다.'),
}


class UpgradeScreen:
    def __init__(self, height, health, max_health):
        self.height = height
        self.health = health
        self.max_health = max_health
        pool = [key for key in CARDS if key != 'blade' or health > 2]
        self.cards = sample(pool, 2)
        self.rerolls = [True, True]
        self.seen = set(self.cards)
        self.title = korean_font(36)
        self.font = korean_font(22)
        self.small = korean_font(18)

    def handle_event(self, event):
        if event.type != p.SDL_MOUSEBUTTONDOWN or event.button != 1:
            return False
        x, y = event.x, self.height - 1 - event.y
        for index, left in enumerate((150, 660)):
            if left + 25 <= x < left + 205 and 254 <= y < 304 and self.rerolls[index]:
                pool = [key for key in CARDS if key not in self.seen
                        and (key != 'blade' or self.health > 2)]
                self.cards[index] = choice(pool)
                self.seen.add(self.cards[index])
                self.rerolls[index] = False
        return 495 <= x < 785 and 136 <= y < 194

    def apply(self, stage):
        stage.upgrades = set(self.cards)
        stage.health = stage.MAX_HEALTH if 'heal' in self.cards else self.health
        if 'blade' in self.cards:
            stage.health -= 2

    def draw(self):
        gold = (244, 207, 141)
        white = (224, 233, 242)
        fill(0, 0, 1280, self.height, (14, 20, 34))
        self.title.draw(150, 605, '다음 스테이지 강화', gold)
        self.font.draw(150, 550, f'현재 체력 {self.health}/{self.max_health}   ·   두 카드 모두 적용', white)
        for index, left in enumerate((150, 660)):
            key = self.cards[index]
            title, detail = CARDS[key]
            fill(left, 235, 470, 255, gold)
            fill(left + 2, 237, 466, 251, (30, 40, 59))
            self.title.draw(left + 25, 425, title, gold)
            self.small.draw(left + 25, 365, detail, white)
            enabled = self.rerolls[index]
            fill(left + 25, 254, 180, 50, (55, 81, 108) if enabled else (48, 53, 66))
            self.small.draw(left + 45, 279, '리롤 1회' if enabled else '리롤 사용함', white)
        fill(495, 136, 290, 58, gold)
        self.font.draw(537, 165, '확정하고 계속', (18, 22, 32))
        self.small.draw(150, 85, '전투 강화는 다음 챕터 동안 적용됩니다.', white)
        self.small.draw(150, 55, '피의 단검은 현재 체력이 3 이상일 때 등장하며, 완전 회복보다 나중에 적용됩니다.', white)
