"""중갑병의 기본 전투 데이터."""

from dataclasses import dataclass

try:
    from .trainingcenter import Dummy
except ImportError:
    from trainingcenter import Dummy


@dataclass
class Verysheidman(Dummy):
    hp: int = 18
