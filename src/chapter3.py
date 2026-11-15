"""증강을 적용해 진입할 수 있는 성 내부 후속 구간."""

try:
    from .chapter1 import ChapterOne
except ImportError:
    from chapter1 import ChapterOne


class ChapterThree(ChapterOne):
    TITLE = '챕터 3  |  성 내부 초소'
    NEXT_STAGE = None
    ARROW_PLATFORM = None
    GUARD_POSITIONS = (820, 1400, 2080)
    STONE_PLATFORMS = ((530, 630, 181), (1740, 1840, 196))
    SCAFFOLDS = ((1050, 1250, 211),)
    FIRE_VENTS = ((960, 1.1), (1910, 2.2))
