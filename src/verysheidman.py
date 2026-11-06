"""중갑병의 기본 전투 데이터."""

from dataclasses import dataclass

try:
    from .trainingcenter import Dummy
except ImportError:
    from trainingcenter import Dummy


@dataclass
class Verysheidman(Dummy):
    MAX_HP = 18
    hp: int = MAX_HP
