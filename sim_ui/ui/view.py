from __future__ import annotations

import math
import time

from PySide6.QtCore import Qt, QPointF, QPoint, QEvent, Signal, QRectF
from PySide6.QtGui import QCursor, QPainter, QPen, QColor, QFont
from PySide6.QtWidgets import QGraphicsView

try:
    from PySide6.QtOpenGLWidgets import QOpenGLWidget
    OPENGL_AVAILABLE = True
except ImportError:
    OPENGL_AVAILABLE = False

from ..core.constants import MIME_INSTRUMENT

# =============================================================================
# GRAPHICS VIEW (ZOOM + PAN + RUBBER BAND)
# =============================================================================

class InstrumentGraphicsView(QGraphicsView):
    instrument_dropped = Signal(str, object)
    context_menu_requested = Signal(QPoint)
    cursor_moved = Signal(QPointF)

        # =========================================================================
    # RIGHELLI (fissi nel viewport, si aggiornano con pan/zoom)
    # =========================================================================

    _RULER_SIZE = 22
    _RULER_BG = QColor(25, 25, 30, 220)
    _RULER_TICK = QColor(170, 170, 175)
    _RULER_TEXT = QColor(200, 200, 205)
    _RULER_BORDER = QColor(80, 80, 85)

    def paintEvent(self, event):
        super().paintEvent(event)
        painter = QPainter(self.viewport())
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, False)
        self._draw_rulers(painter)
        painter.end()

    def _draw_rulers(self, painter: QPainter):
        vp = self.viewport().rect()
        rs = self._RULER_SIZE

        # Rect visibile in coordinate scena
        scene_rect = self.mapToScene(vp).boundingRect()
        zoom = self.transform().m11()

        # Passo "pulito" per le tacche
        step = self._nice_ruler_step(zoom)

        # --- Righello superiore (asse X) ---
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(self._RULER_BG)
        painter.drawRect(0, 0, vp.width(), rs)

        font = QFont("Consolas", 7)
        painter.setFont(font)

        x_start = int(math.floor(scene_rect.left() / step)) * step
        x_end = scene_rect.right()
        x = x_start
        while x <= x_end:
            screen_pt = self.mapFromScene(QPointF(x, 0))
            sx = screen_pt.x()
            if 0 <= sx <= vp.width():
                is_major = (abs(x % (step * 5)) < 0.01)
                tick_h = 10 if is_major else 6
                painter.setPen(QPen(self._RULER_TICK, 1))
                painter.drawLine(int(sx), rs, int(sx), rs - tick_h)
                if is_major:
                    painter.setPen(self._RULER_TEXT)
                    painter.drawText(QRectF(sx - 20, 2, 40, 12),
                                     Qt.AlignmentFlag.AlignCenter,
                                     str(int(x)))
            x += step

        # Bordo inferiore righello X
        painter.setPen(QPen(self._RULER_BORDER, 1))
        painter.drawLine(0, rs, vp.width(), rs)

        # --- Righello destro (asse Y) ---
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(self._RULER_BG)
        painter.drawRect(vp.width() - rs, 0, rs, vp.height())

        y_start = int(math.floor(scene_rect.top() / step)) * step
        y_end = scene_rect.bottom()
        y = y_start
        while y <= y_end:
            screen_pt = self.mapFromScene(QPointF(0, y))
            sy = screen_pt.y()
            if 0 <= sy <= vp.height():
                is_major = (abs(y % (step * 5)) < 0.01)
                tick_w = 10 if is_major else 6
                painter.setPen(QPen(self._RULER_TICK, 1))
                painter.drawLine(vp.width() - rs, int(sy),
                                 vp.width() - rs + tick_w, int(sy))
                if is_major:
                    painter.setPen(self._RULER_TEXT)
                    painter.save()
                    painter.translate(vp.width() - rs + 12, int(sy))
                    painter.rotate(90)
                    painter.drawText(QRectF(-15, -8, 30, 12),
                                     Qt.AlignmentFlag.AlignCenter,
                                     str(int(y)))
                    painter.restore()
            y += step

        # Bordo sinistro righello Y
        painter.setPen(QPen(self._RULER_BORDER, 1))
        painter.drawLine(vp.width() - rs, 0, vp.width() - rs, vp.height())

    def _nice_ruler_step(self, zoom: float) -> float:
        """Calcola un passo 'pulito' per le tacche in base allo zoom."""
        target_px = 60  # pixel schermo desiderati tra le tacche
        scene_step = target_px / max(0.01, zoom)

        magnitude = 10 ** math.floor(math.log10(max(0.001, scene_step)))
        residual = scene_step / magnitude

        if residual <= 1.0:
            return magnitude
        elif residual <= 2.0:
            return 2 * magnitude
        elif residual <= 5.0:
            return 5 * magnitude
        else:
            return 10 * magnitude

    def __init__(self, scene, parent=None):
        super().__init__(scene, parent)
        self.setAcceptDrops(True)
        self.viewport().installEventFilter(self)

        # Rubber band per selezione multipla
        self.setDragMode(QGraphicsView.DragMode.RubberBandDrag)
        self.setAcceptDrops(True)

        # Ottimizzazioni viewport
        self.setViewportUpdateMode(QGraphicsView.ViewportUpdateMode.MinimalViewportUpdate)
        self.setCacheMode(QGraphicsView.CacheModeFlag.CacheNone)

        # Pan state
        self._panning = False
        self._pan_start = QPoint()

        # Mouse tracking per coordinate
        self.setMouseTracking(True)

        # Aggiorna i righelli durante lo scroll
        self.horizontalScrollBar().valueChanged.connect(self.viewport().update)
        self.verticalScrollBar().valueChanged.connect(self.viewport().update)

        self._fps_counter = FPSCounter()

    def tick_fps(self):
        self._fps_counter.tick()

    def get_fps(self) -> float:
        return self._fps_counter.fps


    # --- Context menu / event filter ---
    def eventFilter(self, obj, event):
        et = event.type()
        if et == QEvent.Type.MouseButtonRelease and event.button() == Qt.MouseButton.RightButton:
            # QMouseEvent → ha position()
            self.context_menu_requested.emit(event.position().toPoint())
            return True
        elif et == QEvent.Type.ContextMenu:
            # QContextMenuEvent → ha pos(), NON position()
            self.context_menu_requested.emit(event.pos())
            event.accept()
            return True
        return super().eventFilter(obj, event)

    def contextMenuEvent(self, event):
        # QContextMenuEvent → usa pos()
        vp = self.viewport().mapFrom(self, event.pos())
        self.context_menu_requested.emit(vp)
        event.accept()
        
    # --- Zoom con Ctrl+Wheel ---
    def wheelEvent(self, event):
        if event.modifiers() == Qt.KeyboardModifier.ControlModifier:
            factor = 1.15 if event.angleDelta().y() > 0 else 1.0/1.15
            self.scale(factor, factor)
            self.viewport().update()
            event.accept()
        else:
            super().wheelEvent(event)

    # --- Pan con tasto centrale ---
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.MiddleButton:
            self._panning = True
            self._pan_start = event.position().toPoint()
            self.viewport().setCursor(Qt.CursorShape.ClosedHandCursor)
            event.accept()
        else:
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._panning:
            delta = event.position().toPoint() - self._pan_start
            self._pan_start = event.position().toPoint()
            self.horizontalScrollBar().setValue(self.horizontalScrollBar().value() - delta.x())
            self.verticalScrollBar().setValue(self.verticalScrollBar().value() - delta.y())
            event.accept()
        else:
            # Emetti posizione scena per status bar
            sp = self.mapToScene(event.position().toPoint())
            self.cursor_moved.emit(sp)
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.MiddleButton:
            self._panning = False
            self.viewport().setCursor(Qt.CursorShape.ArrowCursor)
            event.accept()
        else:
            super().mouseReleaseEvent(event)

    # --- Zoom API ---
    def zoom_in(self): self.scale(1.2, 1.2)
    def zoom_out(self): self.scale(1/1.2, 1/1.2)
    def zoom_reset(self): self.resetTransform()

    def fit_all(self):
        items = self.scene().items()
        if items:
            rect = QRectF()
            for it in items:
                rect = rect.united(it.sceneBoundingRect())
            if not rect.isNull():
                self.fitInView(rect.adjusted(-20,-20,20,20), Qt.AspectRatioMode.KeepAspectRatio)

    # --- Drag & Drop ---
    def _set_drag_cursor(self):
        try: self.viewport().setCursor(Qt.CursorShape.DragCopyCursor)
        except AttributeError: self.viewport().setCursor(Qt.CursorShape.PointingHandCursor)
    def _reset_cursor(self): self.viewport().setCursor(Qt.CursorShape.ArrowCursor)

    def dragEnterEvent(self, e):
        m = e.mimeData()
        if m and m.hasFormat(MIME_INSTRUMENT):
            e.acceptProposedAction(); self._set_drag_cursor()
        else: super().dragEnterEvent(e)

    def dragMoveEvent(self, e):
        m = e.mimeData()
        if m and m.hasFormat(MIME_INSTRUMENT): e.acceptProposedAction()
        else: super().dragMoveEvent(e)

    def dragLeaveEvent(self, e): self._reset_cursor(); super().dragLeaveEvent(e)

    def dropEvent(self, e):
        m = e.mimeData()
        if not m or not m.hasFormat(MIME_INSTRUMENT):
            super().dropEvent(e); return
        tid = bytes(m.data(MIME_INSTRUMENT)).decode("utf-8", errors="ignore")
        vp = e.position().toPoint()
        vp2 = self.viewport().mapFrom(self, vp)
        sp = self.mapToScene(vp2)
        self.instrument_dropped.emit(tid, sp)
        e.acceptProposedAction(); self._reset_cursor()

    # --- OpenGL support ---

    def set_opengl(self, enabled: bool):
        """Attiva/disattiva rendering OpenGL."""
        if enabled and OPENGL_AVAILABLE:
            gl_widget = QOpenGLWidget()
            self.setViewport(gl_widget)
        else:
            self.setViewport(None)  # Torna al rendering software

    def is_opengl(self) -> bool:
        return isinstance(self.viewport(), QOpenGLWidget) if OPENGL_AVAILABLE else False

    def get_fps(self) -> float:
        return self._fps_counter.fps

    def tick_fps(self):
        self._fps_counter.tick()

# =============================================================================
# FPS COUNTER
# =============================================================================

class FPSCounter:
    def __init__(self):
        self._frame_count = 0
        self._last_time = time.perf_counter()
        self._fps = 0.0

    def tick(self):
        self._frame_count += 1
        now = time.perf_counter()
        elapsed = now - self._last_time
        if elapsed >= 1.0:
            self._fps = self._frame_count / elapsed
            self._frame_count = 0
            self._last_time = now

    @property
    def fps(self) -> float:
        return self._fps
