from __future__ import annotations
import math
import random
import time
from typing import Dict, List

from tcas_sim.core.aircraft import Aircraft
from tcas_sim.core.transponder import Transponder
from tcas_sim.core.tcas import TCAS
from tcas_sim.enums import (
    TCASVersion, TCASMode, TransponderMode, DisplayColor, SymbolType,
    ThreatLevel, VerticalTrend, TrackState, RAKind
)
from tcas_sim.sensitivity.thresholds import SensitivityProfile
from tcas_sim.tracking.logic import Tracker, compute_sl_from_altitude_ft
from tcas_sim.advisories.logic import AdvisoryEngine
from tcas_sim.zones.airspace import AirspaceVolume
from tcas_sim.cockpit.outputs import DisplayEntry


class Simulator:
    def __init__(
        self,
        time_scale: float = 1.5,
        max_intruders: int = 10,
        threat_spawn_prob: float = 0.30,
    ):
        self.time_scale = float(time_scale)
        self.max_intruders = int(max_intruders)
        self.threat_spawn_prob = float(threat_spawn_prob)

        self.ownship = Aircraft("OWN", 12000, 0, 250.0, 0.0, 0.0, 0.0, 12000)

        self.profile = SensitivityProfile.default_v71()
        self.tcas = TCAS(
            version=TCASVersion.V7_1,
            mode=TCASMode.TA_RA,
            ownship=self.ownship,
            sensitivityProfile=self.profile,
        )

        self.protectedVolume = AirspaceVolume.from_thresholds(self.tcas.currentSL, self.tcas.activeThresholds)

        self.intruders: List[Aircraft] = []
        self.intruder_xpdrs: Dict[str, Transponder] = {}

        self.tracker = Tracker()
        self.advisory_engine = AdvisoryEngine()

        self.last_spawn = time.time()

        # autopilot demo mode (not UML)
        self.ap_mode = "ALT"  # ALT or RA
        self.cmd_vs_fpm = 0

        # banner text (not UML)
        self.banner_text = ""
        self.banner_until = 0.0

    def set_banner(self, text: str, duration_s: float = 4.0):
        self.banner_text = text
        self.banner_until = time.time() + duration_s

    def banner(self) -> str:
        return self.banner_text if self.banner_text and time.time() <= self.banner_until else ""

    def step(self, dt_real: float):
        now = time.time()
        dt = dt_real * self.time_scale

        # SL update from altitude
        sl = compute_sl_from_altitude_ft(self.ownship.altitudeFt)
        if sl != self.tcas.currentSL:
            self.tcas.set_sl(sl)
            self.protectedVolume = AirspaceVolume.from_thresholds(sl, self.tcas.activeThresholds)

        # spawn intruders
        if now - self.last_spawn > random.uniform(1.6, 3.2) and len(self.intruders) < self.max_intruders:
            self.last_spawn = now
            ac, xpdr = self._spawn_intruder()
            self.intruders.append(ac)
            self.intruder_xpdrs[ac.callsign] = xpdr

        # move intruders
        for ac in self.intruders:
            spd_nmps = ac.groundSpeedKt / 3600.0
            hdg = math.radians(ac.headingDeg)
            ac.x_nm += math.sin(hdg) * spd_nmps * dt
            ac.y_nm += math.cos(hdg) * spd_nmps * dt
            ac.altitudeFt += int(ac.verticalRateFpm * dt / 60.0)

        # cull far
        self.intruders = [a for a in self.intruders if math.hypot(a.x_nm, a.y_nm) < 16.0]
        self.intruder_xpdrs = {cs: xp for cs, xp in self.intruder_xpdrs.items() if any(a.callsign == cs for a in self.intruders)}

        # tracks
        self.tcas.tracks = self.tracker.update(
            now=now,
            ownship=self.ownship,
            intruders=self.intruders,
            intruder_xpdrs=self.intruder_xpdrs,
            tcas_mode=self.tcas.mode,
            thresholds=self.tcas.activeThresholds,
        )

        # advisories
        ta, ra = self.advisory_engine.update(
            now=now,
            ownship=self.ownship,
            tcas_mode=self.tcas.mode,
            thresholds=self.tcas.activeThresholds,
            tracks=list(self.tcas.tracks.values()),
        )

        # update banner on transitions
        if ra and ra.kind in (RAKind.CLIMB, RAKind.DESCEND, RAKind.LEVEL_OFF):
            if ra.kind == RAKind.CLIMB:
                self.set_banner("CLIMB, CLIMB", 5.0)
            elif ra.kind == RAKind.DESCEND:
                self.set_banner("DESCEND, DESCEND", 5.0)
            elif ra.kind == RAKind.LEVEL_OFF:
                self.set_banner("LEVEL OFF, LEVEL OFF", 5.0)
        elif ta and not ra:
            self.set_banner("TRAFFIC, TRAFFIC", 4.0)
        elif (not ta) and (not ra) and self.advisory_engine.primaryThreat is None:
            # optional: could detect a true RA->NONE transition more precisely
            pass

        # apply autopilot (demo)
        self._autopilot_step(dt, ra)

        # build display entries (UML object DisplayEntry)
        display_entries = self._build_display_entries()

        return ta, ra, display_entries

    def _autopilot_step(self, dt: float, ra):
        if self.ap_mode == "RA" and ra is not None:
            desired_vs = ra.requiredVerticalRateFpm
            if ra.kind == RAKind.LEVEL_OFF:
                desired_vs = 0
            self.cmd_vs_fpm = desired_vs
        else:
            err = self.ownship.targetAltitudeFt - self.ownship.altitudeFt
            self.cmd_vs_fpm = int(max(-3000, min(3000, err * 3)))

        dv = self.cmd_vs_fpm - self.ownship.verticalRateFpm
        self.ownship.verticalRateFpm += int(max(-450, min(450, dv)))
        self.ownship.altitudeFt += int(self.ownship.verticalRateFpm * dt / 60.0)

    def _build_display_entries(self) -> List[DisplayEntry]:
        entries: List[DisplayEntry] = []
        for trk in self.tcas.tracks.values():
            # vertical trend
            if trk.intruderVerticalRateFpm > 500:
                vt = VerticalTrend.CLIMBING
            elif trk.intruderVerticalRateFpm < -500:
                vt = VerticalTrend.DESCENDING
            else:
                vt = VerticalTrend.LEVEL

            # threat level + symbology + color
            if trk.state == TrackState.THREAT_RA:
                tl = ThreatLevel.RESOLUTION_ADVISORY
                col = DisplayColor.RED
                sym = SymbolType.SQUARE
            elif trk.state == TrackState.INTRUDER_TA:
                tl = ThreatLevel.TRAFFIC_ADVISORY
                col = DisplayColor.YELLOW
                sym = SymbolType.CIRCLE
            elif trk.state == TrackState.PROXIMATE:
                tl = ThreatLevel.PROXIMITY
                col = DisplayColor.CYAN
                sym = SymbolType.DIAMOND
            else:
                tl = ThreatLevel.NON_THREAT
                col = DisplayColor.WHITE
                sym = SymbolType.DIAMOND

            entries.append(
                DisplayEntry(
                    relativeAltitudeFt=trk.relativeAltitudeFt,
                    verticalTrend=vt,
                    threatLevel=tl,
                    color=col,
                    symbolType=sym,
                )
            )
        return entries

    def _spawn_intruder(self) -> tuple[Aircraft, Transponder]:
        own = self.ownship
        make_threat = (random.random() < self.threat_spawn_prob)

        if make_threat:
            r = random.uniform(0.8, 2.2)
            theta = random.uniform(0, 2 * math.pi)
            x = math.cos(theta) * r
            y = math.sin(theta) * r
            hdg = (math.degrees(math.atan2(-x, -y)) + 360.0) % 360.0
            alt = own.altitudeFt + random.randint(-500, 500)
            vr = random.choice([-1500, -1000, -500]) if alt > own.altitudeFt else random.choice([500, 1000, 1500])
            gs = random.uniform(280, 520)
        else:
            r = random.uniform(2.0, 12.0)
            theta = random.uniform(0, 2 * math.pi)
            x = math.cos(theta) * r
            y = math.sin(theta) * r
            hdg = (math.degrees(theta) + 180) % 360
            alt = own.altitudeFt + random.randint(-3000, 3000)
            vr = random.choice([-2000, -1500, -1000, -500, 0, 500, 1000, 1500, 2000])
            gs = random.uniform(180, 480)

        callsign = f"AC{random.randint(10, 99)}"
        ac = Aircraft(callsign, int(alt), int(vr), float(gs), float(hdg), float(x), float(y), int(alt))

        xpdr = Transponder(
            mode=TransponderMode.MODE_S,
            squawk="1200",
            altitudeReporting=True,
            modeSAddress=f"{random.randint(0, 2**24 - 1):06X}",
        )
        return ac, xpdr
