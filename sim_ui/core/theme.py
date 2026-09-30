from __future__ import annotations
from dataclasses import dataclass, field

from PySide6.QtGui import QColor


# =============================================================================
# CLASSE TEMA
# =============================================================================

@dataclass
class InstrumentTheme:
    """Parametri visivi per il rendering degli strumenti."""

    # --- Identificazione ---
    theme_id: str
    display_name: str
    family: str = ""
    description: str = ""

    # --- Bezel (cornice esterna) ---
    bezel_color: QColor = field(default_factory=lambda: QColor(40, 40, 45))
    bezel_ring_color: QColor = field(default_factory=lambda: QColor(30, 30, 34))

    # --- Quadrante (sfondo interno) ---
    dial_color: QColor = field(default_factory=lambda: QColor(20, 22, 28))

    # --- Tacche ---
    tick_major_color: QColor = field(default_factory=lambda: QColor(220, 220, 220))
    tick_minor_color: QColor = field(default_factory=lambda: QColor(160, 160, 160))
    tick_major_width: float = 2.0
    tick_minor_width: float = 1.0

    # --- Testo ---
    text_color: QColor = field(default_factory=lambda: QColor(220, 220, 220))
    text_secondary_color: QColor = field(default_factory=lambda: QColor(180, 190, 200))
    text_tertiary_color: QColor = field(default_factory=lambda: QColor(140, 150, 160))
    font_family: str = ""
    font_size_numbers: int = 11
    font_size_title: int = 10
    font_size_unit: int = 9

    # --- Lancette ---
    needle_color: QColor = field(default_factory=lambda: QColor(255, 255, 255))
    needle_hub_color: QColor = field(default_factory=lambda: QColor(90, 90, 95))

    # --- Attitude (cielo / terra) ---
    sky_color: QColor = field(default_factory=lambda: QColor(55, 110, 190))
    ground_color: QColor = field(default_factory=lambda: QColor(120, 75, 35))
    horizon_color: QColor = field(default_factory=lambda: QColor(255, 255, 255))
    pitch_ladder_color: QColor = field(default_factory=lambda: QColor(255, 255, 255))

    # --- Riferimenti fissi ---
    reference_color: QColor = field(default_factory=lambda: QColor(255, 160, 0))
    aircraft_symbol_color: QColor = field(default_factory=lambda: QColor(255, 200, 0))

    # --- Selezione e scena ---
    selection_color: QColor = field(default_factory=lambda: QColor(255, 193, 7))
    scene_background: QColor = field(default_factory=lambda: QColor(15, 18, 25))
    grid_color: QColor = field(default_factory=lambda: QColor(255, 255, 255, 18))


# =============================================================================
# REGISTRY DEI TEMI
# =============================================================================

class ThemeRegistry:
    """Catalogo dei temi disponibili."""

    def __init__(self) -> None:
        self._themes: dict[str, InstrumentTheme] = {}
        self._order: list[str] = []
        self._default_id: str | None = None

    def register(self, theme: InstrumentTheme, is_default: bool = False) -> None:
        if theme.theme_id in self._themes:
            raise ValueError(f"Tema già registrato: {theme.theme_id}")
        self._themes[theme.theme_id] = theme
        self._order.append(theme.theme_id)
        if is_default or self._default_id is None:
            self._default_id = theme.theme_id

    def get(self, theme_id: str) -> InstrumentTheme | None:
        return self._themes.get(theme_id)

    def default(self) -> InstrumentTheme | None:
        if self._default_id:
            return self._themes.get(self._default_id)
        return next(iter(self._themes.values()), None) if self._themes else None

    def themes(self) -> list[InstrumentTheme]:
        return [self._themes[tid] for tid in self._order]

    def theme_ids(self) -> tuple[str, ...]:
        return tuple(self._order)

    def set_default(self, theme_id: str) -> None:
        if theme_id in self._themes:
            self._default_id = theme_id


# =============================================================================
# TEMA BASE
# =============================================================================

def _theme_base() -> InstrumentTheme:
    """Tema Base: replica ESATTA dello stile attuale."""
    return InstrumentTheme(
        theme_id="base",
        display_name="Base",
        family="base",
        description="Stile originale del simulatore",
        bezel_color=QColor(40, 40, 45),
        bezel_ring_color=QColor(30, 30, 34),
        dial_color=QColor(20, 22, 28),
        tick_major_color=QColor(220, 220, 220),
        tick_minor_color=QColor(160, 160, 160),
        tick_major_width=2.0,
        tick_minor_width=1.0,
        text_color=QColor(220, 220, 220),
        text_secondary_color=QColor(180, 190, 200),
        text_tertiary_color=QColor(140, 150, 160),
        font_family="",
        needle_color=QColor(255, 255, 255),
        needle_hub_color=QColor(90, 90, 95),
        sky_color=QColor(55, 110, 190),
        ground_color=QColor(120, 75, 35),
        horizon_color=QColor(255, 255, 255),
        pitch_ladder_color=QColor(255, 255, 255),
        reference_color=QColor(255, 160, 0),
        aircraft_symbol_color=QColor(255, 200, 0),
        scene_background=QColor(230, 218, 188),  # Canapa
        grid_color=QColor(180, 168, 145),         # Canapa scuro per contrasto
        selection_color=QColor(0, 120, 215),
        # selection_color=QColor(255, 193, 7),
        # scene_background=QColor(15, 18, 25),
        # grid_color=QColor(255, 255, 255, 18),
    )


# =============================================================================
# TEMA NIGHT (alternativa di test)
# =============================================================================

def _theme_night() -> InstrumentTheme:
    """
    Tema Night: toni blu scuro con accenti ciano.
    Serve come verifica del meccanismo di cambio tema.
    """
    return InstrumentTheme(
        theme_id="night",
        display_name="Night",
        family="night",
        description="Tema notturno con accenti ciano",
        bezel_color=QColor(18, 24, 38),
        bezel_ring_color=QColor(12, 16, 28),
        dial_color=QColor(8, 12, 20),
        tick_major_color=QColor(100, 200, 230),
        tick_minor_color=QColor(60, 130, 160),
        tick_major_width=2.0,
        tick_minor_width=1.0,
        text_color=QColor(140, 220, 240),
        text_secondary_color=QColor(100, 170, 200),
        text_tertiary_color=QColor(70, 130, 160),
        font_family="",
        needle_color=QColor(160, 230, 250),
        needle_hub_color=QColor(40, 70, 90),
        sky_color=QColor(20, 40, 70),
        ground_color=QColor(25, 50, 40),
        horizon_color=QColor(120, 200, 220),
        pitch_ladder_color=QColor(110, 190, 210),
        reference_color=QColor(100, 220, 200),
        aircraft_symbol_color=QColor(150, 230, 240),
        scene_background=QColor(15, 18, 25),      # Attuale scuro
        grid_color=QColor(40, 45, 55),            # Grigio scuro
        selection_color=QColor(0, 200, 200),
        # selection_color=QColor(80, 200, 220),
        # scene_background=QColor(10, 14, 20),
        # grid_color=QColor(100, 180, 200, 12),
    )




# =============================================================================
# COSTRUZIONE DEFAULT
# =============================================================================

def build_default_themes() -> ThemeRegistry:
    """Crea il registry con i temi disponibili."""
    registry = ThemeRegistry()
    registry.register(_theme_base(), is_default=True)
    registry.register(_theme_night())
    return registry