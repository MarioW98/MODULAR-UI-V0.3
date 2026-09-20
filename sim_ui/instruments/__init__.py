from .base import BaseInstrument, UnitButtonsMixin, PlaceholderInstrument
from .circular import CircularGauge
from .specific import (
    AirspeedIndicator, Altimeter, DigitalAltimeter,
    AttitudeIndicator, AttitudeIndicatorFull, AttitudeIndicatorSquare,
    RPMGauge, OilTempGauge, HeadingIndicator, DigitalVSI
)
from .professional import (
    AirspeedIndicatorProfessional,
    HeadingIndicatorProfessional,
    AltimeterProfessional,
    VSIGaugeProfessional
)
from .factory import InstrumentFactory