from __future__ import annotations
import math
from dataclasses import dataclass
from PySide6.QtCore import QTimer, QObject, Signal


@dataclass
class TelemetryData:
    airspeed: float = 0.0
    altitude: float = 0.0
    rpm: float = 0.0
    oil_temp: float = 0.0
    heading: float = 0.0
    pitch: float = 0.0
    roll: float = 0.0
    turn_rate: float = 0.0 
    manifold_pressure: float = 0.0
    fuel_flow: float = 0.0
    vertical_speed: float = 0.0


class TelemetryAdapter(QObject):
    telemetry_updated = Signal(TelemetryData)

    def start(self): pass
    def stop(self): pass


class MockTelemetryAdapter(TelemetryAdapter):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._time = 0.0
        self._interval_ms = 50  # Default: 20 FPS
        self._prev_heading = 0.0

    def start(self, interval_ms: int = None):
        if interval_ms is not None:
            self._interval_ms = interval_ms
        self._timer.start(self._interval_ms)

    def stop(self):
        self._timer.stop()

    def set_interval(self, interval_ms: int):
        """Cambia la frequenza di aggiornamento, anche a runtime."""
        self._interval_ms = interval_ms
        if self._timer.isActive():
            self._timer.stop()
            self._timer.start(self._interval_ms)

    def _tick(self):
        dt = self._interval_ms / 1000.0
        self._time += dt
        t = self._time

        # Rate di virata variabile: oscilla tra -5 e +5 °/sec
        # L'aereo vira a destra, poi dritto, poi a sinistra
        heading_rate = 5.0 * math.sin(t * 0.25)

        # Heading calcolato come integrale del rate
        heading = (self._prev_heading + heading_rate * dt) % 360

        # Turn rate effettivo (derivata dell'heading con gestione wrap-around)
        delta_heading = heading - self._prev_heading
        if delta_heading > 180:
            delta_heading -= 360
        elif delta_heading < -180:
            delta_heading += 360
        turn_rate = delta_heading / dt if dt > 0 else 0.0

        self._prev_heading = heading

        self.telemetry_updated.emit(TelemetryData(
            airspeed=120 + 35 * math.sin(t * 0.4),
            altitude=3500 + 800 * math.sin(t * 0.25),
            rpm=2200 + 350 * math.sin(t * 0.6),
            oil_temp=85 + 15 * math.sin(t * 0.15),
            heading=heading,
            pitch=55 * math.sin(t * 0.35),
            roll=18 * math.sin(t * 0.5),
            turn_rate=turn_rate,
            manifold_pressure=22 + 4 * math.sin(t * 0.3),
            fuel_flow=8 + 2 * math.sin(t * 0.2),
            vertical_speed=1200 * math.sin(t * 0.15),
        ))



class ExternalTelemetryAdapter(TelemetryAdapter):
    def start(self): pass
    def stop(self): pass

    def push_data(self, data: dict | TelemetryData):
        if isinstance(data, dict):
            telemetry = TelemetryData(
                **{k: data.get(k, 0.0) for k in TelemetryData.__dataclass_fields__}
            )
        else:
            telemetry = data
        self.telemetry_updated.emit(telemetry)