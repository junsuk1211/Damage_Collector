"""석궁병의 기본 전투 데이터."""

from dataclasses import dataclass

try:
    from .trainingcenter import Dummy
except ImportError:
    from trainingcenter import Dummy


@dataclass
class Arrowman(Dummy):
    hp: int = 9
