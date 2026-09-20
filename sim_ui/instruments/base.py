from __future__ import annotations
import math
import uuid

from PySide6.QtCore import Qt, QPointF, QRectF
from PySide6.QtGui import QBrush, QColor, QPainter, QPainterPath, QPen, QPixmap
from PySide6.QtWidgets import QGraphicsItem, QGraphicsObject, QMenu

from ..core.constants import DEFAULT_GRID_SIZE
from ..core.prototype import InstrumentPrototype
from ..core.telemetry import TelemetryData
from ..core.theme import InstrumentTheme, _theme_base


class BaseInstrument(QGraphicsObject):
    def __init__(self, prototype: InstrumentPrototype, parent=None):
        super().__init__(parent)
        self._prototype = prototype
        self._instance_id = str(uuid.uuid4())
        self._bg_cache: QPixmap | None = None
        

        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, True)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges, True)
        self.setAcceptedMouseButtons(Qt.MouseButton.LeftButton)
        self.setCursor(Qt.CursorShape.OpenHandCursor)

        self._snap_enabled = False
        self._grid_size = DEFAULT_GRID_SIZE
        self._theme: InstrumentTheme | None = None

    @property
    def prototype(self): return self._prototype

    @property
    def instance_id(self): return self._instance_id

    def set_instance_id(self, v: str): self._instance_id = v

    def set_snap_enabled(self, e: bool): self._snap_enabled = e

    def set_grid_size(self, g: float): self._grid_size = max(1.0, g)

    def update_data(self, data: TelemetryData): pass

    def boundingRect(self) -> QRectF:
        return QRectF(0, 0, self._prototype.width, self._prototype.height)

    def _render_bg(self):
        w, h = int(self._prototype.width), int(self._prototype.height)
        px = QPixmap(w, h)
        px.fill(Qt.GlobalColor.transparent)
        p = QPainter(px)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setRenderHint(QPainter.RenderHint.TextAntialiasing)
        self.paint_background(p)
        p.end()
        self._bg_cache = px

    def paint(self, painter, option, widget=None):
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.TextAntialiasing)
        if self._bg_cache is None:
            self._render_bg()
        if self._bg_cache:
            painter.drawPixmap(0, 0, self._bg_cache)
        self.paint_foreground(painter)
        if self.isSelected():
            painter.setPen(QPen(self.theme().selection_color, 2))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawRoundedRect(self.boundingRect().adjusted(1, 1, -1, -1), 8, 8)

    def paint_background(self, p: QPainter): pass
    def paint_foreground(self, p: QPainter): pass

    def itemChange(self, change, value):
        if (change == QGraphicsItem.GraphicsItemChange.ItemPositionChange
                and self._snap_enabled and self._grid_size > 0):
            pos = value
            g = self._grid_size
            x, y = round(pos.x() / g) * g, round(pos.y() / g) * g
            s = self.scene()
            if s:
                sr = s.sceneRect()
                w = self.boundingRect().width() * self.scale()
                h = self.boundingRect().height() * self.scale()
                x = max(sr.left(), min(x, sr.right() - w))
                y = max(sr.top(), min(y, sr.bottom() - h))
            return QPointF(x, y)
        return super().itemChange(change, value)

    def mousePressEvent(self, e):
        if e.button() == Qt.MouseButton.LeftButton:
            self.setCursor(Qt.CursorShape.ClosedHandCursor)
        super().mousePressEvent(e)

    def mouseReleaseEvent(self, e):
        if e.button() == Qt.MouseButton.LeftButton:
            self.setCursor(Qt.CursorShape.OpenHandCursor)
        super().mouseReleaseEvent(e)

    def set_theme(self, theme: InstrumentTheme):
        self._theme = theme
        self._bg_cache = None   # invalida la cache dello sfondo
        self.update()

    def theme(self) -> InstrumentTheme:
        """Restituisce il tema attivo, con fallback su un tema base di sicurezza."""
        if self._theme is None:
            self._theme = _theme_base()
        return self._theme


class PlaceholderInstrument(BaseInstrument):
    def paint_background(self, p):
        th = self.theme()
        r = self.boundingRect().adjusted(2, 2, -2, -2)
        p.setPen(QPen(th.tick_major_color, 2))
        p.setBrush(QBrush(QColor(self._prototype.color)))
        p.drawRoundedRect(r, 12, 12)
        p.setPen(th.text_color)
        f = p.font()
        f.setBold(True)
        p.setFont(f)
        p.drawText(r.adjusted(8, 8, -8, -8),
                   Qt.AlignmentFlag.AlignCenter,
                   self._prototype.display_name)


class UnitButtonsMixin:
    """Aggiunge pulsanti per il cambio unità di misura."""

    def init_units(self, units, unit_index: int = 0):
        self._units = list(units)
        self._unit_index = unit_index % max(1, len(self._units))
        self._unit_pressed = None
        self._unit_was_movable = True

    def current_unit(self):
        if not getattr(self, "_units", None):
            return None
        return self._units[self._unit_index]

    def cycle_unit(self):
        if not getattr(self, "_units", None):
            return
        self._unit_index = (self._unit_index + 1) % len(self._units)
        self._on_unit_changed()

    def set_unit_index(self, idx: int):
        if 0 <= idx < len(self._units):
            self._unit_index = idx
            self._on_unit_changed()

    def _on_unit_changed(self):
        if hasattr(self, "_bg_cache"):
            self._bg_cache = None
        self.update()

    def unit_round_button_rect(self) -> QRectF:
        br = self.boundingRect()
        size = 16.0
        return QRectF(br.right() - size - 6.0, br.top() + 6.0, size, size)

    def unit_menu_button_rect(self) -> QRectF:
        r = self.unit_round_button_rect()
        return QRectF(r.left() + 2.0, r.bottom() + 4.0, r.width() - 4.0, 10.0)

    def _unit_button_at(self, pos: QPointF):
        if not getattr(self, "_units", None):
            return None
        if self.unit_round_button_rect().contains(pos):
            return "cycle"
        if self.unit_menu_button_rect().contains(pos):
            return "menu"
        return None

    def paint(self, painter, option, widget=None):
        super().paint(painter, option, widget)
        if getattr(self, "_units", None):
            self.paint_unit_buttons(painter)

    def paint_unit_buttons(self, p: QPainter):
        rr = self.unit_round_button_rect()
        mr = self.unit_menu_button_rect()

        p.setPen(QPen(QColor(160, 170, 180), 1))
        p.setBrush(QColor(52, 58, 66))
        p.drawEllipse(rr)

        icon = rr.adjusted(4, 4, -4, -4)
        p.setPen(QPen(QColor(225, 230, 235), 1.5))
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawArc(icon, 40 * 16, 280 * 16)

        c = rr.center()
        radius = icon.width() / 2.0
        ang = math.radians(40)
        ax = c.x() + radius * math.cos(ang)
        ay = c.y() - radius * math.sin(ang)

        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QColor(225, 230, 235))

        arrow = QPainterPath()
        arrow.moveTo(ax + 3.0, ay)
        arrow.lineTo(ax - 1.0, ay - 2.5)
        arrow.lineTo(ax - 1.0, ay + 2.5)
        arrow.closeSubpath()
        p.drawPath(arrow)

        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QColor(225, 230, 235))

        tri = QPainterPath()
        tri.moveTo(mr.left(), mr.top())
        tri.lineTo(mr.right(), mr.top())
        tri.lineTo(mr.center().x(), mr.bottom())
        tri.closeSubpath()
        p.drawPath(tri)

    def show_unit_menu(self):
        if not getattr(self, "_units", None):
            return
        menu = QMenu()
        for i, u in enumerate(self._units):
            act = menu.addAction(u.label)
            act.setCheckable(True)
            act.setChecked(i == self._unit_index)
            act.triggered.connect(
                lambda checked=False, idx=i: self.set_unit_index(idx)
            )
        view = None
        if self.scene() and self.scene().views():
            view = self.scene().views()[0]
        if view:
            scene_pos = self.mapToScene(self.unit_menu_button_rect().center())
            view_pos = view.mapFromScene(scene_pos)
            menu.exec(view.mapToGlobal(view_pos))

    def mousePressEvent(self, e):
        if e.button() == Qt.MouseButton.LeftButton and getattr(self, "_units", None):
            action = self._unit_button_at(e.pos())
            if action:
                self._unit_pressed = action
                self._unit_was_movable = bool(
                    self.flags() & QGraphicsItem.GraphicsItemFlag.ItemIsMovable
                )
                self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, False)
                e.accept()
                self.update()
                return
        super().mousePressEvent(e)

    def mouseReleaseEvent(self, e):
        if e.button() == Qt.MouseButton.LeftButton and getattr(self, "_unit_pressed", None):
            pressed = self._unit_pressed
            action = self._unit_button_at(e.pos())
            self._unit_pressed = None
            if self._unit_was_movable:
                self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, True)
            if action == pressed:
                if pressed == "cycle":
                    self.cycle_unit()
                elif pressed == "menu":
                    self.show_unit_menu()
            self.update()
            e.accept()
            return
        super().mouseReleaseEvent(e)