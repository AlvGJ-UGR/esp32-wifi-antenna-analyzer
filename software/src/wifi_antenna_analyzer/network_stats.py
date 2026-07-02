"""Estadísticas del escaneo en vivo y series temporales de RSSI (Fase 5).

Dos responsabilidades, ambas lógica pura sin I/O:

- `compute_scan_statistics`: resumen instantáneo de la última vista
  de red por BSSID (nº de redes, RSSI medio/min/max, canal más
  ocupado, distribución de seguridad).
- `ScanHistory`: acumula el histórico de RSSI por BSSID a lo largo
  del tiempo (con un límite de puntos por red) para poder pintarlo
  en la pestaña "Gráficas".

Nombrado `network_stats.py` (no `statistics.py`) para no repetir el
nombre del módulo de la librería estándar que ya se usa en
`models.py`.
"""

from __future__ import annotations

import statistics as stats
from collections import Counter, deque
from collections.abc import Iterable
from dataclasses import dataclass, field
from datetime import datetime

from .models import NetworkSample

DEFAULT_HISTORY_POINTS = 200


@dataclass(frozen=True, slots=True)
class ScanStatistics:
    """Resumen agregado de un conjunto de redes vistas en un instante dado."""

    network_count: int
    rssi_mean: float | None
    rssi_min: int | None
    rssi_max: int | None
    channel_counts: dict[int, int]
    security_counts: dict[str, int]

    @property
    def busiest_channel(self) -> int | None:
        """Canal con más redes; None si no hay datos. Empate: el de menor número."""
        if not self.channel_counts:
            return None
        return max(sorted(self.channel_counts), key=lambda ch: self.channel_counts[ch])

    @property
    def busiest_channel_count(self) -> int:
        channel = self.busiest_channel
        return self.channel_counts.get(channel, 0) if channel is not None else 0


def compute_scan_statistics(samples: Iterable[NetworkSample]) -> ScanStatistics:
    """Calcula estadísticas a partir de una vista actual de la red (una muestra por BSSID).

    Si se pasan varias muestras del mismo BSSID (p.ej. el histórico
    completo de varios escaneos en vez de solo el último), se
    deduplican quedándose con la última por orden de iteración —
    igual que hace `ScannerTab.upsert_sample` en la GUI — para no
    contar la misma red varias veces.
    """
    latest_by_bssid: dict[str, NetworkSample] = {}
    for sample in samples:
        latest_by_bssid[sample.bssid] = sample
    current = list(latest_by_bssid.values())

    if not current:
        return ScanStatistics(
            network_count=0,
            rssi_mean=None,
            rssi_min=None,
            rssi_max=None,
            channel_counts={},
            security_counts={},
        )

    rssi_values = [sample.rssi for sample in current]
    channel_counts = dict(Counter(sample.channel for sample in current))
    security_counts = dict(Counter(sample.security_name for sample in current))

    return ScanStatistics(
        network_count=len(current),
        rssi_mean=stats.fmean(rssi_values),
        rssi_min=min(rssi_values),
        rssi_max=max(rssi_values),
        channel_counts=channel_counts,
        security_counts=security_counts,
    )


@dataclass
class NetworkHistory:
    """RSSI de una única red a lo largo del tiempo, acotado a los últimos N puntos."""

    ssid: str
    bssid: str
    max_points: int = DEFAULT_HISTORY_POINTS
    points: deque[tuple[datetime, int]] = field(init=False, repr=False)

    def __post_init__(self) -> None:
        self.points = deque(maxlen=self.max_points)

    def add(self, timestamp: datetime, rssi: int) -> None:
        self.points.append((timestamp, rssi))

    @property
    def latest_rssi(self) -> int | None:
        return self.points[-1][1] if self.points else None


class ScanHistory:
    """Agrupa `NetworkHistory` por BSSID según van llegando `NetworkSample`.

    Pensado para vivir durante toda la sesión de conexión de la GUI
    (se reinicia con `clear()` al desconectar), no para persistirse
    entre sesiones.
    """

    def __init__(self, max_points_per_network: int = DEFAULT_HISTORY_POINTS) -> None:
        self._max_points = max_points_per_network
        self._by_bssid: dict[str, NetworkHistory] = {}

    def add_sample(self, sample: NetworkSample) -> None:
        history = self._by_bssid.get(sample.bssid)
        if history is None:
            history = NetworkHistory(
                ssid=sample.ssid, bssid=sample.bssid, max_points=self._max_points
            )
            self._by_bssid[sample.bssid] = history
        history.add(sample.timestamp, sample.rssi)

    def get(self, bssid: str) -> NetworkHistory | None:
        return self._by_bssid.get(bssid)

    def histories(self) -> list[NetworkHistory]:
        """Todas las redes con histórico, ordenadas por RSSI más reciente (mejor primero)."""
        return sorted(
            self._by_bssid.values(),
            key=lambda h: h.latest_rssi if h.latest_rssi is not None else float("-inf"),
            reverse=True,
        )

    def clear(self) -> None:
        self._by_bssid.clear()
