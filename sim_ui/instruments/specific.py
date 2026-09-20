from __future__ import annotations
import math

from PySide6.QtCore import Qt, QPointF, QRectF
from PySide6.QtGui import QBrush, QColor, QPainter, QPainterPath, QPen

from .base import BaseInstrument, UnitButtonsMixin
from .circular import CircularGauge
from ..core.telemetry import TelemetryData
from ..core.units import AIRSPEED_UNITS, ALTITUDE_UNITS, VSI_UNITS


class AirspeedIndicator(UnitButtonsMixin, CircularGauge):
    """
    Anemometro con cambio unità:
    KNOTS → KM/H → MPH → M/S
    """

    def __init__(self, p, parent=None):
        super().__init__(p, parent)

        self._base_min = 0.0
        self._base_max = 200.0
        self._base_value = 0.0

        self._minor_per_major = 4

        self.init_units(AIRSPEED_UNITS, 0)
        self._apply_unit()

    def _on_unit_changed(self):
        self._apply_unit()
        super()._on_unit_changed()

    def _apply_unit(self):
        u = self.current_unit()
        if not u:
            return

        self._min_val = self._base_min * u.factor
        self._max_val = self._base_max * u.factor
        self._major_step = u.major_step if u.major_step else 20.0 * u.factor
        self._unit_label = u.label
        self._label_format = "{:.%df}" % u.decimals

        self._value = self._base_value * u.factor

    def update_data(self, d: TelemetryData):
        self._base_value = d.airspeed
        self._value = self._base_value * self.current_unit().factor
        self.update()

class Altimeter(UnitButtonsMixin, BaseInstrument):
    """
    Altimetro sensibile a due lancette con cambio unità:
    FEET → METERS
    """

    def __init__(self, prototype, parent=None):
        super().__init__(prototype, parent)
        self._altitude = 0.0
        self.init_units(ALTITUDE_UNITS, 0)

    def update_data(self, data: TelemetryData):
        self._altitude = max(0.0, data.altitude)
        self.update()

    def _display_altitude(self) -> float:
        u = self.current_unit()
        if not u:
            return self._altitude
        return self._altitude * u.factor

    # =========================================================================
    # SFONDO
    # =========================================================================

    def paint_background(self, painter: QPainter):
        w, h = self._prototype.width, self._prototype.height
        cx, cy = w / 2, h / 2
        outer_r = min(cx, cy) - 4

        # Bezel
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(40, 40, 45))
        painter.drawEllipse(QPointF(cx, cy), outer_r, outer_r)

        dial_r = outer_r - 6
        painter.setBrush(QColor(18, 20, 26))
        painter.drawEllipse(QPointF(cx, cy), dial_r, dial_r)

        # Tacche e numeri 0-9
        tick_outer = dial_r - 4
        num_r = tick_outer - 22

        for i in range(10):
            angle_deg = i * 36.0

            # Tacca principale
            painter.save()
            painter.translate(cx, cy)
            painter.rotate(angle_deg)
            painter.setPen(QPen(QColor(230, 230, 230), 2.5))
            painter.drawLine(QPointF(0, -tick_outer), QPointF(0, -tick_outer + 16))
            painter.restore()

            # Numero
            rad = math.radians(angle_deg)
            lx = cx + num_r * math.sin(rad)
            ly = cy - num_r * math.cos(rad)

            painter.setPen(QColor(240, 240, 240))
            nf = painter.font()
            nf.setPixelSize(16)
            nf.setBold(True)
            painter.setFont(nf)
            painter.drawText(
                QRectF(lx - 12, ly - 10, 24, 20),
                Qt.AlignmentFlag.AlignCenter,
                str(i)
            )

            # Tacche minori
            for m in range(1, 5):
                minor_angle = angle_deg + m * (36.0 / 5.0)

                painter.save()
                painter.translate(cx, cy)
                painter.rotate(minor_angle)
                painter.setPen(QPen(QColor(180, 180, 180), 1))
                painter.drawLine(QPointF(0, -tick_outer), QPointF(0, -tick_outer + 8))
                painter.restore()

        # Titolo
        painter.setPen(QColor(180, 190, 200))
        tf = painter.font()
        tf.setPixelSize(9)
        tf.setBold(True)
        painter.setFont(tf)
        painter.drawText(
            QRectF(cx - 50, cy + dial_r * 0.30, 100, 16),
            Qt.AlignmentFlag.AlignCenter,
            "ALT"
        )

        # Etichetta unità
        u = self.current_unit()
        caption = f"100 {u.label}" if u else ""

        painter.setPen(QColor(140, 150, 160))
        uf = painter.font()
        uf.setPixelSize(8)
        uf.setBold(False)
        painter.setFont(uf)
        painter.drawText(
            QRectF(cx - 40, cy + dial_r * 0.48, 80, 14),
            Qt.AlignmentFlag.AlignCenter,
            caption
        )

    # =========================================================================
    # PRIMO PIANO
    # =========================================================================

    def paint_foreground(self, painter: QPainter):
        w, h = self._prototype.width, self._prototype.height
        cx, cy = w / 2, h / 2
        dial_r = min(cx, cy) - 10

        alt = self._display_altitude()

        # Lancetta lunga: 1 giro = 1000 unità
        hundreds = alt % 1000.0
        hundreds_angle = (hundreds / 1000.0) * 360.0

        # Lancetta corta: 1 giro = 10000 unità
        thousands = alt % 10000.0
        thousands_angle = (thousands / 10000.0) * 360.0

        # Lancetta corta
        painter.save()
        painter.translate(cx, cy)
        painter.rotate(thousands_angle)

        short_len = dial_r * 0.55
        short_needle = QPainterPath()
        short_needle.moveTo(0, -short_len)
        short_needle.lineTo(-5, 10)
        short_needle.lineTo(5, 10)
        short_needle.closeSubpath()

        painter.setPen(QPen(QColor(200, 200, 200), 1))
        painter.setBrush(QColor(255, 255, 255))
        painter.drawPath(short_needle)
        painter.restore()

        # Lancetta lunga
        painter.save()
        painter.translate(cx, cy)
        painter.rotate(hundreds_angle)

        long_len = dial_r - 14
        long_needle = QPainterPath()
        long_needle.moveTo(0, -long_len)
        long_needle.lineTo(-2.5, 14)
        long_needle.lineTo(2.5, 14)
        long_needle.closeSubpath()

        painter.setPen(QPen(QColor(200, 200, 200), 1))
        painter.setBrush(QColor(255, 255, 255))
        painter.drawPath(long_needle)
        painter.restore()

        # Cappuccio centrale
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(80, 80, 85))
        painter.drawEllipse(QPointF(cx, cy), 8, 8)

        painter.setBrush(QColor(50, 50, 55))
        painter.drawEllipse(QPointF(cx, cy), 5, 5)


class DigitalAltimeter(UnitButtonsMixin, BaseInstrument):
    """
    Altimetro digitale compatto con cambio unità:
    FEET → METERS
    """

    def __init__(self, prototype, parent=None):
        super().__init__(prototype, parent)

        self._altitude = 0.0
        self._prev_altitude = 0.0
        self._px_per_step = 24.0
        self._step = 100.0

        self.init_units(ALTITUDE_UNITS, 0)

    def update_data(self, data: TelemetryData):
        self._prev_altitude = self._altitude
        self._altitude = max(0.0, data.altitude)
        self.update()

    def _display_altitude(self) -> float:
        u = self.current_unit()
        if not u:
            return self._altitude
        return self._altitude * u.factor

    def _display_prev_altitude(self) -> float:
        u = self.current_unit()
        if not u:
            return self._prev_altitude
        return self._prev_altitude * u.factor

    # =========================================================================
    # SFONDO
    # =========================================================================

    def paint_background(self, painter: QPainter):
        w, h = self._prototype.width, self._prototype.height

        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(40, 40, 45))
        painter.drawRoundedRect(QRectF(1, 1, w - 2, h - 2), 8, 8)

        painter.setBrush(QColor(20, 22, 28))
        painter.drawRoundedRect(QRectF(4, 4, w - 8, h - 8), 5, 5)

    # =========================================================================
    # PRIMO PIANO
    # =========================================================================

    def paint_foreground(self, painter: QPainter):
        w, h = self._prototype.width, self._prototype.height
        cx, cy = w / 2, h / 2

        tape_top = 6
        tape_bottom = h - 6
        tape_cy = (tape_top + tape_bottom) / 2

        alt = self._display_altitude()
        prev_alt = self._display_prev_altitude()

        # =================================================================
        # NASTRO SCORREVOLE
        # =================================================================
        painter.save()

        clip = QPainterPath()
        clip.addRoundedRect(
            QRectF(5, tape_top, w - 10, tape_bottom - tape_top),
            4, 4
        )
        painter.setClipPath(clip)

        base_alt = int(alt / self._step) * self._step

        for offset in range(-5, 6):
            alt_value = base_alt + offset * self._step
            if alt_value < 0:
                continue

            y_pos = tape_cy - (alt_value - alt) / self._step * self._px_per_step

            if y_pos < tape_top - 16 or y_pos > tape_bottom + 16:
                continue

            distance = abs(offset)

            if distance <= 1:
                alpha = 200
                font_size = 12
            elif distance <= 2:
                alpha = 120
                font_size = 11
            else:
                alpha = 60
                font_size = 10

            painter.setPen(QColor(220, 220, 220, alpha))
            nf = painter.font()
            nf.setPixelSize(font_size)
            nf.setFamily("Consolas")
            painter.setFont(nf)

            painter.drawText(
                QRectF(4, y_pos - 7, w - 18, 14),
                Qt.AlignmentFlag.AlignCenter,
                str(int(alt_value))
            )

        painter.restore()

        # =================================================================
        # BOX NUMERO PRINCIPALE
        # =================================================================
        box_w = w - 14
        box_h = 32
        box_x = 7
        box_y = tape_cy - box_h / 2

        painter.setPen(QPen(QColor(200, 200, 200), 1))
        painter.setBrush(QBrush(QColor(35, 38, 45)))
        painter.drawRoundedRect(QRectF(box_x, box_y, box_w, box_h), 4, 4)

        painter.setPen(QColor(255, 255, 255))
        vf = painter.font()
        vf.setPixelSize(22)
        vf.setBold(True)
        vf.setFamily("Consolas")
        painter.setFont(vf)

        painter.drawText(
            QRectF(box_x, box_y, box_w, box_h),
            Qt.AlignmentFlag.AlignCenter,
            f"{int(alt)}"
        )

        # =================================================================
        # TRIANGOLO DIREZIONALE (colorato)
        # =================================================================
        delta = alt - prev_alt

        if abs(delta) > 0.5:
            tri_x = w - 11
            tri_y = tape_cy + 25
            tri_size = 5

            # Colore in base alla direzione
            if delta > 0.5:
                tri_color = QColor(100, 220, 120)    # verde (salita)
            elif delta < -0.5:
                tri_color = QColor(240, 130, 100)    # rosso-arancio (discesa)
            else:
                tri_color = QColor(255, 255, 255)    # bianco (neutro)

            tri = QPainterPath()
            if delta > 0:
                # Triangolo SU
                tri.moveTo(tri_x, tri_y - tri_size)
                tri.lineTo(tri_x - tri_size, tri_y + tri_size)
                tri.lineTo(tri_x + tri_size, tri_y + tri_size)
            else:
                # Triangolo GIÙ
                tri.moveTo(tri_x, tri_y + tri_size)
                tri.lineTo(tri_x - tri_size, tri_y - tri_size)
                tri.lineTo(tri_x + tri_size, tri_y - tri_size)

            tri.closeSubpath()
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(tri_color)
            painter.drawPath(tri)

class DigitalVSI(UnitButtonsMixin, BaseInstrument):
    """
    Variometro digitale compatto con:
    - Numero grande con segno
    - Nastro scorrevole
    - Triangolo direzionale
    - Cambio unità (FT/MIN / M/S)
    """

    def __init__(self, prototype, parent=None):
        super().__init__(prototype, parent)
        self._vsi = 0.0
        self._prev_vsi = 0.0
        self._px_per_step = 20.0
        self._step = 200.0       # passo del nastro in unità corrente
        self.init_units(VSI_UNITS, 0)
        self._apply_step()

    def _on_unit_changed(self):
        self._apply_step()
        super()._on_unit_changed()

    def _apply_step(self):
        u = self.current_unit()
        if not u:
            return
        # Passo del nastro: 200 fpm oppure 1 m/s
        self._step = 200.0 if u.unit_id == "fpm" else 1.0

    def update_data(self, data: TelemetryData):
        self._prev_vsi = self._vsi
        self._vsi = data.vertical_speed
        self.update()

    def _display_vsi(self) -> float:
        u = self.current_unit()
        if not u:
            return self._vsi
        return self._vsi * u.factor

    def _display_prev_vsi(self) -> float:
        u = self.current_unit()
        if not u:
            return self._prev_vsi
        return self._prev_vsi * u.factor

    # =========================================================================
    # SFONDO
    # =========================================================================

    def paint_background(self, painter: QPainter):
        w, h = self._prototype.width, self._prototype.height
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(40, 40, 45))
        painter.drawRoundedRect(QRectF(1, 1, w - 2, h - 2), 8, 8)
        painter.setBrush(QColor(20, 22, 28))
        painter.drawRoundedRect(QRectF(4, 4, w - 8, h - 8), 5, 5)

    # =========================================================================
    # PRIMO PIANO
    # =========================================================================

    def paint_foreground(self, painter: QPainter):
        w, h = self._prototype.width, self._prototype.height
        cx, cy = w / 2, h / 2
        tape_top = 6
        tape_bottom = h - 6
        tape_cy = (tape_top + tape_bottom) / 2
        vsi = self._display_vsi()
        prev_vsi = self._display_prev_vsi()

        # =================================================================
        # NASTRO SCORREVOLE
        # =================================================================
        painter.save()
        clip = QPainterPath()
        clip.addRoundedRect(QRectF(5, tape_top, w - 10, tape_bottom - tape_top), 4, 4)
        painter.setClipPath(clip)

        base_val = round(vsi / self._step) * self._step

        for offset in range(-5, 6):
            tape_value = base_val + offset * self._step
            y_pos = tape_cy - (tape_value - vsi) / self._step * self._px_per_step

            if y_pos < tape_top - 16 or y_pos > tape_bottom + 16:
                continue

            distance = abs(offset)
            if distance <= 1:
                alpha = 180
                font_size = 11
            elif distance <= 2:
                alpha = 110
                font_size = 10
            else:
                alpha = 55
                font_size = 9

            painter.setPen(QColor(220, 220, 220, alpha))
            nf = painter.font()
            nf.setPixelSize(font_size)
            nf.setFamily("Consolas")
            painter.setFont(nf)
            painter.drawText(
                QRectF(4, y_pos - 7, w - 18, 14),
                Qt.AlignmentFlag.AlignCenter,
                f"{int(tape_value)}"
            )

        painter.restore()

        # =================================================================
        # BOX NUMERO PRINCIPALE (con segno)
        # =================================================================
        box_w = w - 14
        box_h = 30
        box_x = 7
        box_y = tape_cy - box_h / 2

        painter.setPen(QPen(QColor(200, 200, 200), 1))
        painter.setBrush(QBrush(QColor(35, 38, 45)))
        painter.drawRoundedRect(QRectF(box_x, box_y, box_w, box_h), 4, 4)

        # Colore in base al segno
        if vsi > 10:
            text_color = QColor(100, 220, 120)   # verde (salita)
        elif vsi < -10:
            text_color = QColor(240, 130, 100)   # rosso-arancio (discesa)
        else:
            text_color = QColor(255, 255, 255)   # bianco (quasi zero)

        painter.setPen(text_color)
        vf = painter.font()
        vf.setPixelSize(18)
        vf.setBold(True)
        vf.setFamily("Consolas")
        painter.setFont(vf)

        sign = "+" if vsi >= 0 else ""
        painter.drawText(
            QRectF(box_x, box_y, box_w, box_h),
            Qt.AlignmentFlag.AlignCenter,
            f"{sign}{int(vsi)}"
        )

        # =================================================================
        # ETICHETTA UNITÀ (in basso)
        # =================================================================
        u = self.current_unit()
        painter.setPen(QColor(140, 150, 160))
        uf = painter.font()
        uf.setPixelSize(8)
        uf.setBold(False)
        painter.setFont(uf)
        painter.drawText(
            QRectF(0, h - 16, w, 12),
            Qt.AlignmentFlag.AlignCenter,
            u.label if u else ""
        )

        # =================================================================
        # TRIANGOLO DIREZIONALE
        # =================================================================
        if abs(vsi) > 10:
            tri_x = w - 11
            tri_y = tape_cy - 20
            tri_size = 5
            tri = QPainterPath()

            if vsi > 0:
                # Triangolo SU
                tri.moveTo(tri_x, tri_y - tri_size)
                tri.lineTo(tri_x - tri_size, tri_y + tri_size)
                tri.lineTo(tri_x + tri_size, tri_y + tri_size)
            else:
                # Triangolo GIÙ
                tri.moveTo(tri_x, tri_y + tri_size)
                tri.lineTo(tri_x - tri_size, tri_y - tri_size)
                tri.lineTo(tri_x + tri_size, tri_y - tri_size)

            tri.closeSubpath()
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(text_color)
            painter.drawPath(tri)

class RPMGauge(CircularGauge):
    def __init__(self, p, parent=None):
        super().__init__(p, parent)
        self._min_val=0; self._max_val=3000; self._major_step=500; self._minor_per_major=4; self._unit_label="RPM"
    def update_data(self, d): self._value = d.rpm; self.update()

class OilTempGauge(CircularGauge):
    def __init__(self, p, parent=None):
        super().__init__(p, parent)
        self._min_val=0; self._max_val=150; self._major_step=25; self._minor_per_major=4; self._unit_label="°C"
    def update_data(self, d): self._value = d.oil_temp; self.update()

class HeadingIndicator(BaseInstrument):
    def __init__(self, p, parent=None):
        super().__init__(p, parent); self._heading = 0.0
    def update_data(self, d): self._heading = d.heading % 360.0; self.update()

    def paint_background(self, p):
        th = self.theme()
        w, h = self._prototype.width, self._prototype.height
        cx, cy = w / 2, h / 2
        outer_r = min(cx, cy) - 4
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(th.bezel_color)
        p.drawEllipse(QPointF(cx, cy), outer_r, outer_r)
        p.setBrush(th.bezel_ring_color)
        p.drawEllipse(QPointF(cx, cy), outer_r - 3, outer_r - 3)
        dial_r = outer_r - 8
        p.setBrush(th.dial_color)
        p.drawEllipse(QPointF(cx, cy), dial_r, dial_r)

    def paint_foreground(self, p):
        th = self.theme()
        w, h = self._prototype.width, self._prototype.height
        cx, cy = w / 2, h / 2
        outer_r = min(cx, cy) - 4
        dial_r = outer_r - 8

        clip = QPainterPath()
        clip.addEllipse(QPointF(cx, cy), dial_r - 2, dial_r - 2)
        p.save(); p.setClipPath(clip)
        p.save(); p.translate(cx, cy); p.rotate(-self._heading)
        card_r = dial_r - 6

        for deg in range(0, 360, 5):
            if deg % 30 == 0:
                tl, tw, tc = 16, th.tick_major_width, th.tick_major_color
            elif deg % 10 == 0:
                tl, tw, tc = 12, th.tick_minor_width, th.tick_major_color
            else:
                tl, tw, tc = 8, th.tick_minor_width, th.tick_minor_color
            p.save(); p.rotate(deg)
            p.setPen(QPen(tc, tw))
            p.drawLine(QPointF(0, -card_r), QPointF(0, -card_r + tl))
            p.restore()

        num_r = card_r - 26
        for deg in range(0, 360, 30):
            if deg == 0: lb, ic = "N", True
            elif deg == 90: lb, ic = "E", True
            elif deg == 180: lb, ic = "S", True
            elif deg == 270: lb, ic = "W", True
            else: lb, ic = str(deg // 10), False
            p.save(); p.rotate(deg); p.translate(0, -num_r)
            p.setPen(th.text_color)
            nf = p.font()
            nf.setPixelSize(14 if ic else th.font_size_numbers)
            nf.setBold(ic)
            p.setFont(nf)
            p.drawText(QRectF(-12, -8, 24, 16), Qt.AlignmentFlag.AlignCenter, lb)
            p.restore()

        p.restore(); p.restore()

        # Lubber line
        p.save(); p.translate(cx, cy)
        lb2 = QPainterPath()
        lb2.moveTo(0, -dial_r + 3)
        lb2.lineTo(-6, -dial_r + 15)
        lb2.lineTo(6, -dial_r + 15)
        lb2.closeSubpath()
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(th.reference_color)
        p.drawPath(lb2)
        p.restore()

        # Simbolo aereo
        p.save(); p.translate(cx, cy)
        p.setPen(QPen(th.aircraft_symbol_color, 2))
        p.drawLine(QPointF(0, -12), QPointF(0, 12))
        p.drawLine(QPointF(-14, -2), QPointF(14, -2))
        p.drawLine(QPointF(-6, 9), QPointF(6, 9))
        p.restore()

class AttitudeIndicator(BaseInstrument):
    def __init__(self, p, parent=None):
        super().__init__(p, parent); self._pitch=0.0; self._roll=0.0
    def update_data(self, d): self._pitch=d.pitch; self._roll=d.roll; self.update()
    def paint_background(self, p):
        th = self.theme()
        w, h = self._prototype.width, self._prototype.height
        cx, cy = w / 2, h / 2
        outer_r = min(cx, cy) - 4
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(th.bezel_color)
        p.drawEllipse(QPointF(cx, cy), outer_r, outer_r)
        p.setBrush(th.dial_color)
        p.drawEllipse(QPointF(cx, cy), outer_r - 6, outer_r - 6)

    def paint_foreground(self, p):
        th = self.theme()
        w, h = self._prototype.width, self._prototype.height
        cx, cy = w / 2, h / 2
        radius = min(cx, cy) - 12

        clip = QPainterPath()
        clip.addEllipse(QPointF(cx, cy), radius, radius)
        p.save()
        p.setClipPath(clip)
        p.translate(cx, cy)
        p.rotate(-self._roll)
        ppx = self._pitch * 2.5

        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(th.sky_color)
        p.drawRect(QRectF(-radius * 2, -radius * 2 + ppx, radius * 4, radius * 2))
        p.setBrush(th.ground_color)
        p.drawRect(QRectF(-radius * 2, ppx, radius * 4, radius * 2))

        p.setPen(QPen(th.horizon_color, 2))
        p.drawLine(QPointF(-radius, ppx), QPointF(radius, ppx))

        p.setPen(QPen(th.pitch_ladder_color, 1))
        for deg in [-20, -10, 10, 20]:
            yo = ppx - deg * 2.5
            hw = 20 if deg % 20 == 0 else 14
            p.drawLine(QPointF(-hw, yo), QPointF(hw, yo))
        p.restore()

        # Simbolo aereo
        p.save()
        p.translate(cx, cy)
        p.setPen(QPen(th.aircraft_symbol_color, 3))
        p.drawLine(QPointF(-28, 0), QPointF(-10, 0))
        p.drawLine(QPointF(10, 0), QPointF(28, 0))
        p.setBrush(th.aircraft_symbol_color)
        p.setPen(Qt.PenStyle.NoPen)
        p.drawEllipse(QPointF(0, 0), 3, 3)
        p.restore()

        # Triangolo riferimento
        p.save()
        p.translate(cx, cy)
        tri = QPainterPath()
        tri.moveTo(0, -radius + 2)
        tri.lineTo(-5, -radius + 10)
        tri.lineTo(5, -radius + 10)
        tri.closeSubpath()
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(th.aircraft_symbol_color)
        p.drawPath(tri)
        p.restore()


class AttitudeIndicatorFull(BaseInstrument):
    """
    Orizzonte artificiale completo con:
    - Scala beccheggio (tacche ogni 5°, numeri ogni 10°)
    - Scala rollio (0°, ±10°, ±20°, ±30°, ±45°, ±60°)
    - Puntatore rollio mobile
    - Simbolo aereo fisso
    """

    def __init__(self, prototype, parent=None):
        super().__init__(prototype, parent)
        self._pitch = 0.0
        self._roll = 0.0
        self._px_per_deg = 3.0

    def update_data(self, data: TelemetryData):
        self._pitch = data.pitch
        self._roll = data.roll
        self.update()

    # =========================================================================
    # SFONDO STATICO
    # =========================================================================

    def paint_background(self, painter: QPainter):
        th = self.theme()
        w, h = self._prototype.width, self._prototype.height
        cx, cy = w / 2, h / 2
        outer_r = min(cx, cy) - 4

        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(th.bezel_color)
        painter.drawEllipse(QPointF(cx, cy), outer_r, outer_r)
        painter.setBrush(th.bezel_ring_color)
        painter.drawEllipse(QPointF(cx, cy), outer_r - 4, outer_r - 4)
        dial_r = outer_r - 8
        painter.setBrush(th.dial_color)
        painter.drawEllipse(QPointF(cx, cy), dial_r, dial_r)

        roll_marks = [0, 10, 20, 30, 45, 60]
        tick_r = dial_r - 2
        for angle in roll_marks:
            signs = [1] if angle == 0 else [1, -1]
            for sign in signs:
                deg = angle * sign
                painter.save()
                painter.translate(cx, cy)
                painter.rotate(deg)
                if angle == 0:
                    tick_len, tick_w = 12, th.tick_major_width
                elif angle in (10, 20, 30):
                    tick_len, tick_w = 10, th.tick_minor_width
                else:
                    tick_len, tick_w = 12, th.tick_minor_width
                painter.setPen(QPen(th.tick_major_color, tick_w))
                painter.drawLine(QPointF(0, -tick_r), QPointF(0, -tick_r + tick_len))
                painter.restore()

    def paint_foreground(self, painter: QPainter):
        th = self.theme()
        w, h = self._prototype.width, self._prototype.height
        cx, cy = w / 2, h / 2
        outer_r = min(cx, cy) - 4
        dial_r = outer_r - 8
        sphere_r = dial_r - 16

        if sphere_r <= 0:
            return

        painter.save()
        clip = QPainterPath()
        clip.addEllipse(QPointF(cx, cy), sphere_r, sphere_r)
        painter.setClipPath(clip)
        painter.translate(cx, cy)
        painter.rotate(-self._roll)

        pitch_offset = self._pitch * self._px_per_deg

        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(th.sky_color)
        painter.drawRect(QRectF(-sphere_r * 2, -sphere_r * 2 + pitch_offset,
                                sphere_r * 4, sphere_r * 2))
        painter.setBrush(th.ground_color)
        painter.drawRect(QRectF(-sphere_r * 2, pitch_offset,
                                sphere_r * 4, sphere_r * 2))

        painter.setPen(QPen(th.horizon_color, 2))
        painter.drawLine(QPointF(-sphere_r, pitch_offset),
                         QPointF(sphere_r, pitch_offset))

        pf = painter.font()
        pf.setPixelSize(th.font_size_unit)
        painter.setFont(pf)

        for deg in range(-30, 35, 5):
            if deg == 0:
                continue
            y_pos = pitch_offset - deg * self._px_per_deg
            if deg % 10 == 0:
                half_w = 30
                draw_number = True
            else:
                half_w = 18
                draw_number = False

            painter.setPen(QPen(th.pitch_ladder_color, 1))
            painter.drawLine(QPointF(-half_w, y_pos), QPointF(half_w, y_pos))

            if draw_number:
                label = str(abs(deg))
                painter.setPen(th.pitch_ladder_color)
                painter.drawText(QRectF(-half_w - 22, y_pos - 6, 20, 12),
                                 Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter,
                                 label)
                painter.drawText(QRectF(half_w + 2, y_pos - 6, 20, 12),
                                 Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
                                 label)

        painter.restore()

        # Puntatore rollio
        painter.save()
        painter.translate(cx, cy)
        painter.rotate(-self._roll)
        ptr_r = sphere_r + 4
        ptr = QPainterPath()
        ptr.moveTo(0, -ptr_r)
        ptr.lineTo(-6, -ptr_r + 12)
        ptr.lineTo(6, -ptr_r + 12)
        ptr.closeSubpath()
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(th.needle_color)
        painter.drawPath(ptr)
        painter.restore()

        # Riferimento fisso
        painter.save()
        painter.translate(cx, cy)
        ref_r = sphere_r + 4
        ref = QPainterPath()
        ref.moveTo(0, -ref_r + 14)
        ref.lineTo(-5, -ref_r + 2)
        ref.lineTo(5, -ref_r + 2)
        ref.closeSubpath()
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(th.reference_color)
        painter.drawPath(ref)
        painter.restore()

        # Simbolo aereo
        painter.save()
        painter.translate(cx, cy)
        painter.setPen(QPen(th.aircraft_symbol_color, 3))
        painter.drawLine(QPointF(-30, 0), QPointF(-12, 0))
        painter.drawLine(QPointF(12, 0), QPointF(30, 0))
        painter.drawLine(QPointF(-30, 0), QPointF(-30, 5))
        painter.drawLine(QPointF(30, 0), QPointF(30, 5))
        painter.setBrush(th.aircraft_symbol_color)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(QPointF(0, 0), 3, 3)
        painter.restore()


class AttitudeIndicatorSquare(BaseInstrument):
    """
    Orizzonte artificiale quadrato con comportamento circolare:
    - 0°: orizzonte normale (cielo sopra, terra sotto)
    - +90°: tutto cielo
    - +180°: orizzonte invertito (terra sopra, cielo sotto)
    - -90°: tutta terra
    - -180°: orizzonte invertito (cielo sopra, terra sotto)
    - Linee orizzonte sia a 0° che a 180°
    """

    def __init__(self, prototype, parent=None):
        super().__init__(prototype, parent)
        self._pitch = 0.0
        self._roll = 0.0
        self._px_per_deg = 2.5

    def update_data(self, data: TelemetryData):
        self._pitch = data.pitch
        self._roll = data.roll
        self.update()

    def paint_background(self, painter: QPainter):
        th = self.theme()
        w, h = self._prototype.width, self._prototype.height
        margin = 4
        corner = 12

        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(th.bezel_color)
        painter.drawRoundedRect(QRectF(margin, margin, w - 2 * margin, h - 2 * margin),
                                corner, corner)
        m2 = margin + 4
        painter.setBrush(th.bezel_ring_color)
        painter.drawRoundedRect(QRectF(m2, m2, w - 2 * m2, h - 2 * m2),
                                corner - 2, corner - 2)
        m3 = margin + 8
        painter.setBrush(th.dial_color)
        painter.drawRoundedRect(QRectF(m3, m3, w - 2 * m3, h - 2 * m3),
                                corner - 4, corner - 4)

    def paint_foreground(self, painter: QPainter):
        th = self.theme()
        w, h = self._prototype.width, self._prototype.height
        cx, cy = w / 2, h / 2
        dial_margin = 12
        dial_w = w - 2 * dial_margin
        dial_h = h - 2 * dial_margin

        if dial_w <= 0 or dial_h <= 0:
            return

        norm_pitch = ((self._pitch + 180.0) % 360.0) - 180.0

        painter.save()
        clip = QPainterPath()
        clip.addRoundedRect(QRectF(dial_margin, dial_margin, dial_w, dial_h), 8, 8)
        painter.setClipPath(clip)
        painter.translate(cx, cy)
        painter.rotate(-self._roll)

        ppd = self._px_per_deg
        pitch_offset = norm_pitch * ppd
        large = max(w, h) * 3

        h0 = pitch_offset
        half_period = 180.0 * ppd
        if norm_pitch >= 0:
            h_sec = h0 - half_period
        else:
            h_sec = h0 + half_period

        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(th.sky_color)
        painter.drawRect(QRectF(-large, -large, large * 2, large + h0))
        painter.setBrush(th.ground_color)
        painter.drawRect(QRectF(-large, h0, large * 2, large))

        if norm_pitch >= 0 and h_sec > -large:
            painter.setBrush(th.ground_color)
            painter.drawRect(QRectF(-large, -large, large * 2, large + h_sec))
        elif norm_pitch < 0 and h_sec < large:
            painter.setBrush(th.sky_color)
            painter.drawRect(QRectF(-large, h_sec, large * 2, large))

        painter.setPen(QPen(th.horizon_color, 2))
        painter.drawLine(QPointF(-large, h0), QPointF(large, h0))

        if -large < h_sec < large:
            painter.setPen(QPen(th.horizon_color, 2))
            painter.drawLine(QPointF(-large, h_sec), QPointF(large, h_sec))

        pf = painter.font()
        pf.setPixelSize(th.font_size_unit)
        painter.setFont(pf)

        for deg in range(-170, 175, 5):
            if deg == 0:
                continue
            y_pos = pitch_offset - deg * ppd
            if deg % 10 == 0:
                half_w = 28
                draw_number = True
            else:
                half_w = 16
                draw_number = False

            painter.setPen(QPen(th.pitch_ladder_color, 1))
            painter.drawLine(QPointF(-half_w, y_pos), QPointF(half_w, y_pos))

            if draw_number:
                label = str(abs(deg))
                painter.setPen(th.pitch_ladder_color)
                painter.drawText(QRectF(-half_w - 24, y_pos - 6, 22, 12),
                                 Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter,
                                 label)
                painter.drawText(QRectF(half_w + 2, y_pos - 6, 22, 12),
                                 Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
                                 label)

        for deg in [-90, 90]:
            y_pos = pitch_offset - deg * ppd
            painter.setPen(QPen(th.reference_color, 2))
            painter.drawLine(QPointF(-40, y_pos), QPointF(40, y_pos))

        painter.restore()

        # Arco rollio
        arc_r = min(dial_w, dial_h) / 2 - 8
        painter.save()
        painter.translate(cx, cy)
        painter.setPen(QPen(th.tick_minor_color, 1))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        arc_rect = QRectF(-arc_r, -arc_r, arc_r * 2, arc_r * 2)
        painter.drawArc(arc_rect, 20 * 16, 140 * 16)
        painter.restore()

        roll_marks = [0, 10, 20, 30, 45, 60]
        for angle in roll_marks:
            signs = [1] if angle == 0 else [1, -1]
            for sign in signs:
                deg = angle * sign
                painter.save()
                painter.translate(cx, cy)
                painter.rotate(deg)
                if angle == 0:
                    tick_len, tick_w = 14, th.tick_major_width
                    tick_color = th.tick_major_color
                elif angle in (10, 20, 30):
                    tick_len, tick_w = 10, th.tick_minor_width
                    tick_color = th.tick_major_color
                else:
                    tick_len, tick_w = 12, th.tick_minor_width
                    tick_color = th.tick_major_color
                painter.setPen(QPen(tick_color, tick_w))
                painter.drawLine(QPointF(0, -arc_r), QPointF(0, -arc_r + tick_len))
                painter.restore()

        # Puntatore rollio
        painter.save()
        painter.translate(cx, cy)
        painter.rotate(-self._roll)
        ptr_r = arc_r - 16
        ptr = QPainterPath()
        ptr.moveTo(0, -ptr_r)
        ptr.lineTo(-6, -ptr_r + 12)
        ptr.lineTo(6, -ptr_r + 12)
        ptr.closeSubpath()
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(th.needle_color)
        painter.drawPath(ptr)
        painter.restore()

        # Riferimento fisso
        painter.save()
        painter.translate(cx, cy)
        ref_r = arc_r - 16
        ref = QPainterPath()
        ref.moveTo(0, -ref_r + 14)
        ref.lineTo(-5, -ref_r + 2)
        ref.lineTo(5, -ref_r + 2)
        ref.closeSubpath()
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(th.reference_color)
        painter.drawPath(ref)
        painter.restore()

        # Simbolo aereo
        painter.save()
        painter.translate(cx, cy)
        painter.setPen(QPen(th.aircraft_symbol_color, 3))
        painter.drawLine(QPointF(-30, 0), QPointF(-12, 0))
        painter.drawLine(QPointF(12, 0), QPointF(30, 0))
        painter.drawLine(QPointF(-30, 0), QPointF(-30, 5))
        painter.drawLine(QPointF(30, 0), QPointF(30, 5))
        painter.setBrush(th.aircraft_symbol_color)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(QPointF(0, 0), 3, 3)
        painter.restore()