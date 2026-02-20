# TCAS-II Simulator (UML-aligned, Formal-Spec Ready)

This project is a **TCAS-II inspired simulator** implemented in Python with a GUI, structured as a multi-package codebase that **mirrors a UML class diagram** suitable for **formal specification work** (e.g., Z/EVES or OCL/USE).

The goal is not just to draw UML, but to **implement the model** and make it easy to:
- trace behavior back to formal concepts (tracks, advisories, zones, thresholds),
- write invariants and pre/postconditions over the same entities,
- evolve the model toward a more complete TCAS-II spec.

> The GUI is deliberately separated from the UML model packages. It consumes the model objects but does not define the formal system.

---

## Features

### Formal-system aligned model
- **Core platform objects**: `Aircraft`, `TCAS`, `Transponder`
- **Surveillance & tracking**: `Track` with tau/rate/closure fields, `TrackState`
- **Sensitivity level logic**: `SensitivityProfile` and `SensitivityThresholds`
- **Protected zones**: `AirspaceVolume` + `CautionZone`, `WarningZone`, `CollisionZone`
- **Advisories**: `TrafficAdvisory`, `ResolutionAdvisory` with RA kind/sense and guidance bands
- **Coordination** (stubbed): `CoordinationSession`, `ResolutionPair` for future TCAS/TCAS work
- **Enumerations** in a central module (`tcas_sim/enums.py`) to keep the model consistent

### Working simulator + GUI
- Random intruder generation with configurable:
  - time scaling
  - max intruders
  - threat spawn probability
- Tau/DMOD/ZTHR based TA/RA gating (educational implementation)
- RA guidance presented as red/green bands (IVSI-like)
- On-screen alert banner (e.g., `TRAFFIC, TRAFFIC`, `CLIMB, CLIMB`, etc.)

---

## Repository Layout

The Python package layout is intentionally aligned with the UML packages:

```
tcas_sim/
app.py
enums.py

core/           # Core Platform
sensitivity/    # Sensitivity & Thresholds
tracking/       # Surveillance & Tracking
zones/          # Protected Airspace & Zones
advisories/     # Advisories
cockpit/        # Cockpit Outputs
coordination/   # Coordination (TCAS II)

sim/            # Simulation harness (NOT part of UML)
gui/            # GUI widgets (NOT part of UML)
````

### What is *not* part of the UML model?
- `tcas_sim/sim/` (random traffic, kinematic movement, time scaling)
- `tcas_sim/gui/` (PySide6 rendering and controls)
- `tcas_sim/app.py` (entrypoint)

These exist to demonstrate the model, but do not define it.

---

## Requirements

- Python 3.10+ recommended
- `PySide6`

Install:

```bash
pip install pyside6
````

---

## Run

From the directory **above** `tcas_sim/`:

```bash
python -m tcas_sim.app
```

A window will open with:

* a **traffic scope** (targets + relative altitude tags),
* an **RA/VSI** widget (red/green bands),
* a **control panel** (RNG selection, altitude bug, heading pointer, AP modes).

---

## Configuration

The simulation harness is configurable via `Simulator(...)` in `tcas_sim/app.py`:

```python
sim = Simulator(
    time_scale=1.5,
    max_intruders=10,
    threat_spawn_prob=0.30
)
```

Recommended for demos:

* Increase `time_scale` to observe altitude deltas and RA evolution faster.
* Adjust `threat_spawn_prob` to see more frequent TA/RA events.

---

## How the Logic Maps to Formal Concepts

The code is organized so you can write formal constraints against stable model objects.

### Key objects for formal specification

* `tracking.Track`

  * `rangeTauSec`, `verticalTauSec`
  * `closureRateKts`, `verticalClosureFpm`
  * `TrackState` derived from TA/RA gating
* `sensitivity.SensitivityThresholds`

  * `taTauSec`, `raTauSec`, `taDMODNm`, `raDMODNm`, `taZTHRFt`, `raZTHRFt`, `alimFt`
* `advisories.ResolutionAdvisory`

  * `RAKind`, `RASense`
  * `requiredVerticalRateFpm`, `minAllowedVSFpm`, `maxAllowedVSFpm`
  * `alimFt`

### Typical invariants you can encode (examples)

* Relative altitude correctness:

  * `Track.relativeAltitudeFt = intruder.altitudeFt - ownship.altitudeFt`
* Tau definition constraints:

  * if closure > 0 then `rangeTauSec = rangeNm / closureRateKts * 3600` else `∞`
* RA precondition:

  * If `intruderTransponder.altitudeReporting = false` then `TrackState != THREAT_RA`
* Symbology consistency:

  * `TrackState == THREAT_RA -> symbol is SQUARE + color RED`

These are intentionally “close to the metal” to support a Z/OCL formalization.

---

## Design Notes

* This is an **educational simulator**, not DO-185B compliant.
* It captures the *core idea* of TCAS-II:

  * time-based alerting (tau),
  * threshold-dependent protected volume (DMOD/ZTHR/ALIM),
  * vertical-only resolution guidance.

Planned refinements (good targets for formal-method extensions):

* Horizontal miss distance filtering (HMD)
* Multi-threat composite RAs
* TCAS/TCAS coordination using `CoordinationSession`
* AGL-based inhibits (radar altitude integration)
* More faithful RA taxonomy (preventive vs corrective, strengthening, reversals)

---

## Author

**[Carlos Alvarado Martinez]** - [GitHub](https://github.com/calvarado2004)

## License / Disclaimer

This project is for **academic and demonstrative purposes** only.
It must not be used for real-world collision avoidance, aviation operations, or safety-critical decision-making.

MIT License - see LICENSE file for details.
