"""Persistencia de muestras de escaneo.

Hoy escribe a CSV. La interfaz está pensada para poder añadir un
backend SQLite en la Fase 5 sin tener que tocar quien la usa.
"""

from __future__ import annotations

import csv
from collections.abc import Iterable
from datetime import datetime
from pathlib import Path

from .models import BenchmarkResult, NetworkSample


class ScanCsvWriter:
    """Escribe NetworkSample a un CSV, una fila por muestra, con flush inmediato.

    El nombre del fichero incluye la antena y un timestamp para no
    pisar resultados de pruebas anteriores.
    """

    FIELDNAMES = ["fecha", "hora", "antena", "scan", "ssid", "mac", "rssi", "channel", "security"]

    def __init__(self, outdir: Path | str, antenna: str) -> None:
        self.outdir = Path(outdir)
        self.outdir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_antenna = antenna.replace(" ", "_")
        self.path = self.outdir / f"scan_{safe_antenna}_{timestamp}.csv"

        self._file = self.path.open("w", newline="", encoding="utf-8")
        self._writer = csv.DictWriter(self._file, fieldnames=self.FIELDNAMES)
        self._writer.writeheader()

    def write(self, sample: NetworkSample) -> None:
        self._writer.writerow(
            {
                "fecha": sample.timestamp.strftime("%Y-%m-%d"),
                "hora": sample.timestamp.strftime("%H:%M:%S"),
                "antena": sample.antenna,
                "scan": sample.scan_id,
                "ssid": sample.ssid,
                "mac": sample.bssid,
                "rssi": sample.rssi,
                "channel": sample.channel,
                "security": sample.security_name,
            }
        )
        self._file.flush()

    def close(self) -> None:
        self._file.close()

    def __enter__(self) -> ScanCsvWriter:
        return self

    def __exit__(self, *exc_info: object) -> None:
        self.close()


class BenchmarkCsvWriter:
    """Escribe el resumen de un benchmark (una fila por red) a CSV.

    A diferencia de ScanCsvWriter (una fila por muestra cruda), aquí
    cada fila es ya el agregado de una red: media, desviación, etc.
    """

    FIELDNAMES = [
        "fecha",
        "hora",
        "antena",
        "ssid",
        "mac",
        "muestras",
        "rssi_medio",
        "rssi_desv",
        "rssi_min",
        "rssi_max",
    ]

    def __init__(self, outdir: Path | str, antenna: str) -> None:
        self.outdir = Path(outdir)
        self.outdir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_antenna = antenna.replace(" ", "_")
        self.path = self.outdir / f"benchmark_{safe_antenna}_{timestamp}.csv"

        self._file = self.path.open("w", newline="", encoding="utf-8")
        self._writer = csv.DictWriter(self._file, fieldnames=self.FIELDNAMES)
        self._writer.writeheader()

    def write_results(self, results: Iterable[BenchmarkResult]) -> None:
        now = datetime.now()
        for result in results:
            self._writer.writerow(
                {
                    "fecha": now.strftime("%Y-%m-%d"),
                    "hora": now.strftime("%H:%M:%S"),
                    "antena": result.antenna,
                    "ssid": result.ssid,
                    "mac": result.bssid,
                    "muestras": result.count,
                    "rssi_medio": f"{result.mean:.2f}" if result.mean is not None else "",
                    "rssi_desv": f"{result.stdev:.2f}" if result.stdev is not None else "",
                    "rssi_min": result.minimum if result.minimum is not None else "",
                    "rssi_max": result.maximum if result.maximum is not None else "",
                }
            )
        self._file.flush()

    def close(self) -> None:
        self._file.close()

    def __enter__(self) -> BenchmarkCsvWriter:
        return self

    def __exit__(self, *exc_info: object) -> None:
        self.close()
