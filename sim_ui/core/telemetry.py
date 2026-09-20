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
        self._time += self._interval_ms / 1000.0
        t = self._time
        self.telemetry_updated.emit(TelemetryData(
            airspeed=120 + 35 * math.sin(t * 0.4),
            altitude=3500 + 800 * math.sin(t * 0.25),
            rpm=2200 + 350 * math.sin(t * 0.6),
            oil_temp=85 + 15 * math.sin(t * 0.15),
            heading=(t * 8) % 360,
            pitch=55 * math.sin(t * 0.35),
            roll=18 * math.sin(t * 0.5),
            manifold_pressure=22 + 4 * math.sin(t * 0.3),
            fuel_flow=8 + 2 * math.sin(t * 0.2),
            vertical_speed=500 * math.sin(t * 0.15),
            
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