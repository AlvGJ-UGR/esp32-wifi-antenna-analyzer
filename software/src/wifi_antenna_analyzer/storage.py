"""Persistencia de muestras de escaneo.

Hoy escribe a CSV. La interfaz está pensada para poder añadir un
backend SQLite en la Fase 5 sin tener que tocar quien la usa.
"""

from __future__ import annotations

import csv
from datetime import datetime
from pathlib import Path

from .models import NetworkSample


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
