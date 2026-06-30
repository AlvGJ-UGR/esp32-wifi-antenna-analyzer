"""Punto de entrada de consola: `waa-scan`.

Lee el flujo de eventos del ESP32, los muestra por consola y los
guarda en CSV. Es la versión "headless" de la herramienta; la GUI
(Fase 2) usa la misma capa serial_link/storage por debajo.
"""

from __future__ import annotations

import argparse
import logging
import sys

from .models import NetworkSample, ScanEnd
from .serial_link import SerialLink, SerialLinkError
from .storage import ScanCsvWriter

logger = logging.getLogger(__name__)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="waa-scan",
        description="Lector de consola del ESP32 Wi-Fi Antenna Analyzer",
    )
    parser.add_argument("--port", required=True, help="Puerto serie, ej: COM5 o /dev/ttyUSB0")
    parser.add_argument("--baud", type=int, default=115200, help="Velocidad serie (default 115200)")
    parser.add_argument(
        "--antenna",
        default="default",
        help="Nombre de la antena que estás probando ahora mismo (para el CSV)",
    )
    parser.add_argument(
        "--outdir",
        default="../data",
        help="Carpeta donde guardar el CSV (default: ../data)",
    )
    parser.add_argument(
        "-v", "--verbose", action="store_true", help="Activa logs de depuración (DEBUG)"
    )
    return parser.parse_args(argv)


def _format_sample(sample: NetworkSample) -> str:
    return (
        f"[scan {sample.scan_id}] {sample.ssid:25s} "
        f"RSSI={sample.rssi:4d} dBm  ch={sample.channel:2d}  "
        f"{sample.security_name:16s}  {sample.bssid}"
    )


def run(args: argparse.Namespace) -> int:
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s %(levelname)-8s %(message)s",
        datefmt="%H:%M:%S",
    )

    link = SerialLink(port=args.port, baudrate=args.baud, antenna=args.antenna)
    try:
        link.connect()
    except SerialLinkError as exc:
        logger.error(str(exc))
        return 1

    print(f"Conectado a {args.port} @ {args.baud} baudios. Antena: {args.antenna}")
    print("Esperando datos del ESP32... (Ctrl+C para salir)\n")

    with ScanCsvWriter(args.outdir, args.antenna) as writer:
        print(f"Guardando datos en: {writer.path}\n")
        try:
            for event in link.read_events():
                if isinstance(event, ScanEnd):
                    print(f"--- Fin escaneo #{event.scan_id}: {event.network_count} redes ---\n")
                    continue
                print(_format_sample(event))
                writer.write(event)
        except KeyboardInterrupt:
            print("\nInterrumpido por el usuario. Cerrando...")
        finally:
            link.close()
            print(f"Datos guardados en: {writer.path}")

    return 0


def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv)
    sys.exit(run(args))


if __name__ == "__main__":
    main()
