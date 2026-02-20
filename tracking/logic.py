from __future__ import annotations
import math
from typing import Dict, List, Tuple

from tcas_sim.core.aircraft import Aircraft
from tcas_sim.core.transponder import Transponder
from tcas_sim.enums import TrackState, SensitivityLevel, TCASMode
from tcas_sim.sensitivity.thresholds import SensitivityThresholds
from tcas_sim.tracking.track import Track


def compute_sl_from_altitude_ft(alt_ft: int) -> SensitivityLevel:
    if alt_ft < 1000:
        return SensitivityLevel.SL2
    if alt_ft < 2350:
        return SensitivityLevel.SL3
    if alt_ft < 5000:
        return SensitivityLevel.SL4
    if alt_ft < 10000:
        return SensitivityLevel.SL5
    if alt_ft < 20000:
        return SensitivityLevel.SL6
    return SensitivityLevel.SL7


def modified_tau_trigger(range_nm: float, closure_kts: float, tau_thresh_s: int, dmod_nm: float) -> bool:
    if range_nm <= dmod_nm:
        return True
    if closure_kts <= 1e-6:
        return False
    tau = (range_nm / closure_kts) * 3600.0
    return tau <= float(tau_thresh_s)


def vertical_trigger(rel_alt_ft: int, v_closure_fpm: int, tau_thresh_s: int, zthr_ft: int) -> bool:
    if abs(rel_alt_ft) <= zthr_ft:
        return True
    if v_closure_fpm <= 0:
        return False
    v_tau = (abs(rel_alt_ft) / v_closure_fpm) * 60.0
    return v_tau <= float(tau_thresh_s)


class Tracker:
    """
    Creates/updates Track objects from ownship + intruders.
    Keeps minimal memory for range-rate computation.
    """
    def __init__(self):
        self._prev_range: Dict[str, Tuple[float, float]] = {}

    def update(
        self,
        now: float,
        ownship: Aircraft,
        intruders: List[Aircraft],
        intruder_xpdrs: Dict[str, Transponder],
        tcas_mode: TCASMode,
        thresholds: SensitivityThresholds,
    ) -> Dict[str, Track]:
        tracks: Dict[str, Track] = {}

        for ac in intruders:
            dx = ac.x_nm - ownship.x_nm
            dy = ac.y_nm - ownship.y_nm
            rng = math.hypot(dx, dy)

            bearing = (math.degrees(math.atan2(dx, dy)) + 360.0) % 360.0
            rel_alt = ac.altitudeFt - ownship.altitudeFt

            prev = self._prev_range.get(ac.callsign)
            if prev is None:
                range_rate_kts = 0.0
            else:
                prev_rng, prev_t = prev
                dt = max(1e-3, now - prev_t)
                range_rate_kts = ((rng - prev_rng) / dt) * 3600.0

            self._prev_range[ac.callsign] = (rng, now)
            closure_kts = max(0.0, -range_rate_kts)

            # vertical closure (only if altitude separation reducing)
            v_closure_signed = ownship.verticalRateFpm - ac.verticalRateFpm
            v_closure_mag = abs(v_closure_signed) if (rel_alt * v_closure_signed < 0) else 0

            range_tau = (rng / closure_kts) * 3600.0 if closure_kts > 1e-6 else float("inf")
            vert_tau = (abs(rel_alt) / v_closure_mag) * 60.0 if v_closure_mag > 0 else float("inf")

            xpdr = intruder_xpdrs.get(ac.callsign)
            altitude_reporting = bool(xpdr.altitudeReporting) if xpdr else True

            # classification (TA/RA gates use thresholds; RA also depends on mode + altitude reporting)
            prox = (rng <= 6.0 and abs(rel_alt) <= 1200)

            ta_ok = modified_tau_trigger(rng, closure_kts, thresholds.taTauSec, thresholds.taDMODNm) and \
                    vertical_trigger(rel_alt, v_closure_mag, thresholds.taTauSec, thresholds.taZTHRFt)

            ra_ok = False
            if tcas_mode == TCASMode.TA_RA and thresholds.raTauSec is not None and thresholds.raDMODNm is not None and thresholds.raZTHRFt is not None:
                ra_ok = altitude_reporting and \
                        modified_tau_trigger(rng, closure_kts, thresholds.raTauSec, thresholds.raDMODNm) and \
                        vertical_trigger(rel_alt, v_closure_mag, thresholds.raTauSec, thresholds.raZTHRFt)

            if ra_ok:
                state = TrackState.THREAT_RA
                ttc = int(min(range_tau, vert_tau)) if math.isfinite(range_tau) or math.isfinite(vert_tau) else 999
            elif ta_ok:
                state = TrackState.INTRUDER_TA
                ttc = int(min(range_tau, vert_tau)) if math.isfinite(range_tau) or math.isfinite(vert_tau) else 999
            elif prox:
                state = TrackState.PROXIMATE
                ttc = 999
            else:
                state = TrackState.OTHER
                ttc = 999

            tracks[ac.callsign] = Track(
                intruder=ac,
                bearingDeg=bearing,
                rangeNm=rng,
                relativeAltitudeFt=rel_alt,
                rangeRateKts=range_rate_kts,
                closureRateKts=closure_kts,
                intruderVerticalRateFpm=ac.verticalRateFpm,
                verticalClosureFpm=v_closure_mag,
                rangeTauSec=range_tau,
                verticalTauSec=vert_tau,
                isAltitudeReporting=altitude_reporting,
                state=state,
                timeToConflictSec=ttc,
                lastUpdateAt=now,
            )

        return tracks
