from __future__ import annotations
from dataclasses import dataclass
from tcas_sim.enums import SensitivityLevel
from tcas_sim.sensitivity.thresholds import SensitivityThresholds


@dataclass
class ProtectionZone:
    minTimeToConflictSec: int
    maxTimeToConflictSec: int


@dataclass
class CautionZone(ProtectionZone):
    pass


@dataclass
class WarningZone(ProtectionZone):
    pass


@dataclass
class CollisionZone(ProtectionZone):
    pass


@dataclass
class AirspaceVolume:
    sl: SensitivityLevel
    usesThresholds: SensitivityThresholds

    cautionZone: CautionZone
    warningZone: WarningZone
    collisionZone: CollisionZone

    @staticmethod
    def from_thresholds(sl: SensitivityLevel, th: SensitivityThresholds) -> "AirspaceVolume":
        # For demo/spec: TA ~ 20–48 sec, RA ~ 15–35 sec, collision ~ < 15 sec (coarse bands)
        cz = CautionZone(minTimeToConflictSec=20, maxTimeToConflictSec=48)
        wz = WarningZone(minTimeToConflictSec=15, maxTimeToConflictSec=35)
        col = CollisionZone(minTimeToConflictSec=0, maxTimeToConflictSec=15)
        return AirspaceVolume(sl=sl, usesThresholds=th, cautionZone=cz, warningZone=wz, collisionZone=col)
