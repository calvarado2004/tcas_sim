from __future__ import annotations
from dataclasses import dataclass
from typing import Dict

from tcas_sim.enums import SensitivityLevel


@dataclass(frozen=True)
class SensitivityThresholds:
    sl: SensitivityLevel
    taTauSec: int
    raTauSec: int | None
    taDMODNm: float
    raDMODNm: float | None
    taZTHRFt: int
    raZTHRFt: int | None
    alimFt: int | None


@dataclass
class SensitivityProfile:
    thresholds: Dict[SensitivityLevel, SensitivityThresholds]

    @staticmethod
    def default_v71() -> "SensitivityProfile":
        t = {
            SensitivityLevel.SL2: SensitivityThresholds(SensitivityLevel.SL2, 20, None, 0.30, None, 850, None, None),
            SensitivityLevel.SL3: SensitivityThresholds(SensitivityLevel.SL3, 25, 15,   0.33, 0.20, 850, 600, 300),
            SensitivityLevel.SL4: SensitivityThresholds(SensitivityLevel.SL4, 30, 20,   0.48, 0.35, 850, 600, 300),
            SensitivityLevel.SL5: SensitivityThresholds(SensitivityLevel.SL5, 40, 25,   0.75, 0.55, 850, 600, 350),
            SensitivityLevel.SL6: SensitivityThresholds(SensitivityLevel.SL6, 45, 30,   1.00, 0.80, 850, 600, 400),
            SensitivityLevel.SL7: SensitivityThresholds(SensitivityLevel.SL7, 48, 35,   1.30, 1.10, 850, 700, 600),
        }
        return SensitivityProfile(thresholds=t)
