"""Lógica del modo Benchmark (Fase 3).

Acumula las muestras de RSSI de cada red (agrupadas por BSSID) que
llegan durante una ventana de tiempo, y al cerrarla calcula
estadísticas agregadas por red (media, desviación, mín, máx).

Igual que `SerialLink.parse_line`, esto es deliberadamente puro: no
sabe nada de hilos, del puerto serie ni del reloj real. Quien lo usa
(la GUI o la CLI) decide cuándo empieza y cuándo termina la ventana;
eso hace que se pueda testear con datos sintéticos.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .models import BenchmarkResult, NetworkSample


@dataclass
class BenchmarkSession:
    """Agrupa NetworkSample por BSSID durante una ventana de benchmark."""

    antenna: str
    duration_seconds: float = 30.0
    _results: dict[str, BenchmarkResult] = field(default_factory=dict, init=False, repr=False)

    def add_sample(self, sample: NetworkSample) -> None:
        """Añade una muestra, agrupándola por BSSID (no por SSID)."""
        result = self._results.get(sample.bssid)
        if result is None:
            result = BenchmarkResult(bssid=sample.bssid, ssid=sample.ssid, antenna=self.antenna)
            self._results[sample.bssid] = result
        result.add_sample(sample.rssi)

    @property
    def network_count(self) -> int:
        return len(self._results)

    @property
    def sample_count(self) -> int:
        return sum(result.count for result in self._results.values())

    def results(self) -> list[BenchmarkResult]:
        """Resultados ordenados por RSSI medio descendente (mejor señal primero).

        Las redes sin muestras (no debería pasar, pero por seguridad)
        quedan al final.
        """
        return sorted(
            self._results.values(),
            key=lambda result: result.mean if result.mean is not None else float("-inf"),
            reverse=True,
        )
