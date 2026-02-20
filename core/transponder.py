from __future__ import annotations
from dataclasses import dataclass
from tcas_sim.enums import TransponderMode


@dataclass
class Transponder:
    mode: TransponderMode
    squawk: str
    altitudeReporting: bool
    modeSAddress: str
