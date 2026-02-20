from __future__ import annotations
import math
from typing import List, Optional

from PySide6.QtCore import Qt, QRectF
from PySide6.QtGui import QPainter, QPen, QBrush, QPainterPath, QFont
from PySide6.QtWidgets import QGraphicsScene, QGraphicsView

from tcas_sim.tracking.track import Track
from tcas_sim.enums import DisplayColor, SymbolType, TrackState
from tcas_sim.advisories.advisory import ResolutionAdvisory
from tcas_sim.enums import RAKind


class TrafficScope(QGraphicsView):
    def __init__(self):
        self.scene = QGraphicsScene()
        super().__init__(self.scene)
        self.setBackgroundBrush(QBrush(Qt.black))
        self.setSceneRect(-260, -260, 520, 520)
        self.setFrameShape(QGraphicsView.NoFrame)

        self.selectedRangeNm = 5.0
        self.ownshipHeadingDeg = 0.0
        self.active_ra: Optional[ResolutionAdvisory] = None
        self.banner_text: str = ""

        self._bezel_outer_r = 242
        self._bezel_thickness = 22

    def set_range_nm(self, rng: float) -> None:
        self.selectedRangeNm = float(rng)
        self.viewport().update()

    def set_heading_deg(self, hdg: float) -> None:
        self.ownshipHeadingDeg = float(hdg) % 360.0
        self.viewport().update()

    def set_ra(self, ra: Optional[ResolutionAdvisory]) -> None:
        self.active_ra = ra
        self.viewport().update()

    def set_banner(self, text: str) -> None:
        self.banner_text = text
        self.viewport().update()

    def render_tracks(self, tracks: List[Track]) -> None:
        self.scene.clear()

        pen_ring = QPen(Qt.gray)
        pen_ring.setWidth(1)
        for frac in (1.0, 0.5, 0.25):
            px = frac * 190
            self.scene.addEllipse(-px, -px, 2 * px, 2 * px, pen_ring)

        self.scene.addEllipse(-5, -5, 10, 10, QPen(Qt.cyan), QBrush(Qt.cyan))

        for trk in tracks:
            x, y = self._polar_to_xy(trk.bearingDeg, trk.rangeNm)

            if trk.state == TrackState.THREAT_RA:
                col = Qt.red
                sym = SymbolType.SQUARE
            elif trk.state == TrackState.INTRUDER_TA:
                col = Qt.yellow
                sym = SymbolType.CIRCLE
            elif trk.state == TrackState.PROXIMATE:
                col = Qt.cyan
                sym = SymbolType.DIAMOND
            else:
                col = Qt.white
                sym = SymbolType.DIAMOND

            pen = QPen(col); pen.setWidth(2)
            brush = QBrush(col)

            if sym == SymbolType.DIAMOND:
                poly = [(-0, -7), (7, 0), (0, 7), (-7, 0)]
                qpoly = [self._pt(x + dx, y + dy) for dx, dy in poly]
                if trk.state == TrackState.OTHER:
                    self.scene.addPolygon(qpoly, pen)
                else:
                    self.scene.addPolygon(qpoly, pen, brush)
            elif sym == SymbolType.CIRCLE:
                self.scene.addEllipse(x - 7, y - 7, 14, 14, pen, brush)
            else:
                self.scene.addRect(x - 7, y - 7, 14, 14, pen, brush)

            rel_hund = int(round(trk.relativeAltitudeFt / 100.0))
            tag = f"{rel_hund:+03d}"
            titem = self.scene.addText(tag)
            titem.setDefaultTextColor(col)
            titem.setPos(x + 12, y - 12)

        self.viewport().update()

    def drawForeground(self, painter: QPainter, rect):
        super().drawForeground(painter, rect)
        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.save()

        self._draw_bezel_outline(painter)
        self._draw_ra_bezel_overlay(painter)
        self._draw_heading_arrow(painter)

        painter.setPen(QPen(Qt.cyan))
        font = QFont(); font.setPointSize(14); font.setBold(True)
        painter.setFont(font)
        painter.drawText(150, -225, "RNG")
        painter.drawText(210, -225, f"{int(self.selectedRangeNm)}")

        if self.banner_text:
            painter.setPen(QPen(Qt.white))
            f2 = QFont(); f2.setPointSize(16); f2.setBold(True)
            painter.setFont(f2)
            painter.drawText(-240, -230, 480, 30, Qt.AlignCenter, self.banner_text)

        painter.restore()

    def _draw_bezel_outline(self, p: QPainter):
        outer = self._bezel_outer_r
        thick = self._bezel_thickness
        inner = outer - thick

        p.setPen(Qt.NoPen)
        p.setBrush(QBrush(Qt.darkGray))
        rect_outer = QRectF(-outer, -outer, 2 * outer, 2 * outer)
        rect_inner = QRectF(-inner, -inner, 2 * inner, 2 * inner)
        path = QPainterPath()
        path.addEllipse(rect_outer)
        hole = QPainterPath()
        hole.addEllipse(rect_inner)
        path = path.subtracted(hole)
        p.drawPath(path)

        p.setPen(QPen(Qt.gray, 2))
        p.setBrush(Qt.NoBrush)
        p.drawEllipse(rect_inner)

    def _draw_ra_bezel_overlay(self, p: QPainter):
        ra = self.active_ra
        if ra is None or ra.kind not in (RAKind.CLIMB, RAKind.DESCEND):
            return

        outer = self._bezel_outer_r
        thick = self._bezel_thickness
        inner = outer - thick

        def seg_path(start_deg: float, span_deg: float) -> QPainterPath:
            qt_start = 90 - start_deg
            rect_outer = QRectF(-outer, -outer, 2 * outer, 2 * outer)
            rect_inner = QRectF(-inner, -inner, 2 * inner, 2 * inner)
            path = QPainterPath()
            path.arcMoveTo(rect_outer, qt_start)
            path.arcTo(rect_outer, qt_start, -span_deg)
            path.arcTo(rect_inner, qt_start - span_deg, span_deg)
            path.closeSubpath()
            return path

        if ra.kind == RAKind.CLIMB:
            green_start, green_span = (345, 40)
        else:
            green_start, green_span = (165, 40)

        red1_start = (green_start + green_span) % 360
        red1_span = 180
        red2_start = (red1_start + red1_span) % 360
        red2_span = 360 - green_span - red1_span

        p.setPen(Qt.NoPen)
        p.setBrush(QBrush(Qt.red))
        p.drawPath(seg_path(red1_start, red1_span))
        p.drawPath(seg_path(red2_start, red2_span))

        p.setBrush(QBrush(Qt.green))
        p.drawPath(seg_path(green_start, green_span))

    def _draw_heading_arrow(self, p: QPainter):
        ang = math.radians(self.ownshipHeadingDeg)
        L = 150
        x = math.sin(ang) * L
        y = -math.cos(ang) * L

        pen = QPen(Qt.white, 7)
        pen.setCapStyle(Qt.RoundCap)
        p.setPen(pen)
        p.drawLine(0, 0, x, y)

        head = 22
        left = ang + math.radians(150)
        right = ang - math.radians(150)
        lx = x + math.sin(left) * head
        ly = y - math.cos(left) * head
        rx = x + math.sin(right) * head
        ry = y - math.cos(right) * head
        p.drawLine(x, y, lx, ly)
        p.drawLine(x, y, rx, ry)

    def _polar_to_xy(self, bearingDeg: float, rangeNm: float):
        r_px = (rangeNm / self.selectedRangeNm) * 190
        ang = math.radians(bearingDeg)
        x = math.sin(ang) * r_px
        y = -math.cos(ang) * r_px
        return x, y

    def _pt(self, x: float, y: float):
        from PySide6.QtCore import QPointF
        return QPointF(x, y)
