from __future__ import annotations
from dataclasses import dataclass
from tcas_sim.enums import AdvisoryState, RAKind, RASense


@dataclass
class Advisory:
    issuedAt: float
    state: AdvisoryState


@dataclass
class TrafficAdvisory(Advisory):
    pass


@dataclass
class ResolutionAdvisory(Advisory):
    kind: RAKind
    sense: RASense

    requiredVerticalRateFpm: int
    minAllowedVSFpm: int
    maxAllowedVSFpm: int

    alimFt: int
