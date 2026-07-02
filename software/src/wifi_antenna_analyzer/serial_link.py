"""Conexión serie con el ESP32 y parseo del protocolo JSON por línea."""

from __future__ import annotations

import json
import logging
from collections.abc import Iterator
from datetime import datetime
from typing import Protocol

from .models import NetworkSample, ScanEnd, SecurityType

logger = logging.getLogger(__name__)


class SerialLinkError(RuntimeError):
    """Error al abrir o leer del puerto serie."""


class _SerialLike(Protocol):
    """Subconjunto de pyserial.Serial que necesitamos (facilita el testing)."""

    def readline(self) -> bytes: ...
    def close(self) -> None: ...
    @property
    def is_open(self) -> bool: ...


class SerialLink:
    """Lee el flujo de eventos JSON que manda el firmware del ESP32.

    Uso típico:
        with SerialLink(port="COM5", antenna="dipolo_5dbi") as link:
            for event in link.read_events():
                ...
    """

    def __init__(
        self,
        port: str,
        baudrate: int = 115200,
        timeout: float = 1.0,
        antenna: str = "default",
    ) -> None:
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        self.antenna = antenna
        self._serial: _SerialLike | None = None

    def connect(self) -> None:
        """Abre el puerto serie. Lanza SerialLinkError si falla."""
        import serial  # import perezoso: así los tests pueden inyectar un fake sin pyserial

        try:
            self._serial = serial.Serial(self.port, self.baudrate, timeout=self.timeout)
        except serial.SerialException as exc:
            raise SerialLinkError(f"No se pudo abrir el puerto {self.port}: {exc}") from exc
        logger.info("Conectado a %s @ %d baudios", self.port, self.baudrate)

    def close(self) -> None:
        if self._serial is not None and self._serial.is_open:
            self._serial.close()
            logger.info("Puerto %s cerrado", self.port)

    def attach(self, serial_like: _SerialLike) -> None:
        """Inyecta una conexión ya abierta (real o fake). Útil para tests."""
        self._serial = serial_like

    def read_events(self) -> Iterator[NetworkSample | ScanEnd]:
        """Generador infinito de eventos parseados. Bloquea según el timeout configurado."""
        if self._serial is None:
            raise SerialLinkError("Llama a connect() o attach() antes de leer eventos")

        while True:
            raw = self._serial.readline()
            if not raw:
                continue

            line = raw.decode("utf-8", errors="ignore").strip()
            if not line:
                continue
            if line.startswith("#"):
                logger.debug("Firmware: %s", line)
                continue

            event = self.parse_line(line, antenna=self.antenna)
            if event is not None:
                yield event

    @staticmethod
    def parse_line(line: str, antenna: str = "default") -> NetworkSample | ScanEnd | None:
        """Convierte una línea de texto en NetworkSample/ScanEnd, o None si no es válida.

        Método estático y puro (sin I/O) a propósito: así se puede testear
        el protocolo sin necesidad de hardware ni de mockear pyserial.
        """
        try:
            data = json.loads(line)
        except json.JSONDecodeError:
            logger.debug("Línea descartada (JSON inválido): %r", line)
            return None

        if data.get("event") == "scan_end":
            return ScanEnd(
                scan_id=data.get("scan", -1),
                network_count=data.get("count", 0),
            )

        required = ("scan", "mac", "rssi", "channel")
        if not all(key in data for key in required):
            logger.debug("Evento incompleto, descartado: %s", data)
            return None

        return NetworkSample(
            scan_id=data["scan"],
            ssid=data.get("ssid") or "(oculta)",
            bssid=data["mac"],
            rssi=data["rssi"],
            channel=data["channel"],
            security=SecurityType.from_code(data.get("security")),
            timestamp=datetime.now(),
            antenna=antenna,
        )

    def __enter__(self) -> SerialLink:
        self.connect()
        return self

    def __exit__(self, *exc_info: object) -> None:
        self.close()
