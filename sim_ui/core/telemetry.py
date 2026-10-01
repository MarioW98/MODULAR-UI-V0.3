from __future__ import annotations

import math
from dataclasses import dataclass

from PySide6.QtCore import QTimer, QObject, Signal


@dataclass
class TelemetryData:
    """
    Dati di telemetria in unità SI.
    Il backend deve fornire valori in queste unità.
    """
    airspeed: float = 0.0           # m/s
    altitude: float = 0.0           # m
    vertical_speed: float = 0.0     # m/s (positivo = salita)
    heading: float = 0.0            # gradi (0-360)
    pitch: float = 0.0              # gradi (positivo = naso su)
    roll: float = 0.0               # gradi (positivo = ala destra giù)
    turn_rate: float = 0.0          # gradi/s (positivo = virata destra)
    rpm: float = 0.0                # giri/min
    oil_temp: float = 0.0           # °C
    manifold_pressure: float = 0.0  # kPa
    fuel_flow: float = 0.0          # kg/s


class TelemetryAdapter(QObject):
    telemetry_updated = Signal(TelemetryData)
    # Firma con default: gli adapter derivati possono aggiungere parametri
    # opzionali (es. MockTelemetryAdapter.start(interval_ms)) restando
    # conformi al principio LSP — ogni chiamata `adapter.start()` valida
    # sulla base resta valida su qualsiasi sottoclasse.
    def start(self, interval_ms: int | None = None): pass
    def stop(self): pass


class MockTelemetryAdapter(TelemetryAdapter):

    def __init__(self, parent=None):
        super().__init__(parent)
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._time = 0.0
        self._interval_ms = 50
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

        # --- Heading e turn rate (calcolo coerente) ---
        heading_rate = 5.0 * math.sin(t * 0.25)       # ±5 °/s
        heading = (self._prev_heading + heading_rate * dt) % 360.0

        delta_heading = heading - self._prev_heading
        if delta_heading > 180:
            delta_heading -= 360
        elif delta_heading < -180:
            delta_heading += 360
        turn_rate = delta_heading / dt if dt > 0 else 0.0
        self._prev_heading = heading

        # --- Emissione dati in unità SI ---
        self.telemetry_updated.emit(TelemetryData(
            airspeed=50.0 + 15.0 * math.sin(t * 0.4),          # 35–65 m/s
            altitude=1500.0 + 300.0 * math.sin(t * 0.25),      # 1200–1800 m
            vertical_speed=2.0 * math.sin(t * 0.15),            # ±2 m/s
            heading=heading,                                     # 0–360°
            pitch=5.0 * math.sin(t * 0.35),                      # ±5°
            roll=15.0 * math.sin(t * 0.5),                       # ±15°
            turn_rate=turn_rate,                                 # ±5 °/s
            rpm=2200.0 + 300.0 * math.sin(t * 0.6),             # 1900–2500 rpm
            oil_temp=85.0 + 10.0 * math.sin(t * 0.15),          # 75–95 °C
            manifold_pressure=90.0 + 10.0 * math.sin(t * 0.3),  # 80–100 kPa
            fuel_flow=0.003 + 0.001 * math.sin(t * 0.2),        # 2–4 g/s
        ))


class ExternalTelemetryAdapter(TelemetryAdapter):
    """
    Adapter per ricevere dati telemetrici da un backend esterno.
    Thread-safe: push_data() può essere chiamato da qualsiasi thread.
    L'emissione del segnale viene schedulata nel main thread Qt.
    """

    def start(self): pass
    def stop(self): pass

    def push_data(self, data: dict | TelemetryData):
        """
        Riceve dati telemetrici dal backend.
        
        Questo metodo è thread-safe: può essere chiamato da qualsiasi thread.
        L'emissione del segnale telemetry_updated viene schedulata nel main
        thread Qt usando QTimer.singleShot(0, ...).
        
        Args:
            data: dict con chiavi corrispondenti a TelemetryData, oppure
                  istanza di TelemetryData.
        """
        if isinstance(data, dict):
            telemetry = TelemetryData(
                **{k: data.get(k, 0.0) for k in TelemetryData.__dataclass_fields__}
            )
        else:
            telemetry = data
        
        # Schedula l'emissione nel main thread Qt
        # QTimer.singleShot(0, ...) esegue il callback nel prossimo ciclo
        # dell'event loop, garantendo thread-safety
        QTimer.singleShot(0, lambda: self.telemetry_updated.emit(telemetry))