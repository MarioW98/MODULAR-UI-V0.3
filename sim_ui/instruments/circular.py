from __future__ import annotations
import math

from PySide6.QtCore import Qt, QPointF, QRectF
from PySide6.QtGui import QColor, QPainter, QPainterPath, QPen

from .base import BaseInstrument
from ..core.telemetry import TelemetryData


class CircularGauge(BaseInstrument):
    def __init__(self, proto, parent=None):
        super().__init__(proto, parent)
        self._value = 0.0
        self._min_val = 0.0
        self._max_val = 100.0
        self._major_step = 20.0
        self._minor_per_major = 4
        self._unit_label = ""
        self._label_format = "{:.0f}"

    def value_to_rotation(self, v: float) -> float:
        n = (v - self._min_val) / max(1e-9, self._max_val - self._min_val)
        return -135.0 + max(0.0, min(1.0, n)) * 270.0

    def update_data(self, data: TelemetryData):
        pass

    def paint_background(self, p):
        th = self.theme()
        w, h = self._prototype.width, self._prototype.height
        cx, cy = w / 2, h / 2
        outer_r = min(cx, cy) - 4

        # Bezel
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(th.bezel_color)
        p.drawEllipse(QPointF(cx, cy), outer_r, outer_r)

        # Quadrante
        dial_r = outer_r - 6
        p.setBrush(th.dial_color)
        p.drawEllipse(QPointF(cx, cy), dial_r, dial_r)

        tick_outer = dial_r - 4
        major_len = 14
        minor_len = 8
        label_r = tick_outer - major_len - 12
        nm = int((self._max_val - self._min_val) / self._major_step) + 1

        for i in range(nm):
            val = self._min_val + i * self._major_step
            rot = self.value_to_rotation(val)

            # Tacca maggiore
            p.save()
            p.translate(cx, cy)
            p.rotate(rot)
            p.setPen(QPen(th.tick_major_color, th.tick_major_width))
            p.drawLine(QPointF(0, -tick_outer), QPointF(0, -tick_outer + major_len))
            p.restore()

            # Numero
            rad = math.radians(rot)
            lx = cx + label_r * math.sin(rad)
            ly = cy - label_r * math.cos(rad)
            p.setPen(th.text_color)
            lf = p.font()
            if th.font_family:
                lf.setFamily(th.font_family)
            lf.setPixelSize(th.font_size_numbers)
            p.setFont(lf)
            p.drawText(QRectF(lx - 20, ly - 8, 40, 16),
                       Qt.AlignmentFlag.AlignCenter,
                       self._label_format.format(val))

            # Tacche minori
            if i < nm - 1:
                for m in range(1, self._minor_per_major + 1):
                    mv = val + m * (self._major_step / (self._minor_per_major + 1))
                    mr = self.value_to_rotation(mv)
                    p.save()
                    p.translate(cx, cy)
                    p.rotate(mr)
                    p.setPen(QPen(th.tick_minor_color, th.tick_minor_width))
                    p.drawLine(QPointF(0, -tick_outer), QPointF(0, -tick_outer + minor_len))
                    p.restore()

        # Titolo
        p.setPen(th.text_secondary_color)
        tf = p.font()
        if th.font_family:
            tf.setFamily(th.font_family)
        tf.setPixelSize(th.font_size_title)
        tf.setBold(True)
        p.setFont(tf)
        p.drawText(QRectF(cx - 50, cy + dial_r * 0.35, 100, 20),
                   Qt.AlignmentFlag.AlignCenter,
                   self._prototype.display_name.upper())

        # Etichetta unità
        if self._unit_label:
            p.setPen(th.text_tertiary_color)
            uf = p.font()
            if th.font_family:
                uf.setFamily(th.font_family)
            uf.setPixelSize(th.font_size_unit)
            uf.setBold(False)
            p.setFont(uf)
            p.drawText(QRectF(cx - 40, cy + dial_r * 0.55, 80, 16),
                       Qt.AlignmentFlag.AlignCenter, self._unit_label)

    def paint_foreground(self, p):
        th = self.theme()
        w, h = self._prototype.width, self._prototype.height
        cx, cy = w / 2, h / 2
        dial_r = min(cx, cy) - 10
        needle_len = dial_r - 20
        rot = self.value_to_rotation(self._value)

        # Lancetta
        p.save()
        p.translate(cx, cy)
        p.rotate(rot)
        nd = QPainterPath()
        nd.moveTo(0, -needle_len)
        nd.lineTo(-3, 12)
        nd.lineTo(3, 12)
        nd.closeSubpath()
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(th.needle_color)
        p.drawPath(nd)
        p.restore()

        # Cappuccio centrale
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(th.needle_hub_color)
        p.drawEllipse(QPointF(cx, cy), 7, 7)