from __future__ import annotations

from PySide6.QtCore import Qt, QPoint, QSize, QMimeData, Signal
from PySide6.QtGui import QBrush, QColor, QDrag, QPainter, QPixmap
from PySide6.QtWidgets import (
    QDockWidget, QLineEdit, QListWidget, QListWidgetItem,
    QSizePolicy, QVBoxLayout, QWidget,
)

from ..core.constants import INSTRUMENT_MIME_TYPE
from ..core.prototype import InstrumentRegistry


# =============================================================================
# LISTA STRUMENTI (drag & drop)
# =============================================================================

class HangarListWidget(QListWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setDragEnabled(True)

    def startDrag(self, supportedActions):
        item = self.currentItem()
        if not item:
            return
        tid = item.data(Qt.ItemDataRole.UserRole)
        if not tid:
            return
        mime = QMimeData()
        mime.setData(INSTRUMENT_MIME_TYPE, tid.encode())
        drag = QDrag(self)
        drag.setMimeData(mime)
        px = self._pixmap(item.text().strip())
        if not px.isNull():
            drag.setPixmap(px)
            drag.setHotSpot(QPoint(px.width() // 2, px.height() // 2))
        drag.exec(Qt.DropAction.CopyAction)

    def _pixmap(self, text):
        if not text:
            text = "Strumento"
        px = QPixmap(220, 44)
        px.fill(QColor(35, 40, 52))
        p = QPainter(px)
        p.setPen(QColor(230, 235, 245))
        f = p.font()
        f.setBold(True)
        p.setFont(f)
        p.drawText(px.rect().adjusted(10, 0, -10, 0),
                   Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft, text)
        p.end()
        return px


# =============================================================================
# DOCK HANGAR con barra di ricerca
# =============================================================================

class HangarDockWidget(QDockWidget):
    instrument_requested = Signal(str)

    def __init__(self, registry: InstrumentRegistry, parent=None):
        super().__init__("Hangar", parent)
        self.setAllowedAreas(
            Qt.DockWidgetArea.LeftDockWidgetArea | Qt.DockWidgetArea.RightDockWidgetArea
        )
        self._registry = registry

        # ---------------------------------------------------------------------
        # Contenitore verticale: barra di ricerca + lista
        # ---------------------------------------------------------------------
        container = QWidget(self)
        layout = QVBoxLayout(container)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(4)

        # Barra di ricerca (sempre visibile in alto)
        self._search = QLineEdit(container)
        self._search.setPlaceholderText("Cerca strumento...")
        self._search.setClearButtonEnabled(True)
        self._search.setSizePolicy(QSizePolicy.Policy.Expanding,
                                   QSizePolicy.Policy.Fixed)
        self._search.setMinimumWidth(50)
        self._search.textChanged.connect(self._apply_filter)
        layout.addWidget(self._search)

        # Lista strumenti
        self._list = HangarListWidget(container)
        self._list.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        layout.addWidget(self._list, 1)

        self.setWidget(container)

        self._populate()
        self._list.itemDoubleClicked.connect(self._on_dbl)

    # =========================================================================
    # POPOLAMENTO
    # =========================================================================

    def _populate(self):
        self._list.clear()
        for cat in self._registry.categories():
            h = QListWidgetItem(cat.upper())
            h.setFlags(Qt.ItemFlag.ItemIsEnabled)
            hf = h.font()
            hf.setBold(True)
            h.setFont(hf)
            h.setForeground(QBrush(QColor(140, 170, 255)))
            h.setBackground(QBrush(QColor(28, 33, 44)))
            h.setSizeHint(QSize(0, 30))
            self._list.addItem(h)
            for p in self._registry.prototypes_in_category(cat):
                it = QListWidgetItem(f"  {p.display_name}")
                it.setData(Qt.ItemDataRole.UserRole, p.type_id)
                it.setToolTip(p.description or p.display_name)
                self._list.addItem(it)

    # =========================================================================
    # FILTRO DI RICERCA
    # =========================================================================

    def _apply_filter(self, text: str):
        """
        Mostra/nasconde le voci in base al testo cercato.
        - Cerca in: nome visualizzato, type_id, descrizione (tooltip)
        - Le intestazioni di categoria spariscono se non hanno strumenti visibili
        """
        query = text.strip().lower()

        current_header_row = None
        header_visible_count: dict[int, int] = {}

        for row in range(self._list.count()):
            item = self._list.item(row)
            tid = item.data(Qt.ItemDataRole.UserRole)

            if tid is None:
                # Intestazione di categoria
                current_header_row = row
                header_visible_count[row] = 0
                continue

            name = item.text().strip().lower()
            desc = (item.toolTip() or "").lower()
            type_id = tid.lower()

            match = (not query) or (query in name) or (query in type_id) or (query in desc)
            item.setHidden(not match)

            if match and current_header_row is not None:
                header_visible_count[current_header_row] += 1

        # Nascondi le categorie senza strumenti visibili
        for row, count in header_visible_count.items():
            self._list.item(row).setHidden(count == 0)

    # =========================================================================
    # EVENTI
    # =========================================================================

    def _on_dbl(self, item):
        tid = item.data(Qt.ItemDataRole.UserRole)
        if tid:
            self.instrument_requested.emit(tid)