"""
ESP32 Wi-Fi Antenna Analyzer — software/serial_reader.py
----------------------------------------------------------
Fase 1-2: lee las líneas JSON que manda el ESP32 por USB,
las muestra por consola y las va guardando en un CSV.

Esto es deliberadamente sencillo (sin GUI todavía). Es la base
sobre la que en próximas sesiones construiremos:
  - la interfaz gráfica (pestañas: Scanner / Comparador / Gráficas / Estadísticas)
  - el modo benchmark
  - el comparador de antenas por MAC
  - exportación a PDF / SQLite

Uso:
    python serial_reader.py --port COM5
    python serial_reader.py --port /dev/ttyUSB0 --baud 115200
"""

import argparse
import csv
import json
import sys
import time
from datetime import datetime
from pathlib import Path

import serial

# Traducción del código numérico de seguridad que manda el ESP32
# (valores de wifi_auth_mode_t en Arduino-ESP32)
SECURITY_NAMES = {
    0: "OPEN",
    1: "WEP",
    2: "WPA_PSK",
    3: "WPA2_PSK",
    4: "WPA_WPA2_PSK",
    5: "WPA2_ENTERPRISE",
    6: "WPA3_PSK",
    7: "WPA2_WPA3_PSK",
    8: "WAPI_PSK",
}


def parse_args():
    p = argparse.ArgumentParser(description="Lector serial del ESP32 Wi-Fi Antenna Analyzer")
    p.add_argument("--port", required=True, help="Puerto serie, ej: COM5 o /dev/ttyUSB0")
    p.add_argument("--baud", type=int, default=115200, help="Velocidad serie (default 115200)")
    p.add_argument(
        "--antenna",
        default="default",
        help="Nombre de la antena que estás probando ahora mismo (para el CSV)",
    )
    p.add_argument(
        "--outdir",
        default="../data",
        help="Carpeta donde guardar el CSV (default: ../data)",
    )
    return p.parse_args()


def open_csv(outdir: str, antenna: str):
    Path(outdir).mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = Path(outdir) / f"scan_{antenna}_{timestamp}.csv"
    f = open(filename, "w", newline="", encoding="utf-8")
    writer = csv.writer(f)
    writer.writerow(["fecha", "hora", "antena", "scan", "ssid", "mac", "rssi", "channel", "security"])
    return f, writer, filename


def main():
    args = parse_args()

    try:
        ser = serial.Serial(args.port, args.baud, timeout=1)
    except serial.SerialException as e:
        print(f"No se pudo abrir el puerto {args.port}: {e}", file=sys.stderr)
        sys.exit(1)

    print(f"Conectado a {args.port} @ {args.baud} baudios. Antena: {args.antenna}")
    print("Esperando datos del ESP32... (Ctrl+C para salir)\n")

    csv_file, csv_writer, csv_path = open_csv(args.outdir, args.antenna)
    print(f"Guardando datos en: {csv_path}\n")

    networks_in_scan = 0

    try:
        while True:
            raw_line = ser.readline()
            if not raw_line:
                continue

            line = raw_line.decode("utf-8", errors="ignore").strip()
            if not line or line.startswith("#"):
                # líneas de log del firmware, no son JSON
                if line:
                    print(line)
                continue

            try:
                data = json.loads(line)
            except json.JSONDecodeError:
                # ruido / línea cortada, la ignoramos
                continue

            if data.get("event") == "scan_end":
                print(f"--- Fin escaneo #{data.get('scan')}: {data.get('count')} redes detectadas ---\n")
                networks_in_scan = 0
                continue

            # Es una red detectada
            networks_in_scan += 1
            sec_name = SECURITY_NAMES.get(data.get("security"), "?")
            now = datetime.now()

            print(
                f"[scan {data.get('scan')}] {data.get('ssid') or '(oculta)':25s} "
                f"RSSI={data.get('rssi'):4d} dBm  ch={data.get('channel'):2d}  "
                f"{sec_name:12s}  {data.get('mac')}"
            )

            csv_writer.writerow(
                [
                    now.strftime("%Y-%m-%d"),
                    now.strftime("%H:%M:%S"),
                    args.antenna,
                    data.get("scan"),
                    data.get("ssid"),
                    data.get("mac"),
                    data.get("rssi"),
                    data.get("channel"),
                    sec_name,
                ]
            )
            csv_file.flush()

    except KeyboardInterrupt:
        print("\nInterrumpido por el usuario. Cerrando...")
    finally:
        csv_file.close()
        ser.close()
        print(f"Datos guardados en: {csv_path}")


if __name__ == "__main__":
    main()
