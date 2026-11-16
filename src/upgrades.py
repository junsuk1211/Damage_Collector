"""챕터 사이에 고르는 강화 카드와 효과."""

from math import cos, sin, tau
from random import choice, choices
from time import perf_counter

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
    'linger': ('잔류 숫자', '바닥에 떨어진 숫자가 3초 더 남습니다.'),
    'recover': ('역전 회수', '피격으로 잃은 숫자 중 가장 큰 1개를 떨어뜨립니다.'),
    'quick_throw': ('속전속결', '숫자 2개를 던지면 쿨타임이 1.5초입니다.'),
    'sequence': ('순서의 법칙', '1 → 2 → 3 순서로 모아 던지면 피해가 9입니다.'),
}

CARD_ICONS = {
    'heal': ('.......', '.##.##.', '#######', '#######', '.#####.', '..###..', '...#...'),
    'blade': ('.....##', '....###', '...###.', '..###..', '#.##...', '.##....', '#..#...'),
    'straight': ('.......', '....#..', '.....#.', '#######', '.....#.', '....#..', '.......'),
    'multiply': ('.......', '.#...#.', '..#.#..', '...#...', '..#.#..', '.#...#.', '.......'),
    'embers': ('...#...', '...##..', '..###..', '.####.#', '.######', '.#####.', '..###..'),
    'reach': ('..#....', '..##.#.', '.#####.', '#######', '#######', '.#####.', '..###..'),
    'shield': ('#######', '#..#..#', '#..#..#', '#.##..#', '.#.#.#.', '..#.#..', '...#...'),
    'refund': ('..####.', '.#....#', '#..#...', '#.##...', '#..#..#', '.#.#.#.', '..####.'),
    'linger': ('.#####.', '..###..', '...#...', '...#...', '..#.#..', '.#####.', '.#####.'),
    'recover': ('...#...', '..###..', '.#####.', '...#...', '#..#..#', '#.....#', '.#####.'),
    'quick_throw': ('....##.', '...##..', '..####.', '.####..', '...#...', '..#....', '.#.....'),
    'sequence': ('......#', '.....##', '....###', '..##...', '..##...', '#......', '#######'),
}

INCOMPATIBLE = {'multiply': 'sequence', 'sequence': 'multiply'}

RARITIES = (
    ('일반', 60, (190, 200, 215), ('reach', 'refund', 'straight', 'linger')),
    ('희귀', 30, (111, 174, 255), ('blade', 'embers', 'multiply', 'recover', 'quick_throw')),
    ('전설', 10, (255, 207, 109), ('heal', 'shield', 'sequence')),
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
    REVEAL_TIME = 0.72

    def __init__(self, height, health, max_health, used=()):
        self.height = height
        self.health = health
        self.max_health = max_health
        self.pool = [key for key in CARDS if key not in used and (key != 'blade' or health > 2)]
        self.cards = []
        for _ in range(2):
            eligible = [key for key in self.pool
                        if key not in self.cards and INCOMPATIBLE.get(key) not in self.cards]
            if eligible:
                self.cards.append(draw_card(eligible))
        self.focus = 0
        self.rerolls = [True] * len(self.cards)
        self.seen = set(self.cards)
        self.reroll_started = [None] * len(self.cards)
        self.title = korean_font(36)
        self.font = korean_font(22)
        self.small = korean_font(18)

    def reroll_pool(self, index):
        others = self.cards[:index] + self.cards[index + 1:]
        return [key for key in self.pool
                if key not in self.seen and INCOMPATIBLE.get(key) not in others]

    def handle_event(self, event):
        if event.type != p.SDL_KEYDOWN or getattr(event, 'repeat', False):
            return False
        if event.key == p.SDLK_LEFT:
            self.focus = 0
        elif event.key == p.SDLK_RIGHT and self.cards:
            self.focus = len(self.cards) - 1
        elif event.key == p.SDLK_r and self.cards and self.rerolls[self.focus]:
            pool = self.reroll_pool(self.focus)
            if pool:
                self.cards[self.focus] = draw_card(pool)
                self.seen.add(self.cards[self.focus])
                self.rerolls[self.focus] = False
                self.reroll_started[self.focus] = perf_counter()
        return event.key in (p.SDLK_RETURN, p.SDLK_KP_ENTER) and not self.is_revealing()

    def is_revealing(self):
        now = perf_counter()
        return any(start is not None and now - start < self.REVEAL_TIME
                   for start in self.reroll_started)

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
            fill(left + 5, 227, 470, 255, (8, 12, 22))
            fill(left, 235, 470, 255, accent)
            fill(left + 2, 237, 466, 251, (25, 32, 49))
            fill(left + 11, 382, 448, 95, (34, 43, 64))
            fill(left + 25, 398, 415, 1, accent)
            for corner in (left + 9, left + 450):
                fill(corner, 475, 11, 4, accent)
                fill(corner + 3, 469, 5, 8, accent)
            for row in range(-28, 29, 2):
                span = 28 - abs(row)
                fill(left + 410 - span, 434 + row, span * 2 + 1, 2, (56, 64, 84))
            self.draw_card_icon(left + 410, 434, key, accent)
            self.title.draw(left + 25, 425, title, gold)
            self.small.draw(left + 25, 455, rarity, accent)
            self.small.draw(left + 25, 365, detail, white)
            enabled = self.rerolls[index] and bool(self.reroll_pool(index))
            fill(left + 25, 254, 180, 50, (55, 81, 108) if enabled else (48, 53, 66))
            self.small.draw(left + 45, 279, 'R  리롤 1회' if enabled else '리롤 불가', white)
            start = self.reroll_started[index]
            if start is not None:
                progress = (perf_counter() - start) / self.REVEAL_TIME
                if progress < 1:
                    self.draw_reveal(left, progress, accent)
        if not self.cards:
            self.font.draw(150, 420, '남은 증강이 없습니다.', white)
        fill(495, 136, 290, 58, (133, 117, 95) if self.is_revealing() else gold)
        self.font.draw(537, 165, 'Enter  확정', (18, 22, 32))
        self.small.draw(150, 85, '전투 강화는 다음 챕터 동안 적용됩니다.', white)
        self.small.draw(150, 55, '피의 단검은 현재 체력이 3 이상일 때 등장하며, 완전 회복보다 나중에 적용됩니다.', white)

    @staticmethod
    def draw_card_icon(x, y, key, accent):
        for row, line in enumerate(CARD_ICONS[key]):
            for column, pixel in enumerate(line):
                if pixel == '#':
                    dx, dy = x - 14 + column * 4, y + 10 - row * 4
                    fill(dx, dy - 2, 4, 4, (17, 23, 38))
                    fill(dx, dy, 4, 4, accent)
                    fill(dx, dy + 3, 4, 1, (228, 244, 255))

    @staticmethod
    def draw_reveal(left, progress, accent):
        center_x, center_y = left + 235, 363
        fade = 1 - progress
        glow = tuple(int(channel * fade) for channel in accent)
        gold = (255, 216, 145)
        if progress < 0.22:
            shine = 1 - progress / 0.22
            span = 25 + 65 * shine
            fill(center_x - span, center_y - 2, span * 2, 4, gold)
            fill(center_x - 3, center_y - span / 2, 6, span, (255, 248, 226))
        for ring in range(2):
            spread = max(0, progress - ring * 0.14)
            if not spread:
                continue
            expansion = 1 - (1 - spread) ** 2
            for index in range(40):
                angle = index * tau / 40 + ring * 0.08
                x = center_x + cos(angle) * (20 + 202 * expansion)
                y = center_y + sin(angle) * (12 + 106 * expansion)
                size = 2 + int(4 * fade)
                fill(x, y, size, size, glow)
        for index in range(24):
            angle = index * tau / 24 + 0.1
            dx, dy = cos(angle), sin(angle)
            reach = 95 + 22 * (index % 5)
            x = center_x + dx * reach * progress
            y = center_y + dy * reach * 0.65 * progress - 26 * progress ** 2
            for trail in (12, 6, 0):
                size = max(1, int((6 - trail / 3) * fade))
                color = gold if not trail and progress < 0.8 else glow
                fill(x - dx * trail, y - dy * trail, size, size, color)
