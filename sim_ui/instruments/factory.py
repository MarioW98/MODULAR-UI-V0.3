from __future__ import annotations
from ..core.prototype import InstrumentPrototype
from .base import BaseInstrument, PlaceholderInstrument
from .professional import (
            AirspeedIndicatorProfessional,
            HeadingIndicatorProfessional,
            AltimeterProfessional,
        )
from .advance_instr import AttitudeAdvance
from .comfort_instr import AirspeedComfort, AltimeterComfort, VSIComfort, HeadingComfort, TurnCoordinatorComfort

class InstrumentFactory:
    _map: dict[str, type] = {}

    @classmethod
    def _build(cls):
        # from .specific import (
        #     AirspeedIndicator, Altimeter, DigitalAltimeter,
        #     AttitudeIndicator, AttitudeIndicatorFull, AttitudeIndicatorSquare,
        #     RPMGauge, OilTempGauge, HeadingIndicator, DigitalVSI, TurnCoordinator,
        # )
        from .gauges import (
            AirspeedIndicator, Altimeter, RPMGauge, OilTempGauge,
            HeadingIndicator,TurnCoordinator,
            )
        from .digital import (
            DigitalAltimeter, DigitalVSI
        )
        from .attitude import (
            AttitudeIndicator, AttitudeIndicatorFull, AttitudeIndicatorSquare
        )

        from .professional import (
            AirspeedIndicatorProfessional,
            HeadingIndicatorProfessional, VSIGaugeProfessional, TurnCoordinatorProfessional
        )

        cls._map = {
            # --- Base ---
            "flight-airspeed": AirspeedIndicator,
            "flight-altimeter": Altimeter,
            "flight-altimeter-digital": DigitalAltimeter,
            "flight-attitude": AttitudeIndicator,
            "flight-attitude-full": AttitudeIndicatorFull,
            "flight-attitude-square": AttitudeIndicatorSquare,
            "engine-rpm": RPMGauge,
            "engine-oil-temp": OilTempGauge,
            "nav-heading": HeadingIndicator,
            "flight-vsi-digital": DigitalVSI,
            "flight-turn-coord": TurnCoordinator,

            # --- Professional ---
            "flight-airspeed-pro": AirspeedIndicatorProfessional,
            "nav-heading-pro": HeadingIndicatorProfessional,
            "flight-altimeter-pro": AltimeterProfessional,
            "flight-vsi-pro": VSIGaugeProfessional,
            "flight-turn-coord-pro": TurnCoordinatorProfessional,

            # --- Advanced ---
            "adv-sq-attitude": AttitudeAdvance,

            # --- Comfort ---
            "comfort-airspeed": AirspeedComfort,
            "comfort-altimeter": AltimeterComfort,
            "comfort-vsi": VSIComfort,
            "comfort-heading": HeadingComfort,
            "comfort-turn-coord": TurnCoordinatorComfort,

        }

    @classmethod
    def create_item(cls, proto: InstrumentPrototype) -> BaseInstrument:
        if not cls._map:
            cls._build()
        klass = cls._map.get(proto.type_id, PlaceholderInstrument)
        return klass(proto)