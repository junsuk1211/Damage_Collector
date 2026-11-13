"""챕터 사이에 고르는 강화 카드와 효과."""

from random import choice, choices

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


CARD_SYMBOLS = {
    'heal': '+', 'blade': '/', 'straight': '→', 'multiply': '×',
    'embers': '✦', 'reach': 'C', 'shield': '◆', 'refund': '1',
}

RARITIES = (
    ('일반', 60, (190, 200, 215), ('reach', 'refund', 'straight')),
    ('희귀', 30, (111, 174, 255), ('blade', 'embers', 'multiply')),
    ('전설', 10, (255, 207, 109), ('heal', 'shield')),
)
CARD_RARITY = {key: (label, color) for label, _, color, keys in RARITIES for key in keys}


def draw_card(eligible):
    groups, weights = [], []
    for _, weight, _, keys in RARITIES:
        available = [key for key in keys if key in eligible]
        if available:
            groups.append(available)
            weights.append(weight)
    return choice(choices(groups, weights=weights)[0])


class UpgradeScreen:
    def __init__(self, height, health, max_health, used=()):
        self.height = height
        self.health = health
        self.max_health = max_health
        self.pool = [key for key in CARDS if key not in used and (key != 'blade' or health > 2)]
        remaining = self.pool.copy()
        self.cards = []
        for _ in range(min(2, len(remaining))):
            key = draw_card(remaining)
            self.cards.append(key)
            remaining.remove(key)
        self.focus = 0
        self.rerolls = [True] * len(self.cards)
        self.seen = set(self.cards)
        self.title = korean_font(36)
        self.font = korean_font(22)
        self.small = korean_font(18)

    def handle_event(self, event):
        if event.type != p.SDL_KEYDOWN or getattr(event, 'repeat', False):
            return False
        if event.key == p.SDLK_LEFT:
            self.focus = 0
        elif event.key == p.SDLK_RIGHT and self.cards:
            self.focus = len(self.cards) - 1
        elif event.key == p.SDLK_r and self.cards and self.rerolls[self.focus]:
            pool = [key for key in self.pool if key not in self.seen]
            if pool:
                self.cards[self.focus] = draw_card(pool)
                self.seen.add(self.cards[self.focus])
                self.rerolls[self.focus] = False
        return event.key in (p.SDLK_RETURN, p.SDLK_KP_ENTER)

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
        self.font.draw(150, 550, f'현재 체력 {self.health}/{self.max_health}   ·   ← → 카드 이동   ·   표시된 강화 모두 적용', white)
        for index, key in enumerate(self.cards):
            left = (150, 660)[index]
            title, detail = CARDS[key]
            rarity, accent = CARD_RARITY[key]
            if index == self.focus:
                fill(left - 5, 230, 480, 265, (224, 238, 255))
            fill(left, 235, 470, 255, accent)
            fill(left + 2, 237, 466, 251, (30, 40, 59))
            self.title.draw(left + 398, 434, CARD_SYMBOLS[key], accent)
            self.title.draw(left + 25, 425, title, gold)
            self.small.draw(left + 25, 455, rarity, accent)
            self.small.draw(left + 25, 365, detail, white)
            enabled = self.rerolls[index] and len(self.seen) < len(self.pool)
            fill(left + 25, 254, 180, 50, (55, 81, 108) if enabled else (48, 53, 66))
            self.small.draw(left + 45, 279, 'R  리롤 1회' if enabled else '리롤 불가', white)
        if not self.cards:
            self.font.draw(150, 420, '남은 증강이 없습니다.', white)
        fill(495, 136, 290, 58, gold)
        self.font.draw(537, 165, 'Enter  확정', (18, 22, 32))
        self.small.draw(150, 85, '전투 강화는 다음 챕터 동안 적용됩니다.', white)
        self.small.draw(150, 55, '피의 단검은 현재 체력이 3 이상일 때 등장하며, 완전 회복보다 나중에 적용됩니다.', white)
