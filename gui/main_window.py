from __future__ import annotations
import time
from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import QMainWindow, QWidget, QHBoxLayout

from tcas_sim.sim.simulator import Simulator
from tcas_sim.gui.traffic_scope import TrafficScope
from tcas_sim.gui.ra_vsi import RAVsiWidget
from tcas_sim.gui.control_panel import ControlPanel


class MainWindow(QMainWindow):
    def __init__(self, sim: Simulator):
        super().__init__()
        self.setWindowTitle("TCAS-II Simulator (UML-aligned packages)")

        self.sim = sim
        self.scope = TrafficScope()
        self.vsi = RAVsiWidget()
        self.panel = ControlPanel(self.sim, self.scope, self.vsi)

        root = QWidget()
        row = QHBoxLayout(root)
        row.setContentsMargins(10, 10, 10, 10)
        row.addWidget(self.scope, stretch=3)
        row.addWidget(self.panel, stretch=1)
        self.setCentralWidget(root)

        self._last = time.time()
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.tick)
        self.timer.start(33)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Left:
            self.sim.ownship.headingDeg = (self.sim.ownship.headingDeg - 5) % 360.0
        elif event.key() == Qt.Key_Right:
            self.sim.ownship.headingDeg = (self.sim.ownship.headingDeg + 5) % 360.0
        else:
            super().keyPressEvent(event)

    def tick(self):
        now = time.time()
        dt = now - self._last
        self._last = now

        ta, ra, _display_entries = self.sim.step(dt)

        self.scope.set_heading_deg(self.sim.ownship.headingDeg)
        self.scope.set_ra(ra)
        self.scope.set_banner(self.sim.banner())
        self.scope.render_tracks(list(self.sim.tcas.tracks.values()))

        self.panel.refresh()
        self.vsi.set_state(self.sim.ownship.verticalRateFpm, ra)
