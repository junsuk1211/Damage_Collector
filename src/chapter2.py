"""챕터 2의 전투와 지형 배치."""

try:
    from .chapter1 import ChapterOne
except ImportError:
    from chapter1 import ChapterOne


class ChapterTwo(ChapterOne):
    TITLE = '챕터 2  |  성 안쪽 통로'
    NEXT_STAGE = None
    GUARD_POSITIONS = (850, 1320, 2140)
    STONE_PLATFORMS = ((580, 705, 194), (1810, 1930, 193))
    SCAFFOLDS = ((765, 980, 224), (1560, 1750, 220))
    BOXES = ((465, 524, 182), (1420, 1505, 204))
    FIRE_VENTS = ((1065, 1.0), (1980, 2.0), (2280, 2.8))
