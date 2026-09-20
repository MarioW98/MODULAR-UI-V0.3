from PySide6.QtCore import Qt, QPointF, QRectF
from PySide6.QtGui import QColor, QPainter, QPen
from PySide6.QtWidgets import QGraphicsScene
from ..core.constants import DEFAULT_GRID_SIZE

class InstrumentScene(QGraphicsScene):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._snap_enabled = False
        self._grid_size = DEFAULT_GRID_SIZE

    def set_snap_enabled(self, e): self._snap_enabled = e; self.invalidate()
    def set_grid_size(self, g): self._grid_size = max(1.0, g); self.invalidate()

    def drawBackground(self, painter, rect):
        super().drawBackground(painter, rect)
        if not self._snap_enabled or self._grid_size <= 0: return
        grid = self._grid_size
        painter.setPen(QPen(QColor(255, 255, 255, 18), 1))
        x = (rect.left() // grid) * grid
        while x <= rect.right():
            painter.drawLine(QPointF(x, rect.top()), QPointF(x, rect.bottom())); x += grid
        y = (rect.top() // grid) * grid
        while y <= rect.bottom():
            painter.drawLine(QPointF(rect.left(), y), QPointF(rect.right(), y)); y += grid

