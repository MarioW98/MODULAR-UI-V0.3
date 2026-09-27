from __future__ import annotations

from PySide6.QtCore import Qt, QMimeData, QSize, Signal
from PySide6.QtGui import QPixmap, QPainter, QDrag, QIcon
from PySide6.QtWidgets import (
    QDockWidget, QWidget, QVBoxLayout, QHBoxLayout, QLineEdit,
    QListWidget, QListWidgetItem, QComboBox, QToolButton,
    QStyleOptionGraphicsItem,
)

from ..core.prototype import InstrumentRegistry
from ..core.theme import build_default_themes
from ..core.telemetry import TelemetryData
from ..core.constants import MIME_INSTRUMENT
from ..instruments.factory import InstrumentFactory

# Ordine e nomi degli stili per il filtro
STYLE_ORDER = ["Base", "Professional","Digital", "Advance",
               "Comfort", "Display", "View"]


class HangarDockWidget(QDockWidget):
    """
    Hangar strumenti con:
    - Barra di ricerca
    - Filtro per stile
    - Toggle miniature/lista
    - Thumbnail degli strumenti
    - Doppio-click per aggiungere, drag per posizionare
    """

    # Segnale emesso quando si richiede uno strumento (doppio-click)
    instrument_requested = Signal(str)

    def __init__(self, registry: InstrumentRegistry, parent=None):
        super().__init__("Hangar", parent)
        self._registry = registry
        self.setObjectName("HangarDock")
        self.setAllowedAreas(Qt.DockWidgetArea.LeftDockWidgetArea |
                             Qt.DockWidgetArea.RightDockWidgetArea)

        # Tema di default per il rendering delle thumbnail
        self._default_theme = build_default_themes().default()

        # Cache delle thumbnail (type_id → QPixmap)
        self._thumb_cache: dict[str, QPixmap] = {}

        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(6)

        # --- Barra di ricerca ---
        self._search = QLineEdit()
        self._search.setPlaceholderText("Cerca strumento...")
        self._search.setClearButtonEnabled(True)
        self._search.textChanged.connect(self._apply_filters)
        layout.addWidget(self._search)

        # --- Filtro stile + toggle vista ---
        filter_row = QHBoxLayout()
        filter_row.setSpacing(4)

        self._style_filter = QComboBox()
        self._style_filter.addItem("Tutti gli stili", "")
        for style in STYLE_ORDER:
            self._style_filter.addItem(style, style)
        self._style_filter.currentIndexChanged.connect(self._apply_filters)
        filter_row.addWidget(self._style_filter, 1)

        self._view_toggle = QToolButton()
        self._view_toggle.setCheckable(True)
        self._view_toggle.setChecked(True)
        self._view_toggle.setAutoRaise(True)
        self._view_toggle.setToolTip("Alterna miniature / lista")
        filter_row.addWidget(self._view_toggle)

        layout.addLayout(filter_row)

        # --- Lista strumenti ---
        self._list = InstrumentList()
        self._list.setDragEnabled(True)
        self._list.itemDoubleClicked.connect(self._on_double_click)
        layout.addWidget(self._list)

        self.setWidget(container)

        # Popola la lista e collega il toggle
        self._populate()
        self._view_toggle.toggled.connect(self._toggle_view_mode)
        self._toggle_view_mode(True)

    # =========================================================================
    # POPOLAMENTO
    # =========================================================================

    def _populate(self):
        """Costruisce la lista raggruppata per categoria."""
        self._list.clear()

        try:
            protos = self._registry.all_prototypes()
        except AttributeError:
            protos = self._registry.all()

        # Raggruppa per categoria mantenendo l'ordine
        categories: dict[str, list] = {}
        for p in protos:
            categories.setdefault(p.category, []).append(p)

        for category, items in categories.items():
            # Intestazione categoria
            header = QListWidgetItem(category)
            header.setFlags(Qt.ItemFlag.NoItemFlags)
            header.setForeground(Qt.GlobalColor.gray)
            font = header.font()
            font.setBold(True)
            header.setFont(font)
            header.setData(Qt.ItemDataRole.UserRole, None)
            self._list.addItem(header)

            for proto in items:
                item = QListWidgetItem(proto.display_name)
                item.setData(Qt.ItemDataRole.UserRole, proto)
                item.setToolTip(proto.description)
                thumb = self._get_thumbnail(proto)
                if thumb:
                    item.setIcon(QIcon(thumb))
                self._list.addItem(item)

    # =========================================================================
    # THUMBNAIL
    # =========================================================================

    def _get_thumbnail(self, proto) -> QPixmap | None:
        """Restituisce la thumbnail (dalla cache o renderizzandola)."""
        if proto.type_id in self._thumb_cache:
            return self._thumb_cache[proto.type_id]
        pixmap = self._render_thumbnail(proto)
        if pixmap:
            self._thumb_cache[proto.type_id] = pixmap
        return pixmap

    def _render_thumbnail(self, proto, target: int = 48) -> QPixmap | None:
        """Renderizza lo strumento in una QPixmap ridotta."""
        try:
            item = InstrumentFactory.create_item(proto)

            # Imposta il tema per gli strumenti Base
            if hasattr(item, "set_theme") and self._default_theme:
                item.set_theme(self._default_theme)

            # Dati di default per posizionare le lancette
            if hasattr(item, "update_data"):
                item.update_data(TelemetryData())

            w, h = int(proto.width), int(proto.height)
            canvas = QPixmap(w, h)
            canvas.fill(Qt.GlobalColor.transparent)

            painter = QPainter(canvas)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
            option = QStyleOptionGraphicsItem()
            item.paint(painter, option, None)
            painter.end()

            return canvas.scaled(target, target,
                                 Qt.AspectRatioMode.KeepAspectRatio,
                                 Qt.TransformationMode.SmoothTransformation)
        except Exception:
            return None

    # =========================================================================
    # TOGGLE VISTA (miniature / lista)
    # =========================================================================

    def _toggle_view_mode(self, use_thumbnails: bool):
        """Alterna tra vista miniature e lista semplice."""
        if use_thumbnails:
            self._list.setIconSize(QSize(52, 52))
            self._list.setSpacing(4)
            self._view_toggle.setText("☰")
            self._view_toggle.setToolTip("Passa alla vista lista")
        else:
            self._list.setIconSize(QSize(0, 0))
            self._list.setSpacing(1)
            self._view_toggle.setText("⊞")
            self._view_toggle.setToolTip("Passa alla vista miniature")

    # =========================================================================
    # FILTRI (ricerca + stile)
    # =========================================================================

    def _apply_filters(self):
        """Filtra la lista in base a testo di ricerca e stile selezionato."""
        query = self._search.text().strip().lower()
        style = self._style_filter.currentData()

        for i in range(self._list.count()):
            item = self._list.item(i)
            proto = item.data(Qt.ItemDataRole.UserRole)

            if proto is None:
                # Intestazione categoria: la gestisco dopo
                continue

            match_search = True
            if query:
                haystack = f"{proto.display_name} {proto.type_id} {proto.description}".lower()
                match_search = query in haystack

            match_style = True
            if style:
                match_style = getattr(proto, "style", "Base") == style

            item.setHidden(not (match_search and match_style))

        # Nascondi le intestazioni di categoria senza elementi visibili
        self._update_category_headers()

    def _update_category_headers(self):
        """Nasconde le intestazioni di categoria se tutti gli strumenti sono filtrati."""
        current_header = None
        visible_in_section = 0

        for i in range(self._list.count()):
            item = self._list.item(i)
            proto = item.data(Qt.ItemDataRole.UserRole)

            if proto is None:
                # Chiudi la sezione precedente
                if current_header is not None:
                    current_header.setHidden(visible_in_section == 0)
                current_header = item
                visible_in_section = 0
            else:
                if not item.isHidden():
                    visible_in_section += 1

        # Chiudi l'ultima sezione
        if current_header is not None:
            current_header.setHidden(visible_in_section == 0)

    # =========================================================================
    # INTERAZIONE
    # =========================================================================

    def _on_double_click(self, item: QListWidgetItem):
        proto = item.data(Qt.ItemDataRole.UserRole)
        if proto is None:
            return
        self.instrument_requested.emit(proto.type_id)


class InstrumentList(QListWidget):
    """QListWidget che supporta il drag degli strumenti verso la scena."""

    def startDrag(self, supportedActions):
        item = self.currentItem()
        if item is None:
            return
        proto = item.data(Qt.ItemDataRole.UserRole)
        if proto is None:
            return

        mime = QMimeData()
        mime.setData(MIME_INSTRUMENT, proto.type_id.encode("utf-8"))

        drag = QDrag(self)
        drag.setMimeData(mime)

        # Usa la thumbnail come immagine del drag
        icon = item.icon()
        if icon and not icon.isNull():
            drag.setPixmap(icon.pixmap(48, 48))

        drag.exec(Qt.DropAction.CopyAction)