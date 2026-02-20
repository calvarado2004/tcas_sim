from __future__ import annotations
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame, QSizePolicy, QApplication

from tcas_sim.sim.simulator import Simulator
from tcas_sim.gui.traffic_scope import TrafficScope
from tcas_sim.gui.ra_vsi import RAVsiWidget


class ControlPanel(QWidget):
    def __init__(self, sim: Simulator, scope: TrafficScope, vsi: RAVsiWidget):
        super().__init__()
        self.sim = sim
        self.scope = scope
        self.vsi = vsi

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignTop)

        hdr = QLabel("RNG")
        hdr.setStyleSheet("color: white; font-weight: 700;")
        layout.addWidget(hdr)

        rng_row = QHBoxLayout()
        for r in (3, 5, 10):
            b = QPushButton(f"{r} NM")
            b.clicked.connect(lambda _=False, rr=r: self.scope.set_range_nm(rr))
            rng_row.addWidget(b)
        layout.addLayout(rng_row)
        layout.addSpacing(10)

        self.lbl_sl = QLabel("")
        self.lbl_alt = QLabel("")
        self.lbl_vs = QLabel("")
        self.lbl_talt = QLabel("")
        self.lbl_ap = QLabel("")
        for lab in (self.lbl_sl, self.lbl_alt, self.lbl_vs, self.lbl_talt, self.lbl_ap):
            lab.setStyleSheet("color: white; font-family: Menlo, monospace; font-size: 13px;")
            lab.setFrameShape(QFrame.Panel)
            lab.setFrameShadow(QFrame.Sunken)
            lab.setMargin(6)
            layout.addWidget(lab)

        layout.addSpacing(10)

        btn_row = QHBoxLayout()
        self.btn_dn = QPushButton("⬇︎ ALT DOWN")
        self.btn_up = QPushButton("⬆︎ ALT UP")
        self.btn_dn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.btn_up.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.btn_dn.clicked.connect(lambda: self.bump_target(-100))
        self.btn_up.clicked.connect(lambda: self.bump_target(+100))
        btn_row.addWidget(self.btn_dn)
        btn_row.addWidget(self.btn_up)
        layout.addLayout(btn_row)

        hint = QLabel("Click: ±100 ft   |   Shift-click: ±1000 ft")
        hint.setStyleSheet("color: gray; font-size: 11px;")
        layout.addWidget(hint)

        layout.addSpacing(10)

        hdg_row = QHBoxLayout()
        self.btn_hdg_l = QPushButton("⬅︎ HDG")
        self.btn_hdg_r = QPushButton("HDG ➡︎")
        self.btn_hdg_l.clicked.connect(lambda: self.bump_heading(-5))
        self.btn_hdg_r.clicked.connect(lambda: self.bump_heading(+5))
        hdg_row.addWidget(self.btn_hdg_l)
        hdg_row.addWidget(self.btn_hdg_r)
        layout.addLayout(hdg_row)

        layout.addSpacing(10)

        ap_row = QHBoxLayout()
        self.btn_ap_alt = QPushButton("AP: ALT")
        self.btn_ap_ra = QPushButton("AP: RA")
        self.btn_ap_alt.clicked.connect(lambda: self.set_ap_mode("ALT"))
        self.btn_ap_ra.clicked.connect(lambda: self.set_ap_mode("RA"))
        ap_row.addWidget(self.btn_ap_alt)
        ap_row.addWidget(self.btn_ap_ra)
        layout.addLayout(ap_row)

        layout.addSpacing(10)
        layout.addWidget(self.vsi)

        self.setStyleSheet("""
            QWidget { background: #111; }
            QPushButton { padding: 10px; font-weight: 650; }
        """)

    def set_ap_mode(self, mode: str):
        self.sim.ap_mode = mode

    def bump_target(self, delta: int):
        mods = QApplication.keyboardModifiers()
        if mods & Qt.ShiftModifier:
            delta *= 10
        self.sim.ownship.targetAltitudeFt += delta

    def bump_heading(self, delta_deg: int):
        mods = QApplication.keyboardModifiers()
        if mods & Qt.ShiftModifier:
            delta_deg *= 3
        self.sim.ownship.headingDeg = (self.sim.ownship.headingDeg + delta_deg) % 360.0

    def refresh(self):
        own = self.sim.ownship
        self.lbl_sl.setText(f"SL:   {self.sim.tcas.currentSL.name}")
        self.lbl_alt.setText(f"ALT:  {own.altitudeFt:6d} ft")
        self.lbl_vs.setText(f"VS:   {own.verticalRateFpm:6d} fpm")
        self.lbl_talt.setText(f"TALT: {own.targetAltitudeFt:6d} ft")
        self.lbl_ap.setText(f"AP:   {self.sim.ap_mode}   CMDVS:{self.sim.cmd_vs_fpm:+d}")
