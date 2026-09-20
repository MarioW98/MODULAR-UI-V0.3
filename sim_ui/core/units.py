from __future__ import annotations
from dataclasses import dataclass


@dataclass(frozen=True)
class UnitDefinition:
    unit_id: str
    label: str
    factor: float
    decimals: int = 0
    major_step: float | None = None


AIRSPEED_UNITS = [
    UnitDefinition("kt",  "KNOTS", 1.0,      0, 20.0),
    UnitDefinition("kmh", "KM/H",  1.852,    0, 50.0),
    UnitDefinition("mph", "MPH",   1.15078,  0, 25.0),
    UnitDefinition("mps", "M/S",   0.514444, 1, 10.0),
]

ALTITUDE_UNITS = [
    UnitDefinition("ft", "FEET",   1.0,    0, None),
    UnitDefinition("m",  "METERS", 0.3048, 0, None),
]
VSI_UNITS = [
    UnitDefinition("fpm", "FT/MIN", 1.0, 0, 500.0),
    UnitDefinition("mps", "M/S", 0.00508, 1, 2.0),
]