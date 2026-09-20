import time
from PySide6.QtCore import Qt, QPointF, QPoint, QEvent, Signal
from PySide6.QtGui import QCursor, QPainter
from PySide6.QtWidgets import QGraphicsView

try:
    from PySide6.QtOpenGLWidgets import QOpenGLWidget
    OPENGL_AVAILABLE = True
except ImportError:
    OPENGL_AVAILABLE = False

from ..core.constants import INSTRUMENT_MIME_TYPE

# =============================================================================
# GRAPHICS VIEW (ZOOM + PAN + RUBBER BAND)
# =============================================================================

class InstrumentGraphicsView(QGraphicsView):
    instrument_dropped = Signal(str, object)
    context_menu_requested = Signal(QPoint)
    cursor_moved = Signal(QPointF)

    def __init__(self, scene, parent=None):
        super().__init__(scene, parent)
        self.setAcceptDrops(True)
        self.viewport().installEventFilter(self)

        # Rubber band per selezione multipla
        self.setDragMode(QGraphicsView.DragMode.RubberBandDrag)

        # Ottimizzazioni viewport
        self.setViewportUpdateMode(QGraphicsView.ViewportUpdateMode.MinimalViewportUpdate)
        self.setCacheMode(QGraphicsView.CacheModeFlag.CacheNone)

        # Pan state
        self._panning = False
        self._pan_start = QPoint()

        # Mouse tracking per coordinate
        self.setMouseTracking(True)

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
        if m and m.hasFormat(INSTRUMENT_MIME_TYPE):
            e.acceptProposedAction(); self._set_drag_cursor()
        else: super().dragEnterEvent(e)

    def dragMoveEvent(self, e):
        m = e.mimeData()
        if m and m.hasFormat(INSTRUMENT_MIME_TYPE): e.acceptProposedAction()
        else: super().dragMoveEvent(e)

    def dragLeaveEvent(self, e): self._reset_cursor(); super().dragLeaveEvent(e)

    def dropEvent(self, e):
        m = e.mimeData()
        if not m or not m.hasFormat(INSTRUMENT_MIME_TYPE):
            super().dropEvent(e); return
        tid = bytes(m.data(INSTRUMENT_MIME_TYPE)).decode("utf-8", errors="ignore")
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
