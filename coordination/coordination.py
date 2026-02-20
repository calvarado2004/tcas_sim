from __future__ import annotations
from dataclasses import dataclass
from tcas_sim.enums import CoordinationStatus, RAKind, RASense


@dataclass
class ResolutionPair:
    ownshipKind: RAKind
    intruderKind: RAKind
    ownshipSense: RASense
    intruderSense: RASense


@dataclass
class CoordinationSession:
    startedAt: float
    status: CoordinationStatus
    resolutionPair: ResolutionPair
