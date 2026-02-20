from __future__ import annotations
from PySide6.QtCore import Qt, QRectF, QSize
from PySide6.QtGui import QPainter, QPen, QBrush, QFont
from PySide6.QtWidgets import QWidget
from tcas_sim.advisories.advisory import ResolutionAdvisory
from tcas_sim.enums import RAKind


class RAVsiWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.setMinimumSize(QSize(260, 380))
        self.vs_fpm = 0
        self.ra: ResolutionAdvisory | None = None

    def set_state(self, vs_fpm: int, ra: ResolutionAdvisory | None) -> None:
        self.vs_fpm = int(vs_fpm)
        self.ra = ra
        self.update()

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing, True)

        w, h = self.width(), self.height()
        p.fillRect(0, 0, w, h, Qt.black)

        max_vs = 3000
        top = 34
        bottom = h - 20

        def y_for(vs: int) -> int:
            vs = max(-max_vs, min(max_vs, vs))
            frac = (max_vs - vs) / (2 * max_vs)
            return int(top + frac * (bottom - top))

        p.setPen(QPen(Qt.gray, 2))
        p.drawRect(18, top, w - 36, bottom - top)

        p.setPen(QPen(Qt.gray, 1))
        f = QFont()
        f.setPointSize(10)
        p.setFont(f)
        for tick in (-3000, -2000, -1000, 0, 1000, 2000, 3000):
            y = y_for(tick)
            p.drawLine(18, y, 45, y)
            lbl = "0" if tick == 0 else f"{tick//1000:+d}k"
            p.drawText(52, y + 4, lbl)

        if self.ra:
            band_half = 250
            kind = self.ra.kind
            req = self.ra.requiredVerticalRateFpm

            if kind == RAKind.CLIMB:
                y_red_start = y_for(+500)
                p.fillRect(QRectF(18, y_red_start, w - 36, bottom - y_red_start), QBrush(Qt.red))
            elif kind == RAKind.DESCEND:
                y_red_end = y_for(-500)
                p.fillRect(QRectF(18, top, w - 36, max(0, y_red_end - top)), QBrush(Qt.red))
            elif kind == RAKind.LEVEL_OFF:
                y1 = y_for(+band_half)
                y2 = y_for(-band_half)
                p.fillRect(QRectF(18, top, w - 36, max(0, min(y1, y2) - top)), QBrush(Qt.red))
                p.fillRect(QRectF(18, max(y1, y2), w - 36, max(0, bottom - max(y1, y2))), QBrush(Qt.red))

            y1 = y_for(req + band_half)
            y2 = y_for(req - band_half)
            p.fillRect(QRectF(18, min(y1, y2), w - 36, abs(y2 - y1)), QBrush(Qt.darkGreen))

        y_vs = y_for(self.vs_fpm)
        p.setPen(QPen(Qt.cyan, 3))
        p.drawLine(18, y_vs, w - 18, y_vs)
        p.drawText(w - 85, y_vs - 6, f"{self.vs_fpm:+d}")

        p.setPen(QPen(Qt.white, 2))
        hf = QFont()
        hf.setPointSize(11)
        hf.setBold(True)
        p.setFont(hf)

        label = "RA: NONE"
        if self.ra:
            label = f"RA: {self.ra.kind.name} ({self.ra.requiredVerticalRateFpm:+d} fpm)"
        p.drawText(18, 20, label)
