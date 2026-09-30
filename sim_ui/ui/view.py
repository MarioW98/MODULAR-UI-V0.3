from __future__ import annotations

import math
import time

from PySide6.QtCore import Qt, QPointF, QPoint, QEvent, Signal, QRectF
from PySide6.QtGui import QCursor, QPainter, QPen, QColor, QFont
from PySide6.QtWidgets import QGraphicsView, QWidget

try:
    from PySide6.QtOpenGLWidgets import QOpenGLWidget
    OPENGL_AVAILABLE = True
except ImportError:
    OPENGL_AVAILABLE = False

from ..core.constants import MIME_INSTRUMENT


# =============================================================================
# RULERS OVERLAY
# =============================================================================

class RulersOverlay(QWidget):
    """
    Widget trasparente sovrapposto al viewport.
    Disegna i righelli senza interferire con il rendering OpenGL.
    """

    def __init__(self, view, parent=None):
        super().__init__(parent)
        self._view = view

        # Non intercettare eventi mouse
        self.setAttribute(Qt.WA_TransparentForMouseEvents, True)

        # Sfondo trasparente
        self.setAttribute(Qt.WA_NoSystemBackground, True)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setAutoFillBackground(False)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, False)
        self._view._draw_rulers(painter)
        painter.end()


# =============================================================================
# GRAPHICS VIEW
# =============================================================================

class InstrumentGraphicsView(QGraphicsView):

    instrument_dropped = Signal(str, object)
    context_menu_requested = Signal(QPoint)
    cursor_moved = Signal(QPointF)

    # =========================================================================
    # COSTANTI RIGHELLI
    # =========================================================================

    _RULER_SIZE = 22
    _RULER_BG = QColor(25, 25, 30, 220)
    _RULER_TICK = QColor(170, 170, 175)
    _RULER_TEXT = QColor(200, 200, 205)
    _RULER_BORDER = QColor(80, 80, 85)

    # =========================================================================
    # INIT
    # =========================================================================

    def __init__(self, scene, parent=None):
        super().__init__(scene, parent)

        self.setAcceptDrops(True)
        # Referenza al viewport corrente: il filtro eventi va re-installato
        # ogni volta che setViewport() sostituisce il widget (toggle OpenGL).
        self._viewport_widget = self.viewport()
        self._viewport_widget.installEventFilter(self)

        # Rubber band per selezione multipla
        self.setDragMode(QGraphicsView.DragMode.RubberBandDrag)

        # Ottimizzazioni viewport
        self.setViewportUpdateMode(
            QGraphicsView.ViewportUpdateMode.MinimalViewportUpdate
        )
        self.setCacheMode(QGraphicsView.CacheModeFlag.CacheNone)

        # Pan state
        self._panning = False
        self._pan_start = QPoint()

        # Mouse tracking per coordinate
        self.setMouseTracking(True)

        # FPS counter
        self._fps_counter = FPSCounter()

        # Overlay righelli
        self._rulers_overlay = None
        self._setup_rulers_overlay()

        # Aggiorna i righelli durante lo scroll
        self.horizontalScrollBar().valueChanged.connect(self._update_rulers)
        self.verticalScrollBar().valueChanged.connect(self._update_rulers)

    # =========================================================================
    # FPS
    # =========================================================================

    def tick_fps(self):
        self._fps_counter.tick()

    def get_fps(self) -> float:
        return self._fps_counter.fps

    # =========================================================================
    # OVERLAY RIGHELLI
    # =========================================================================

    def _setup_rulers_overlay(self):
        """
        Crea o ricrea l'overlay dei righelli.
        L'overlay è figlio della view, NON del viewport.
        """
        old = getattr(self, "_rulers_overlay", None)
        if old is not None:
            old.setParent(None)
            old.deleteLater()

        self._rulers_overlay = RulersOverlay(self, self)
        self._sync_rulers_geometry()
        self._rulers_overlay.show()
        self._rulers_overlay.raise_()

    def _sync_rulers_geometry(self):
        """Allinea l'overlay al rettangolo del viewport."""
        overlay = getattr(self, "_rulers_overlay", None)
        if overlay is None:
            return

        overlay.setGeometry(self.viewport().geometry())
        overlay.raise_()

    def _update_rulers(self):
        """Forza il ridisegno dei righelli."""
        overlay = getattr(self, "_rulers_overlay", None)
        if overlay is not None:
            overlay.update()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._sync_rulers_geometry()
        self._update_rulers()

    # =========================================================================
    # EVENT FILTER
    # =========================================================================

    def eventFilter(self, obj, event):
        et = event.type()

        # Se il viewport cambia dimensione, allinea l'overlay
        if obj is self.viewport() and et == QEvent.Type.Resize:
            self._sync_rulers_geometry()
            self._update_rulers()

        # Context menu con tasto destro
        if et == QEvent.Type.MouseButtonRelease and event.button() == Qt.MouseButton.RightButton:
            self.context_menu_requested.emit(event.position().toPoint())
            return True

        elif et == QEvent.Type.ContextMenu:
            self.context_menu_requested.emit(event.pos())
            event.accept()
            return True

        return super().eventFilter(obj, event)

    def contextMenuEvent(self, event):
        vp = self.viewport().mapFrom(self, event.pos())
        self.context_menu_requested.emit(vp)
        event.accept()

    # =========================================================================
    # ZOOM CON CTRL+WHEEL
    # =========================================================================

    def wheelEvent(self, event):
        if event.modifiers() == Qt.KeyboardModifier.ControlModifier:
            factor = 1.15 if event.angleDelta().y() > 0 else 1.0 / 1.15
            self.scale(factor, factor)
            self._update_rulers()
            event.accept()
        else:
            super().wheelEvent(event)

    # =========================================================================
    # PAN CON TASTO CENTRALE
    # =========================================================================

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

            self.horizontalScrollBar().setValue(
                self.horizontalScrollBar().value() - delta.x()
            )
            self.verticalScrollBar().setValue(
                self.verticalScrollBar().value() - delta.y()
            )

            event.accept()
        else:
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

    # =========================================================================
    # ZOOM API
    # =========================================================================

    def zoom_in(self):
        self.scale(1.2, 1.2)
        self._update_rulers()

    def zoom_out(self):
        self.scale(1 / 1.2, 1 / 1.2)
        self._update_rulers()

    def zoom_reset(self):
        self.resetTransform()
        self._update_rulers()

    def fit_all(self):
        items = self.scene().items()
        if items:
            rect = QRectF()
            for it in items:
                rect = rect.united(it.sceneBoundingRect())

            if not rect.isNull():
                self.fitInView(
                    rect.adjusted(-20, -20, 20, 20),
                    Qt.AspectRatioMode.KeepAspectRatio
                )
                self._update_rulers()

    # =========================================================================
    # DRAG & DROP
    # =========================================================================

    def _set_drag_cursor(self):
        try:
            self.viewport().setCursor(Qt.CursorShape.DragCopyCursor)
        except AttributeError:
            self.viewport().setCursor(Qt.CursorShape.PointingHandCursor)

    def _reset_cursor(self):
        self.viewport().setCursor(Qt.CursorShape.ArrowCursor)

    def dragEnterEvent(self, e):
        m = e.mimeData()
        if m and m.hasFormat(MIME_INSTRUMENT):
            e.acceptProposedAction()
            self._set_drag_cursor()
        else:
            super().dragEnterEvent(e)

    def dragMoveEvent(self, e):
        m = e.mimeData()
        if m and m.hasFormat(MIME_INSTRUMENT):
            e.acceptProposedAction()
        else:
            super().dragMoveEvent(e)

    def dragLeaveEvent(self, e):
        self._reset_cursor()
        super().dragLeaveEvent(e)

    def dropEvent(self, e):
        m = e.mimeData()
        if not m or not m.hasFormat(MIME_INSTRUMENT):
            super().dropEvent(e)
            return

        tid = bytes(m.data(MIME_INSTRUMENT)).decode("utf-8", errors="ignore")
        vp = e.position().toPoint()
        vp2 = self.viewport().mapFrom(self, vp)
        sp = self.mapToScene(vp2)

        self.instrument_dropped.emit(tid, sp)
        e.acceptProposedAction()
        self._reset_cursor()

    # =========================================================================
    # OPENGL
    # =========================================================================

    def set_opengl(self, enabled: bool):
        """
        Attiva/disattiva rendering OpenGL.
        Dopo il cambio viewport ricreo sempre l'overlay dei righelli.
        """
        if not OPENGL_AVAILABLE or self.is_opengl():
            return
        from PySide6.QtGui import QSurfaceFormat

        fmt = QSurfaceFormat()
        fmt.setSamples(4)
        fmt.setSwapBehavior(QSurfaceFormat.SwapBehavior.DoubleBuffer)

        gl_widget = QOpenGLWidget()
        gl_widget.setFormat(fmt)
        self.setViewport(gl_widget)


        self._viewport_widget = self.viewport()
        self._viewport_widget.installEventFilter(self)

        self.setViewportUpdateMode(
                QGraphicsView.ViewportUpdateMode.MinimalViewportUpdate
            )
        self.setCacheMode(QGraphicsView.CacheModeFlag.CacheNone)

        # Reinstalla event filter e mouse tracking sul nuovo viewport
        self.viewport().installEventFilter(self)
        self.viewport().setMouseTracking(True)

        # Ricrea l'overlay dei righelli sul nuovo viewport
        self._setup_rulers_overlay()
        self._update_rulers()

    def is_opengl(self) -> bool:
        if not OPENGL_AVAILABLE:
            return False
        return isinstance(self.viewport(), QOpenGLWidget)

    # =========================================================================
    # DISEGNO RIGHELLI
    # =========================================================================

    def _draw_rulers(self, painter: QPainter):
        """
        Disegna i righelli.
        Viene chiamato da RulersOverlay.paintEvent().
        """
        vp = self.viewport().rect()
        w = vp.width()
        h = vp.height()

        if w <= 0 or h <= 0:
            return

        rs = self._RULER_SIZE

        # Rect visibile in coordinate scena
        scene_rect = self.mapToScene(vp).boundingRect()

        # Zoom attuale
        zoom = self.transform().m11()

        # Passo "pulito" per le tacche
        step = self._nice_ruler_step(zoom)

        # =========================================================================
        # RIGHELLO SUPERIORE — ASSE X
        # =========================================================================

        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(self._RULER_BG)
        painter.drawRect(0, 0, w, rs)

        font = QFont("Consolas", 7)
        painter.setFont(font)

        x_start = int(math.floor(scene_rect.left() / step)) * step
        x_end = scene_rect.right()

        x = x_start
        while x <= x_end:
            sx = self.mapFromScene(QPointF(x, 0)).x()

            if 0 <= sx <= w:
                is_major = abs(x % (step * 5)) < 0.01
                tick_h = 10 if is_major else 6

                painter.setPen(QPen(self._RULER_TICK, 1))
                painter.drawLine(int(sx), rs, int(sx), rs - tick_h)

                if is_major:
                    painter.setPen(self._RULER_TEXT)
                    painter.drawText(
                        QRectF(sx - 20, 2, 40, 12),
                        Qt.AlignmentFlag.AlignCenter,
                        str(int(x))
                    )

            x += step

        # Bordo inferiore righello X
        painter.setPen(QPen(self._RULER_BORDER, 1))
        painter.drawLine(0, rs, w, rs)

        # =========================================================================
        # RIGHELLO DESTRO — ASSE Y
        # =========================================================================

        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(self._RULER_BG)
        painter.drawRect(w - rs, 0, rs, h)

        y_start = int(math.floor(scene_rect.top() / step)) * step
        y_end = scene_rect.bottom()

        y = y_start
        while y <= y_end:
            sy = self.mapFromScene(QPointF(0, y)).y()

            if 0 <= sy <= h:
                is_major = abs(y % (step * 5)) < 0.01
                tick_w = 10 if is_major else 6

                painter.setPen(QPen(self._RULER_TICK, 1))
                painter.drawLine(
                    w - rs,
                    int(sy),
                    w - rs + tick_w,
                    int(sy)
                )

                if is_major:
                    painter.setPen(self._RULER_TEXT)
                    painter.save()
                    painter.translate(w - rs + 12, int(sy))
                    painter.rotate(90)
                    painter.drawText(
                        QRectF(-15, -8, 30, 12),
                        Qt.AlignmentFlag.AlignCenter,
                        str(int(y))
                    )
                    painter.restore()

            y += step

        # Bordo sinistro righello Y
        painter.setPen(QPen(self._RULER_BORDER, 1))
        painter.drawLine(w - rs, 0, w - rs, h)

    def _nice_ruler_step(self, zoom: float) -> float:
        """
        Calcola un passo 'pulito' per le tacche in base allo zoom.
        Esempi di passi: 1, 2, 5, 10, 20, 50, 100, 200, 500...
        """
        target_px = 60
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