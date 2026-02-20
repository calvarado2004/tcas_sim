from __future__ import annotations
from enum import Enum, auto


class TCASVersion(Enum):
    V6_04A = auto()
    V7_0 = auto()
    V7_1 = auto()


class TCASMode(Enum):
    STANDBY = auto()
    TA_ONLY = auto()
    TA_RA = auto()


class TransponderMode(Enum):
    MODE_A = auto()
    MODE_C = auto()
    MODE_S = auto()


class SensitivityLevel(Enum):
    SL2 = 2
    SL3 = 3
    SL4 = 4
    SL5 = 5
    SL6 = 6
    SL7 = 7


class TrackState(Enum):
    OTHER = auto()
    PROXIMATE = auto()
    INTRUDER_TA = auto()
    THREAT_RA = auto()


class AdvisoryState(Enum):
    PENDING = auto()
    ACTIVE = auto()
    WEAKENED = auto()
    STRENGTHENED = auto()
    REVERSED = auto()
    TERMINATED = auto()


class RASense(Enum):
    UPWARD = auto()
    DOWNWARD = auto()
    NONE = auto()


class RAKind(Enum):
    CLIMB = auto()
    DESCEND = auto()
    LEVEL_OFF = auto()
    DO_NOT_CLIMB = auto()
    DO_NOT_DESCEND = auto()
    INCREASE_CLIMB = auto()
    INCREASE_DESCEND = auto()
    MAINTAIN_VERTICAL_SPEED = auto()
    CROSSING_CLIMB = auto()
    CROSSING_DESCEND = auto()
    CROSSING_MAINTAIN = auto()


class VerticalTrend(Enum):
    CLIMBING = auto()
    DESCENDING = auto()
    LEVEL = auto()


class ThreatLevel(Enum):
    NON_THREAT = auto()
    PROXIMITY = auto()
    TRAFFIC_ADVISORY = auto()
    RESOLUTION_ADVISORY = auto()


class DisplayColor(Enum):
    WHITE = auto()
    CYAN = auto()
    YELLOW = auto()
    RED = auto()


class SymbolType(Enum):
    DIAMOND = auto()
    CIRCLE = auto()
    SQUARE = auto()


class CoordinationStatus(Enum):
    INITIATED = auto()
    INTENT_EXCHANGED = auto()
    ACTIVE = auto()
    COMPLETED = auto()
    ABORTED = auto()
