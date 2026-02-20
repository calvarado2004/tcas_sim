from __future__ import annotations
from dataclasses import dataclass


@dataclass
class Aircraft:
    callsign: str
    altitudeFt: int
    verticalRateFpm: int
    groundSpeedKt: float
    headingDeg: float

    # Simulation state (not part of UML attributes, but needed for movement)
    x_nm: float = 0.0
    y_nm: float = 0.0

    # Demo "autopilot bug" (not in UML; simulator convenience)
    targetAltitudeFt: int = 0
