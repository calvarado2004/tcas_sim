from __future__ import annotations
import math
from typing import Optional, List

from tcas_sim.enums import AdvisoryState, RAKind, RASense, TrackState, TCASMode
from tcas_sim.sensitivity.thresholds import SensitivityThresholds
from tcas_sim.tracking.track import Track
from tcas_sim.advisories.advisory import TrafficAdvisory, ResolutionAdvisory
from tcas_sim.core.aircraft import Aircraft


class AdvisoryEngine:
    """
    Converts Track states into TA/RA advisories.
    Implements:
      - TA issuance when any track is INTRUDER_TA or THREAT_RA
      - RA issuance when any track is THREAT_RA and RA is enabled
      - RA sense selection + strength (ALIM/non-crossing preference)
      - Weakening to LEVEL_OFF once ALIM achieved early (simple form)
    """
    def __init__(self):
        self.ta: Optional[TrafficAdvisory] = None
        self.ra: Optional[ResolutionAdvisory] = None
        self.primaryThreat: Optional[str] = None

    def update(
        self,
        now: float,
        ownship: Aircraft,
        tcas_mode: TCASMode,
        thresholds: SensitivityThresholds,
        tracks: List[Track],
    ) -> tuple[Optional[TrafficAdvisory], Optional[ResolutionAdvisory]]:
        intruders = [t for t in tracks if t.state in (TrackState.INTRUDER_TA, TrackState.THREAT_RA)]
        threats = [t for t in tracks if t.state == TrackState.THREAT_RA]

        # TA
        if intruders and self.ta is None:
            self.ta = TrafficAdvisory(issuedAt=now, state=AdvisoryState.ACTIVE)
        if not intruders:
            self.ta = None

        # RA disabled?
        if tcas_mode != TCASMode.TA_RA or thresholds.raTauSec is None or thresholds.alimFt is None:
            self.ra = None
            self.primaryThreat = None
            return self.ta, None

        if not threats:
            self.ra = None
            self.primaryThreat = None
            return self.ta, None

        primary = min(threats, key=lambda t: (t.rangeTauSec, t.rangeNm))
        self.primaryThreat = primary.intruder.callsign

        alim = thresholds.alimFt

        # Weakening example: if already have positive RA and ALIM already achieved now, go LEVEL_OFF
        if self.ra is not None and abs(primary.relativeAltitudeFt) >= alim:
            self.ra = ResolutionAdvisory(
                issuedAt=self.ra.issuedAt,
                state=AdvisoryState.WEAKENED,
                kind=RAKind.LEVEL_OFF,
                sense=RASense.NONE,
                requiredVerticalRateFpm=0,
                minAllowedVSFpm=-250,
                maxAllowedVSFpm=+250,
                alimFt=alim,
            )
            return self.ta, self.ra

        # Select new RA
        kind, sense, req_vs = self._select_ra(primary, ownship, alim)
        min_vs, max_vs = self._guidance_band(kind, req_vs)

        self.ra = ResolutionAdvisory(
            issuedAt=now,
            state=AdvisoryState.ACTIVE,
            kind=kind,
            sense=sense,
            requiredVerticalRateFpm=req_vs,
            minAllowedVSFpm=min_vs,
            maxAllowedVSFpm=max_vs,
            alimFt=alim,
        )
        return self.ta, self.ra

    def _select_ra(self, trk: Track, ownship: Aircraft, alim_ft: int) -> tuple[RAKind, RASense, int]:
        intr = trk.intruder
        t_cpa = min(trk.rangeTauSec if math.isfinite(trk.rangeTauSec) else 25.0, 45.0)
        t_cpa = max(1.0, t_cpa)

        strengths = [1500, 2500, 3500, 4400]

        def proj_sep_and_cross(own_vs: int) -> tuple[int, bool]:
            own_alt_cpa = ownship.altitudeFt + int(own_vs * (t_cpa / 60.0))
            intr_alt_cpa = intr.altitudeFt + int(intr.verticalRateFpm * (t_cpa / 60.0))
            sep = abs(own_alt_cpa - intr_alt_cpa)

            rel_now = intr.altitudeFt - ownship.altitudeFt
            rel_cpa = intr_alt_cpa - own_alt_cpa
            crossing = (rel_now == 0) or (rel_now * rel_cpa < 0)
            return sep, crossing

        best = None  # (achieves, non_crossing, disruption, sep, kind, sense, vs)

        for kind, sense, sign in (
            (RAKind.CLIMB, RASense.UPWARD, +1),
            (RAKind.DESCEND, RASense.DOWNWARD, -1),
        ):
            for mag in strengths:
                vs = sign * mag
                sep, crossing = proj_sep_and_cross(vs)
                achieves = sep >= alim_ft
                non_cross = not crossing
                disruption = abs(vs - ownship.verticalRateFpm)
                cand = (achieves, non_cross, disruption, sep, kind, sense, vs)

                if best is None:
                    best = cand
                else:
                    if cand[0] != best[0]:
                        if cand[0] and not best[0]:
                            best = cand
                    elif cand[1] != best[1]:
                        if cand[1] and not best[1]:
                            best = cand
                    elif cand[2] < best[2]:
                        best = cand
                    elif cand[2] == best[2] and cand[3] > best[3]:
                        best = cand

                if achieves and non_cross:
                    break

        assert best is not None
        _, _, _, _, kind, sense, vs = best
        return kind, sense, int(vs)

    def _guidance_band(self, kind: RAKind, req_vs: int) -> tuple[int, int]:
        # Simple banding: +/- 250 around target. For LEVEL_OFF constrain around 0.
        if kind == RAKind.LEVEL_OFF:
            return (-250, +250)
        return (req_vs - 250, req_vs + 250)
