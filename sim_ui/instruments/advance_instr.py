from __future__ import annotations
import math
from PySide6.QtCore import Qt, QPointF, QRectF
from PySide6.QtGui import (
    QBrush, QColor, QPainter, QPainterPath, QPen,
    QLinearGradient, QRadialGradient, QFont,
)
from .base import BaseInstrument, UnitButtonsMixin
from ..core.telemetry import TelemetryData
from ..core.units import AIRSPEED_UNITS, ALTITUDE_UNITS, unit_index

# =============================================================================
# GARMIN GI 275 — ATTITUDE INDICATOR AVANZATO (High Fidelity Style)
# =============================================================================
class AttitudeAdvance(UnitButtonsMixin, BaseInstrument):
    """
    Orizzonte artificiale avanzato ispirato al Garmin GI 275:
    - Display rettangolare con angoli arrotondati
    - Sfera cielo/terra con gradienti realistici
    - Scala beccheggio numerata (tacche 5°, numeri 10°)
    - Arco rollio con tacche (0, ±10, ±20, ±30, ±45, ±60)
    - Puntatore rollio ambra
    - Simbolo aereo fisso (chevron)
    - Indicatore slip/skid
    - Tape velocità (airspeed) a sinistra con archi operativi
    - Readout digitali pitch, roll e airspeed
    """

    # --- Archi operativi velocità (valori generici, regolabili) ---
    _VS0 = 40    # Stall speed flaps down (inizio arco bianco)
    _VS1 = 50    # Stall speed flaps up (inizio arco verde)
    _VNO = 120   # Max structural cruising speed (fine verde / inizio giallo)
    _VNE = 160   # Never exceed speed (linea rossa)

    # --- Passi tacche tape per unità: (minor, major) in unità visualizzate ---
    _TAPE_STEPS = {
        "KNOTS": (5.0, 10.0),
        "KM/H":  (10.0, 20.0),
        "MPH":   (5.0, 10.0),
        "M/S":   (2.5, 5.0),
    }

    def _tape_steps(self):
        u = self.current_unit()
        label = u.label if u else "KNOTS"
        return self._TAPE_STEPS.get(label, (5.0, 10.0))

    def __init__(self, prototype, parent=None):
        super().__init__(prototype, parent)
        self._pitch = 0.0
        self._roll = 0.0
        self._turn_rate = 0.0
        self._airspeed = 0.0
        self._px_per_deg = 3.5   # pixel per grado di beccheggio
        self._px_per_kt = 2.2    # pixel per nodo di velocità
        self.init_units(AIRSPEED_UNITS, unit_index(AIRSPEED_UNITS, "M/S"))

    def update_data(self, data: TelemetryData):
        self._pitch = data.pitch
        self._roll = data.roll
        self._turn_rate = getattr(data, "turn_rate", 0.0)
        self._airspeed = getattr(data, "airspeed", 0.0)
        self.update()

    # =========================================================================
    # PULSANTI UNITÀ — riposizionati in alto a sinistra
    # =========================================================================

    def unit_round_button_rect(self) -> QRectF:
        br = self.boundingRect()
        size = 16.0
        return QRectF(br.left() + 6.0, br.top() + 6.0, size, size)

    def unit_menu_button_rect(self) -> QRectF:
        r = self.unit_round_button_rect()
        w = 12.0
        return QRectF(r.center().x() - w / 2, r.bottom() + 4.0, w, 8.0)



    # =========================================================================
    # GEOMETRIA COMUNI
    # =========================================================================
    def _display_rect(self):
        w, h = self._prototype.width, self._prototype.height
        m = 10
        return QRectF(m, m, w - 2 * m, h - 2 * m)

    # =========================================================================
    # SFONDO STATICO (Bezel e Cornice)
    # =========================================================================
    def paint_background(self, p: QPainter):
        p.setRenderHints(QPainter.RenderHint.Antialiasing | 
                         QPainter.RenderHint.TextAntialiasing | 
                         QPainter.RenderHint.SmoothPixmapTransform)

        w, h = self._prototype.width, self._prototype.height
        corner = 16

        # --- Bezel esterno con gradiente ---
        bezel_grad = QRadialGradient(w / 2, h / 2, max(w, h) / 1.5)
        bezel_grad.setColorAt(0.0, QColor(60, 60, 65))
        bezel_grad.setColorAt(0.8, QColor(30, 30, 35))
        bezel_grad.setColorAt(1.0, QColor(15, 15, 18))
        
        p.setPen(QPen(QColor(80, 80, 85), 1))
        p.setBrush(QBrush(bezel_grad))
        p.drawRoundedRect(QRectF(2, 2, w - 4, h - 4), corner, corner)

        # --- Cornice display interna ---
        m3 = 10
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QColor(5, 5, 8))
        p.drawRoundedRect(QRectF(m3, m3, w - 2 * m3, h - 2 * m3), corner - 4, corner - 4)

        # --- Etichetta modo "ATT" ---
        p.setPen(QColor(0, 220, 120))
        lf = p.font()
        lf.setPixelSize(10)
        lf.setBold(True)
        p.setFont(lf)
        p.drawText(QRectF(w - m3 - 48, m3 + 6, 40, 14),
                   Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter, "ATT")

    # =========================================================================
    # PRIMO PIANO DINAMICO
    # =========================================================================
    def paint_foreground(self, p: QPainter):
        w, h = self._prototype.width, self._prototype.height
        cx, cy = w / 2, h / 2
        disp = self._display_rect()
        corner = 12
        att_r = (min(w, h) / 2) - 20

        # =====================================================================
        # 1. SFERA CIELO/TERRA + SCALA BECCHEGGIO (clippata al display)
        # =====================================================================
        p.save()
        clip = QPainterPath()
        clip.addRoundedRect(disp, corner, corner)
        p.setClipPath(clip)
        p.translate(cx, cy)
        p.rotate(-self._roll)
        pitch_offset = self._pitch * self._px_per_deg
        large = max(w, h) * 2

        # Cielo
        sky_grad = QLinearGradient(0, -large + pitch_offset, 0, pitch_offset)
        sky_grad.setColorAt(0.0, QColor(10, 40, 100))
        sky_grad.setColorAt(0.7, QColor(40, 110, 200))
        sky_grad.setColorAt(1.0, QColor(80, 150, 230))
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QBrush(sky_grad))
        p.drawRect(QRectF(-large, -large + pitch_offset, large * 2, large))

        # Terra
        gnd_grad = QLinearGradient(0, pitch_offset, 0, large + pitch_offset)
        gnd_grad.setColorAt(0.0, QColor(140, 90, 40))
        gnd_grad.setColorAt(0.3, QColor(100, 60, 20))
        gnd_grad.setColorAt(1.0, QColor(50, 30, 10))
        p.setBrush(QBrush(gnd_grad))
        p.drawRect(QRectF(-large, pitch_offset, large * 2, large))

        # Linea orizzonte
        p.setPen(QPen(QColor(255, 255, 255), 2.5))
        p.drawLine(QPointF(-large, pitch_offset), QPointF(large, pitch_offset))

        # --- Scala beccheggio ---
        pf = p.font()
        pf.setPixelSize(11)
        pf.setBold(True)
        p.setFont(pf)

        for deg in range(-30, 35, 5):
            if deg == 0:
                continue
            y = pitch_offset - deg * self._px_per_deg
            
            if deg % 10 == 0:
                half_w = 35
                pen_style = Qt.PenStyle.SolidLine
                is_numbered = True
            else:
                half_w = 18
                pen_style = Qt.PenStyle.DashLine
                is_numbered = False

            p.setPen(QPen(QColor(255, 255, 255), 2.0, pen_style))
            p.drawLine(QPointF(-half_w, y), QPointF(half_w, y))

            if is_numbered:
                label = str(abs(deg))
                p.setPen(QColor(255, 255, 255))
                p.drawText(QRectF(-half_w - half_w/2, y - 8, 20, 16),
                           Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, label)
                p.drawText(QRectF(half_w + half_w/2-20, y - 8, 20, 16),
                           Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter, label)
        p.restore()

        # =====================================================================
        # 2. ARCO ROLLIO (fisso, sopra la sfera)
        # =====================================================================
        p.save()
        p.setPen(QPen(QColor(255, 255, 255), 2.0))
        p.setBrush(Qt.BrushStyle.NoBrush)
        arc_rect = QRectF(cx - att_r, cy - att_r, att_r * 2, att_r * 2)
        p.drawArc(arc_rect, 30 * 16, 120 * 16)

        roll_marks = [0, 10, 20, 30, 45, 60]
        for angle in roll_marks:
            signs = [1] if angle == 0 else [1, -1]
            for sign in signs:
                deg = angle * sign
                p.save()
                p.translate(cx, cy)
                p.rotate(deg)
                
                if angle == 0:
                    tl, tw = 14, 3.0
                elif angle in (10, 20, 30):
                    tl, tw = 10, 2.0
                else:
                    tl, tw = 12, 2.0
                    
                p.setPen(QPen(QColor(255, 255, 255), tw))
                p.drawLine(QPointF(0, -att_r), QPointF(0, -att_r + tl))
                p.restore()
        p.restore()

        # Riferimento zero rollio
        p.save()
        p.translate(cx, cy)
        zero = QPainterPath()
        zero.moveTo(0, -att_r + 16)
        zero.lineTo(-6, -att_r + 2)
        zero.lineTo(6, -att_r + 2)
        zero.closeSubpath()
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QColor(255, 255, 255))
        p.drawPath(zero)
        p.restore()

        # =====================================================================
        # 3. PUNTATORE ROLLIO (ambra, ruota con il roll)
        # =====================================================================
        p.save()
        p.translate(cx, cy)
        p.rotate(self._roll)
        ptr = QPainterPath()
        ptr.moveTo(0, -att_r + 18)
        ptr.lineTo(-7, -att_r + 32)
        ptr.lineTo(7, -att_r + 32)
        ptr.closeSubpath()
        
        p.setPen(QPen(QColor(180, 120, 0), 1.5))
        p.setBrush(QColor(255, 180, 0))
        p.drawPath(ptr)
        p.restore()

        # =====================================================================
        # 4. SIMBOLO AEREO (Chevron ambra)
        # =====================================================================
        p.save()
        p.translate(cx, cy)
        
        sym_color = QColor(255, 180, 0)
        p.setPen(QPen(sym_color, 3.5, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin))
        p.setBrush(Qt.BrushStyle.NoBrush)

        wings = QPainterPath()
        wing_span = att_r * 0.45
        wing_drop = att_r * 0.08
        center_gap = att_r * 0.12
        
        wings.moveTo(-center_gap, 0)
        wings.lineTo(-wing_span, wing_drop)
        wings.moveTo(center_gap, 0)
        wings.lineTo(wing_span, wing_drop)
        
        p.drawPath(wings)

        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(sym_color)
        p.drawEllipse(QPointF(0, 0), 4, 4)
        p.restore()

        # =====================================================================
        # 5. TAPE VELOCITÀ (Airspeed) - Lato sinistro
        # =====================================================================
        self._draw_airspeed_tape(p, disp, cy)

        # =====================================================================
        # 6. SLIP/SKID
        # =====================================================================
        coordinated_rate = self._roll * 0.16
        slip_skid = self._turn_rate - coordinated_rate
        slip_px = max(-20, min(20, slip_skid * 4.0))

        p.save()
        p.translate(cx, cy)
        
        track_rect = QRectF(-24, att_r * 0.18, 48, 8)
        p.setPen(QPen(QColor(255, 255, 255), 1.5))
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawRoundedRect(track_rect, 3, 3)

        skid_rect = QRectF(slip_px - 6, att_r * 0.18 + 1, 12, 6)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QColor(20, 20, 20))
        p.drawRoundedRect(skid_rect, 2, 2)
        p.restore()

        # =====================================================================
        # 7. READOUT DIGITALI (Pitch e Roll in basso)
        # =====================================================================
        self._draw_readout(p, disp.left() + 17, disp.bottom() - 30, "Pitch", self._pitch)
        self._draw_readout(p, disp.right() - 73, disp.bottom() - 30, "Roll", self._roll)

    # =========================================================================
    # TAPE VELOCITÀ (Airspeed Tape) - Integrata nel bordo sinistro
    # =========================================================================
    # def _draw_airspeed_tape(self, p: QPainter, disp: QRectF, cy: float):
    #     """Disegna la tape della velocità integrata nel bordo sinistro stile GI 275."""
    #     tape_w = 28 
    #     tape_h = disp.height() * 0.35 # Altezza numeri che scorrono
    #     tape_x = disp.left()        # Posizione x
    #     tape_y = cy - tape_h / 2 -4   # Posizione y
        
    #     tape_rect = QRectF(tape_x, tape_y, tape_w, tape_h)
        
    #     # --- Sfondo tape (nero solido, integrato nel display) ---
    #     p.save()
    #     p.setPen(Qt.PenStyle.NoPen)  # Nessun bordo visibile
    #     p.setBrush(QBrush(QColor(8, 8, 10, 150)))  # Scuro trasparente
    #     p.drawRect(tape_rect)  # Rettangolo semplice, non arrotondato
        
    #     # --- Clipping per evitare overflow ---
    #     clip_path = QPainterPath()
    #     clip_path.addRect(tape_rect)
    #     p.setClipPath(clip_path)
        
    #     # --- Archi operativi colorati (lato destro della tape) ---
    #     arc_w = 3  
    #     arc_x = tape_x + tape_w - arc_w - 1
        
    #     # Bianco (VS0 to VNO)
    #     white_top = cy - (self._VNO - self._airspeed) * self._px_per_kt
    #     white_bot = cy - (self._VS0 - self._airspeed) * self._px_per_kt
    #     p.setPen(Qt.PenStyle.NoPen)
    #     p.setBrush(QColor(255, 255, 255, 180))
    #     p.drawRect(QRectF(arc_x, white_top, arc_w, white_bot - white_top))
        
    #     # Verde (VS1 to VNO)
    #     green_top = cy - (self._VNO - self._airspeed) * self._px_per_kt
    #     green_bot = cy - (self._VS1 - self._airspeed) * self._px_per_kt
    #     p.setBrush(QColor(0, 220, 120, 180))
    #     p.drawRect(QRectF(arc_x, green_top, arc_w, green_bot - green_top))
        
    #     # Giallo (VNO to VNE)
    #     yellow_top = cy - (self._VNE - self._airspeed) * self._px_per_kt
    #     yellow_bot = cy - (self._VNO - self._airspeed) * self._px_per_kt
    #     p.setBrush(QColor(255, 200, 0, 180))
    #     p.drawRect(QRectF(arc_x, yellow_top, arc_w, yellow_bot - yellow_top))
        
    #     # Linea rossa a VNE messa dopo
        
    #     # --- Tacche e numeri ---
    #     min_kt = int(self._airspeed - 50)
    #     max_kt = int(self._airspeed + 50)
    #     min_kt = max(0, min_kt - (min_kt % 10))
    #     max_kt = max_kt + (10 - max_kt % 10)
        
    #     pf = p.font()
    #     pf.setPixelSize(8)  # Ridotto da 12 a 11
    #     pf.setBold(True)
    #     pf.setFamily("Consolas")
    #     p.setFont(pf)
        
    #     for kt in range(min_kt, max_kt + 1, 5):
    #         y = cy - (kt - self._airspeed) * self._px_per_kt
            
    #         if kt % 10 == 0:
    #             tick_len = 8  # Ridotto da 10 a 8
    #             p.setPen(QPen(QColor(255, 255, 255), 1.8))
    #             p.drawLine(QPointF(tape_x + tape_w - 6, y), 
    #                       QPointF(tape_x + tape_w - 3, y))
                
    #             # Numero (posizionato più a sinistra per stare nella tape più stretta)
    #             p.setPen(QColor(255, 255, 255))
    #             p.drawText(QRectF(tape_x + 6, y - 7, tape_w - 14, 14),
    #                       Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter,
    #                       str(kt))
    #         else:
    #             tick_len = 5  # Ridotto da 6 a 5
    #             p.setPen(QPen(QColor(200, 200, 200), 1.2))
    #             p.drawLine(QPointF(tape_x + tape_w - 4, y), 
    #                       QPointF(tape_x + tape_w - 2, y))


    #     # Linea rossa a VNE
    #     vne_y = cy - (self._VNE - self._airspeed) * self._px_per_kt
    #     p.setPen(QPen(QColor(255, 50, 50), 2.0))
    #     p.drawLine(QPointF(arc_x - 4, vne_y), QPointF(arc_x + arc_w + 1, vne_y))   
        
    #     p.restore()
        
    #     # --- Readout digitale centrale (ridimensionato per tape più stretta) ---
    #     readout_w = 34 
    #     readout_h = 20  # Ridotto da 22 a 20
    #     readout_x = tape_x + (tape_w - readout_w) / 2
    #     readout_y = cy - readout_h / 2
        
    #     # Sfondo nero con bordo ambra
    #     p.setPen(QPen(QColor(255, 180, 0), 1.8))  # Bordo più sottile
    #     p.setBrush(QBrush(QColor(5, 5, 8, 240)))
    #     p.drawRoundedRect(QRectF(readout_x, readout_y, readout_w, readout_h), 3, 3)
        
    #     # Valore velocità
    #     vf = p.font()
    #     vf.setPixelSize(12)  # Ridotto da 14 a 13
    #     vf.setBold(True)
    #     vf.setFamily("Consolas")
    #     p.setFont(vf)
    #     p.setPen(QColor(255, 255, 255))
    #     p.drawText(QRectF(readout_x, readout_y, readout_w, readout_h),
    #               Qt.AlignmentFlag.AlignCenter,
    #               f"{self._airspeed:.0f}")

    def _draw_airspeed_tape(self, p: QPainter, disp: QRectF, cy: float):
        """Tape velocità con supporto cambio unità (KNOTS/KM-H/MPH/M-S)."""
        u = self.current_unit()
        factor = u.factor if u else 1.0
        # Scala inversamente proporzionale al fattore: la tape mostra
        # sempre lo stesso intervallo FISICO di velocità, solo rinumerato
        px_per_unit = self._px_per_kt / factor
        speed = self._airspeed * factor
        minor_step, major_step = self._tape_steps()
        ratio = int(round(major_step / minor_step))

        tape_w = 28
        tape_h = disp.height() * 0.35
        tape_x = disp.left()
        tape_y = cy - tape_h / 2 - 4
        tape_rect = QRectF(tape_x, tape_y, tape_w, tape_h)

        def v_y(v_base: float) -> float:
            """Posizione y di una velocità espressa in nodi (unità base)."""
            return cy - (v_base * factor - speed) * px_per_unit

        # --- Sfondo tape ---
        p.save()
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QBrush(QColor(8, 8, 10, 150)))
        p.drawRect(tape_rect)

        clip_path = QPainterPath()
        clip_path.addRect(tape_rect)
        p.setClipPath(clip_path)

        # --- Archi operativi (V-speed convertite automaticamente) ---
        arc_w = 3
        arc_x = tape_x + tape_w - arc_w - 1

        # Bianco (VS0 → VNO)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QColor(255, 255, 255, 180))
        p.drawRect(QRectF(arc_x, v_y(self._VNO), arc_w,
                          v_y(self._VS0) - v_y(self._VNO)))

        # Verde (VS1 → VNO)
        p.setBrush(QColor(0, 220, 120, 180))
        p.drawRect(QRectF(arc_x, v_y(self._VNO), arc_w,
                          v_y(self._VS1) - v_y(self._VNO)))

        # Giallo (VNO → VNE)
        p.setBrush(QColor(255, 200, 0, 180))
        p.drawRect(QRectF(arc_x, v_y(self._VNE), arc_w,
                          v_y(self._VNO) - v_y(self._VNE)))

        # --- Tacche e numeri ---
        pf = p.font()
        pf.setPixelSize(8)
        pf.setBold(True)
        pf.setFamily("Consolas")
        p.setFont(pf)

        half_range = (tape_h / 2) / px_per_unit + major_step
        start_i = int(math.floor((speed - half_range) / minor_step))
        end_i = int(math.ceil((speed + half_range) / minor_step))

        for i in range(start_i, end_i + 1):
            v = i * minor_step
            if v < 0:
                continue
            y = cy - (v - speed) * px_per_unit

            if i % ratio == 0:
                # Tacca maggiore + numero
                p.setPen(QPen(QColor(255, 255, 255), 1.8))
                p.drawLine(QPointF(tape_x + tape_w - 6, y),
                           QPointF(tape_x + tape_w - 3, y))
                p.setPen(QColor(255, 255, 255))
                p.drawText(QRectF(tape_x + 2, y - 7, tape_w - 10, 14),
                           Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter,
                           f"{v:.0f}")
            else:
                # Tacca minore
                p.setPen(QPen(QColor(200, 200, 200), 1.2))
                p.drawLine(QPointF(tape_x + tape_w - 4, y),
                           QPointF(tape_x + tape_w - 2, y))

        # --- Linea rossa VNE ---
        vne_y = v_y(self._VNE)
        p.setPen(QPen(QColor(255, 50, 50), 2.0))
        p.drawLine(QPointF(arc_x - 4, vne_y), QPointF(arc_x + arc_w + 1, vne_y))
        p.restore()

        # --- Readout digitale centrale ---
        readout_w = 34
        readout_h = 20
        readout_x = tape_x + (tape_w - readout_w) / 2
        readout_y = cy - readout_h / 2

        p.setPen(QPen(QColor(255, 180, 0), 1.8))
        p.setBrush(QBrush(QColor(5, 5, 8, 240)))
        p.drawRoundedRect(QRectF(readout_x, readout_y, readout_w, readout_h), 3, 3)

        vf = p.font()
        vf.setPixelSize(12)
        vf.setBold(True)
        vf.setFamily("Consolas")
        p.setFont(vf)
        p.setPen(QColor(255, 255, 255))
        p.drawText(QRectF(readout_x, readout_y, readout_w, readout_h),
                   Qt.AlignmentFlag.AlignCenter,
                   f"{speed:.0f}")

        # --- Etichetta unità sotto la tape ---
        if u:
            lbl_w = 30.0
            lbl_x = tape_x + (tape_w - lbl_w) / 2
            lbl_y = tape_rect.bottom() + 3
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(QColor(5, 5, 8, 200))
            p.drawRoundedRect(QRectF(lbl_x, lbl_y, lbl_w, 11), 2, 2)
            uf = p.font()
            uf.setPixelSize(7)
            uf.setBold(True)
            p.setFont(uf)
            p.setPen(QColor(0, 220, 120))
            p.drawText(QRectF(lbl_x, lbl_y, lbl_w, 11),
                       Qt.AlignmentFlag.AlignCenter, u.label)



    def _draw_readout(self, p: QPainter, x: float, y: float,
                      label: str, value: float):
        """Disegna un piccolo readout digitale con etichetta e valore."""
        box = QRectF(x, y, 56, 18)

        # Sfondo scuro con bordo sottile
        p.setPen(QPen(QColor(80, 80, 85), 1))
        p.setBrush(QBrush(QColor(15, 15, 18, 220)))
        p.drawRoundedRect(box, 4, 4)

        # Etichetta (verde fosforescente)
        p.setPen(QColor(0, 220, 120))
        lf = p.font()
        lf.setPixelSize(8)
        lf.setBold(True)
        p.setFont(lf)
        p.drawText(QRectF(x + 2, y, 20, 18),
                   Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
                   label)
        # Valore (bianco, font monospace)          
        p.setPen(QColor(255, 255, 255))
        vf = p.font()
        vf.setPixelSize(9.5)
        vf.setBold(True)
        vf.setFamily("Consolas")
        p.setFont(vf)
        p.drawText(QRectF(x + 25, y, 30, 18),
                   Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter,
                   f"{value:+.1f}°")