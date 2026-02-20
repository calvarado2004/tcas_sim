from __future__ import annotations
from dataclasses import dataclass
from typing import List

from tcas_sim.enums import VerticalTrend, ThreatLevel, DisplayColor, SymbolType


@dataclass
class CockpitAuralAlert:
    message: str


@dataclass
class Display:
    pass


@dataclass
class TrafficDisplay(Display):
    selectedRangeNm: float


@dataclass
class RADisplay(Display):
    scaleMaxVSFpm: int = 3000


@dataclass
class DisplayEntry:
    relativeAltitudeFt: int
    verticalTrend: VerticalTrend
    threatLevel: ThreatLevel
    color: DisplayColor
    symbolType: SymbolType
