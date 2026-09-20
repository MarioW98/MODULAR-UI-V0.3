from __future__ import annotations
from dataclasses import dataclass


@dataclass(frozen=True)
class InstrumentPrototype:
    """Descrizione statica di uno strumento disponibile nell'Hangar."""
    type_id: str
    display_name: str
    category: str
    width: float
    height: float
    color: str
    description: str = ""


class InstrumentRegistry:
    """Catalogo centrale degli strumenti."""

    def __init__(self) -> None:
        self._prototypes: dict[str, InstrumentPrototype] = {}
        self._category_order: list[str] = []

    def register(self, p: InstrumentPrototype) -> None:
        if p.type_id in self._prototypes:
            raise ValueError(f"Già registrato: {p.type_id}")
        self._prototypes[p.type_id] = p
        if p.category not in self._category_order:
            self._category_order.append(p.category)

    def get(self, type_id: str) -> InstrumentPrototype | None:
        return self._prototypes.get(type_id)

    def categories(self) -> tuple[str, ...]:
        return tuple(self._category_order)

    def prototypes_in_category(self, category: str) -> list[InstrumentPrototype]:
        return sorted(
            (p for p in self._prototypes.values() if p.category == category),
            key=lambda p: p.display_name,
        )

    def all_prototypes(self) -> list[InstrumentPrototype]:
        return list(self._prototypes.values())


def build_default_registry() -> InstrumentRegistry:
    r = InstrumentRegistry()

    # --- Volo ---
    r.register(InstrumentPrototype("flight-airspeed", "Airspeed", "Volo",
                                   200, 200, "#2E7D32", "Velocità indicata"))
    r.register(InstrumentPrototype("flight-airspeed-pro", "Airspeed Pro", "Volo",
                                   200, 200, "#1B5E20", "Velocità indicata (Professional)"))
    r.register(InstrumentPrototype("flight-altimeter", "Altimeter", "Volo",
                                   200, 200, "#1E88E5", "Altimetro"))
    r.register(InstrumentPrototype("flight-attitude", "Attitude", "Volo",
                                   220, 220, "#5E35B1", "Assetto"))
    r.register(InstrumentPrototype("flight-attitude-full", "Attitude Full", "Volo",
                                   240, 240, "#4527A0", "Orizzonte artificiale completo"))
    r.register(InstrumentPrototype("flight-attitude-square", "Attitude Square", "Volo",
                                   240, 240, "#311B92", "Orizzonte artificiale quadrato"))
    r.register(InstrumentPrototype("flight-vsi-pro", "VSI Pro", "Volo",
                                   200, 200, "#1A237E", "Variometro (Professional)"))
    ## --- Digital ---
    r.register(InstrumentPrototype("flight-altimeter-digital", "Altimeter Digital", "Volo",
                                   70, 150, "#1E88E5", "Altimetro digitale"))
    r.register(InstrumentPrototype("flight-vsi-digital", "VSI Digital", "Volo",
                                   70, 150, "#283593", "Variometro digitale"))

    # --- Motore ---
    r.register(InstrumentPrototype("engine-rpm", "RPM", "Motore",
                                   200, 200, "#E53935", "Giri motore"))
    r.register(InstrumentPrototype("engine-oil-temp", "Oil Temp", "Motore",
                                   180, 180, "#FB8C00", "Temperatura olio"))

    # --- Navigazione ---
    r.register(InstrumentPrototype("nav-heading", "Heading", "Navigazione",
                                   200, 200, "#00897B", "Indicatore di prua"))
    r.register(InstrumentPrototype("nav-heading-pro", "Heading Pro", "Navigazione",
                                   200, 200, "#004D40", "Indicatore di prua (Professional)"))
    r.register(InstrumentPrototype("flight-altimeter-pro", "Altimeter Pro", "Volo",
                                   200, 200, "#0D47A1", "Altimetro (Professional)"))

    return r