"""석궁병의 기본 전투 데이터."""

from dataclasses import dataclass

try:
    from .trainingcenter import Dummy
except ImportError:
    from trainingcenter import Dummy


@dataclass
class Arrowman(Dummy):
    MAX_HP = 9
    hp: int = MAX_HP
