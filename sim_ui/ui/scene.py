from PySide6.QtCore import Qt, QPointF, QRectF
from PySide6.QtGui import QColor, QPainter, QPen
from PySide6.QtWidgets import QGraphicsScene

from ..core.constants import DEFAULT_GRID_SIZE


class InstrumentScene(QGraphicsScene):

    def __init__(self, parent=None):
        super().__init__(parent)
        self._snap_enabled = False
        self._grid_size = DEFAULT_GRID_SIZE
        self._grid_color = QColor(100, 100, 100, 60)  # default visibile

    # =========================================================================
    # SETTER
    # =========================================================================

    def set_snap_enabled(self, enabled: bool):
        """Attiva/disattiva snap e visibilità griglia."""
        self._snap_enabled = enabled
        self.invalidate()  # forza ridisegno del background

    def set_grid_size(self, size: float):
        """Imposta la dimensione della griglia e ridisegna."""
        self._grid_size = size
        self.invalidate()

    def set_grid_color(self, color):
        """Imposta il colore della griglia e ridisegna."""
        self._grid_color = QColor(color)
        self.invalidate()

    # =========================================================================
    # DISEGNO SFONDO + GRIGLIA
    # =========================================================================

    def drawBackground(self, painter: QPainter, rect: QRectF):
        super().drawBackground(painter, rect)

        if not self._snap_enabled or self._grid_size <= 0:
            return

        grid = self._grid_size
        painter.setPen(QPen(self._grid_color, 1))

        # Linee verticali
        x = (rect.left() // grid) * grid
        while x <= rect.right():
            painter.drawLine(QPointF(x, rect.top()), QPointF(x, rect.bottom()))
            x += grid

        # Linee orizzontali
        y = (rect.top() // grid) * grid
        while y <= rect.bottom():
            painter.drawLine(QPointF(rect.left(), y), QPointF(rect.right(), y))
            y += grid