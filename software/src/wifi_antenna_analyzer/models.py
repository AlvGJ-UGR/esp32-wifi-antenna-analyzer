"""Estructuras de datos compartidas por todo el paquete."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import IntEnum


class SecurityType(IntEnum):
    """Espejo de wifi_auth_mode_t (Arduino-ESP32) tal y como lo manda el firmware."""

    OPEN = 0
    WEP = 1
    WPA_PSK = 2
    WPA2_PSK = 3
    WPA_WPA2_PSK = 4
    WPA2_ENTERPRISE = 5
    WPA3_PSK = 6
    WPA2_WPA3_PSK = 7
    WAPI_PSK = 8

    @classmethod
    def from_code(cls, code: int | None) -> SecurityType | None:
        """Convierte el código numérico del firmware; None si es desconocido."""
        if code is None:
            return None
        try:
            return cls(code)
        except ValueError:
            return None


@dataclass(frozen=True, slots=True)
class NetworkSample:
    """Una red Wi-Fi detectada en un escaneo concreto, con una antena concreta."""

    scan_id: int
    ssid: str
    bssid: str
    rssi: int
    channel: int
    security: SecurityType | None
    timestamp: datetime
    antenna: str = "default"

    @property
    def security_name(self) -> str:
        return self.security.name if self.security is not None else "UNKNOWN"


@dataclass(frozen=True, slots=True)
class ScanEnd:
    """Marcador de fin de un ciclo de escaneo, enviado por el firmware."""

    scan_id: int
    network_count: int


@dataclass
class BenchmarkResult:
    """Estadísticas agregadas de una red a lo largo de una ventana de benchmark.

    Se rellena en la Fase 3 (modo benchmark); se deja definida ya para que
    storage.py y la futura GUI puedan tipar contra ella desde ahora.
    """

    bssid: str
    ssid: str
    antenna: str
    samples: list[int] = field(default_factory=list)

    def add_sample(self, rssi: int) -> None:
        self.samples.append(rssi)

    @property
    def count(self) -> int:
        return len(self.samples)

    @property
    def mean(self) -> float | None:
        return sum(self.samples) / len(self.samples) if self.samples else None

    @property
    def minimum(self) -> int | None:
        return min(self.samples) if self.samples else None

    @property
    def maximum(self) -> int | None:
        return max(self.samples) if self.samples else None
