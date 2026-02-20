from __future__ import annotations
from dataclasses import dataclass
from tcas_sim.enums import TrackState
from tcas_sim.core.aircraft import Aircraft


@dataclass
class Track:
    intruder: Aircraft

    bearingDeg: float
    rangeNm: float
    relativeAltitudeFt: int

    rangeRateKts: float
    closureRateKts: float

    intruderVerticalRateFpm: int
    verticalClosureFpm: int

    rangeTauSec: float
    verticalTauSec: float

    isAltitudeReporting: bool
    state: TrackState

    timeToConflictSec: int
    lastUpdateAt: float
