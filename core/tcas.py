from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional, Dict, List

from tcas_sim.enums import TCASVersion, TCASMode, SensitivityLevel
from tcas_sim.core.aircraft import Aircraft
from tcas_sim.sensitivity.thresholds import SensitivityProfile, SensitivityThresholds
from tcas_sim.tracking.track import Track
from tcas_sim.advisories.advisory import Advisory


@dataclass
class TCAS:
    version: TCASVersion
    mode: TCASMode

    ownship: Aircraft
    sensitivityProfile: SensitivityProfile

    currentSL: SensitivityLevel = SensitivityLevel.SL6
    activeThresholds: SensitivityThresholds = field(init=False)

    tracks: Dict[str, Track] = field(default_factory=dict)
    advisories: List[Advisory] = field(default_factory=list)

    def __post_init__(self) -> None:
        self.activeThresholds = self.sensitivityProfile.thresholds[self.currentSL]

    def set_sl(self, sl: SensitivityLevel) -> None:
        self.currentSL = sl
        self.activeThresholds = self.sensitivityProfile.thresholds[sl]
