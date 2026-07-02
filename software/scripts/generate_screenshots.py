"""Genera capturas reales de la GUI para el README, con datos sintéticos.

No es un mockup: construye la ventana AnalyzerApp de verdad, la
rellena con NetworkSample/BenchmarkResult sintéticos pero realistas,
y usa ImageMagick (`import`) para capturar el framebuffer X11 real
(Xvfb) en el que Tkinter está dibujando.

Uso (Linux, requiere Xvfb + ImageMagick instalados):

    Xvfb :99 -screen 0 1180x820x24 &
    DISPLAY=:99 python scripts/generate_screenshots.py

Escribe los PNG en /home/claude/screenshots — cópialos a mano a
docs/screenshots/ tras revisarlos (no se sobrescriben solos, para
evitar que un cambio de la GUI actualice las capturas del README sin
que alguien las revise antes).

Vuelve a ejecutar esto cada vez que cambie el layout de alguna
pestaña de `waa-gui`, para que las capturas de docs/screenshots/ no
queden desactualizadas respecto al código real.
"""

from __future__ import annotations

import subprocess
import time
import tkinter as tk
from datetime import datetime, timedelta

from wifi_antenna_analyzer.benchmark import BenchmarkSession
from wifi_antenna_analyzer.comparator import compare_antennas
from wifi_antenna_analyzer.gui.app import AnalyzerApp
from wifi_antenna_analyzer.models import NetworkSample, SecurityType

OUT_DIR = "/home/claude/screenshots"
subprocess.run(["mkdir", "-p", OUT_DIR], check=True)

# --- Redes sintéticas, con nombres y RSSI realistas de un entorno doméstico ---
NETWORKS = [
    ("MOVISTAR_A1B2", "AA:11:22:33:44:01", 6, SecurityType.WPA2_PSK, -42),
    ("MiFibra-5G", "AA:11:22:33:44:02", 44, SecurityType.WPA2_WPA3_PSK, -48),
    ("VodafoneWiFi_C3D4", "AA:11:22:33:44:03", 11, SecurityType.WPA2_PSK, -61),
    ("(oculta)", "AA:11:22:33:44:04", 6, SecurityType.WPA2_PSK, -67),
    ("Livebox-9F2A", "AA:11:22:33:44:05", 1, SecurityType.WPA2_PSK, -71),
    ("eduroam", "AA:11:22:33:44:06", 11, SecurityType.WPA2_PSK, -75),
    ("IoT-Cam-Garage", "AA:11:22:33:44:07", 6, SecurityType.OPEN, -80),
]


def make_sample(ssid, bssid, channel, security, rssi, t, antenna):
    return NetworkSample(
        scan_id=1,
        ssid=ssid,
        bssid=bssid,
        rssi=rssi,
        channel=channel,
        security=security,
        timestamp=t,
        antenna=antenna,
    )


def screenshot(name: str) -> None:
    time.sleep(0.3)  # dar tiempo a Tk a terminar de pintar
    subprocess.run(
        ["import", "-display", ":99", "-window", "root", f"{OUT_DIR}/{name}.png"],
        check=True,
    )
    print(f"capturado {name}.png")


def select_tab(app: AnalyzerApp, widget) -> None:
    notebook = app.scanner_tab.master
    notebook.select(widget)


def main() -> None:
    root = tk.Tk()
    root.geometry("1180x820+0+0")
    app = AnalyzerApp(root)
    root.update_idletasks()
    root.update()

    now = datetime.now()

    # --- Poblar Scanner (tabla en vivo) ---
    app.status_var.set("Conectado a COM5 (dipolo_5dbi)")
    app.connect_button.configure(text="Desconectar")
    for ssid, bssid, ch, sec, rssi in NETWORKS:
        s = make_sample(ssid, bssid, ch, sec, rssi, now, "dipolo_5dbi")
        app.scanner_tab.upsert_sample(s)
        app._latest_samples[bssid] = s
        app._scan_history.add_sample(s)
    select_tab(app, app.scanner_tab)
    root.update()
    screenshot("01_scanner")

    # --- Poblar Benchmark (resultados de una sesión de 30s) ---
    session = BenchmarkSession(antenna="dipolo_5dbi", duration_seconds=30)
    for ssid, bssid, ch, sec, base_rssi in NETWORKS:
        for i in range(12):
            jitter = (i % 5) - 2
            t = now + timedelta(seconds=i * 2.5)
            session.add_sample(
                make_sample(ssid, bssid, ch, sec, base_rssi + jitter, t, "dipolo_5dbi")
            )
    results_dipolo = session.results()
    app.benchmark_tab.show_results(results_dipolo)
    app.benchmark_tab.set_status(
        f"Benchmark completado: {len(results_dipolo)} redes, {session.sample_count} muestras"
        " — guardado en benchmark_dipolo_5dbi_20260701_120000.csv"
    )
    app._benchmark_history["dipolo_5dbi"] = results_dipolo
    select_tab(app, app.benchmark_tab)
    root.update()
    screenshot("02_benchmark")

    # --- Segundo benchmark (antena yagi) para el Comparador ---
    session_yagi = BenchmarkSession(antenna="yagi_12dbi", duration_seconds=30)
    yagi_boost = {  # la yagi direccional mejora unas redes y no ve otras tan lejanas
        "MOVISTAR_A1B2": +2,
        "MiFibra-5G": +9,
        "VodafoneWiFi_C3D4": +14,
        "(oculta)": +11,
        "Livebox-9F2A": +6,
        "eduroam": -3,
    }
    for ssid, bssid, ch, sec, base_rssi in NETWORKS:
        if ssid == "IoT-Cam-Garage":
            continue  # la yagi, muy direccional, no llega a ver esta red
        boost = yagi_boost.get(ssid, 0)
        for i in range(12):
            jitter = (i % 5) - 2
            t = now + timedelta(seconds=i * 2.5)
            session_yagi.add_sample(
                make_sample(ssid, bssid, ch, sec, base_rssi + boost + jitter, t, "yagi_12dbi")
            )
    results_yagi = session_yagi.results()
    app._benchmark_history["yagi_12dbi"] = results_yagi
    app.comparator_tab.set_available_antennas(sorted(app._benchmark_history))

    comparison = compare_antennas(results_dipolo, results_yagi)
    app.comparator_tab.show_results(comparison, "dipolo_5dbi", "yagi_12dbi")
    common = sum(1 for row in comparison if row.diff_db is not None)
    app.comparator_tab.set_status(
        f"{len(comparison)} redes comparadas ({common} detectadas por ambas antenas)"
        " — guardado en comparison_dipolo_5dbi_vs_yagi_12dbi_20260701_120500.csv"
    )
    select_tab(app, app.comparator_tab)
    root.update()
    screenshot("03_comparador")

    # --- Estadísticas + Gráficas ---
    app._refresh_live_views()
    select_tab(app, app.statistics_tab)
    root.update()
    screenshot("04_estadisticas")

    select_tab(app, app.charts_tab)
    root.update()
    screenshot("05_graficas")

    root.destroy()


if __name__ == "__main__":
    main()
