"""Export a PDF de un informe de benchmark (Fase 5).

Genera un PDF de una página con una tabla de resultados y un
gráfico de barras horizontal (RSSI medio ± desviación típica por
red), usando el backend PDF de matplotlib directamente — sin
dependencias adicionales de generación de PDF.

Deliberadamente NO usa `matplotlib.pyplot`: construye el `Figure`
directamente (API "sin pyplot" recomendada por matplotlib para uso
no interactivo) para no depender del backend interactivo activo en
ese momento ni interferir con él. Así este módulo se comporta igual
si se llama desde un test headless en CI, desde la GUI Tkinter (que
sí usa un backend interactivo, `TkAgg`, para la pestaña Gráficas), o
desde cualquier otro contexto — sin necesidad de tocar
`matplotlib.use()` en ningún sitio.
"""

from __future__ import annotations

from pathlib import Path

from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.figure import Figure

from .models import BenchmarkResult

MAX_NETWORKS_IN_CHART = 15


def export_benchmark_pdf(
    results: list[BenchmarkResult],
    antenna: str,
    path: Path | str,
) -> Path:
    """Escribe el informe en `path` y devuelve la ruta final (como Path)."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    fig = _build_report_figure(results, antenna)
    with PdfPages(path) as pdf:
        pdf.savefig(fig)

    return path


def _build_report_figure(results: list[BenchmarkResult], antenna: str) -> Figure:
    fig = Figure(figsize=(8.27, 11.69))  # A4 vertical
    fig.suptitle(f"Informe de Benchmark — antena: {antenna}", fontsize=14, fontweight="bold")

    if not results:
        ax = fig.add_axes((0.1, 0.1, 0.8, 0.7))
        ax.axis("off")
        ax.text(0.5, 0.5, "Sin redes detectadas en este benchmark.", ha="center", va="center")
        return fig

    _add_results_table(fig, results)
    _add_rssi_chart(fig, results)
    return fig


def _add_results_table(fig: Figure, results: list[BenchmarkResult]) -> None:
    ax = fig.add_axes((0.05, 0.55, 0.9, 0.35))
    ax.axis("off")

    columns = ["SSID", "MAC", "Muestras", "RSSI medio", "Desv.", "Mín", "Máx"]
    rows = [
        [
            result.ssid,
            result.bssid,
            str(result.count),
            f"{result.mean:.1f}" if result.mean is not None else "-",
            f"{result.stdev:.1f}" if result.stdev is not None else "-",
            str(result.minimum) if result.minimum is not None else "-",
            str(result.maximum) if result.maximum is not None else "-",
        ]
        for result in results
    ]

    table = ax.table(cellText=rows, colLabels=columns, loc="center", cellLoc="left")
    table.auto_set_font_size(False)
    table.set_fontsize(7)
    table.scale(1, 1.3)


def _add_rssi_chart(fig: Figure, results: list[BenchmarkResult]) -> None:
    ax = fig.add_axes((0.15, 0.08, 0.75, 0.4))

    # Mejor señal arriba; si hay muchas redes, mostrar solo las mejores
    # para que las etiquetas del eje Y sigan siendo legibles.
    chart_results = sorted(
        results, key=lambda r: r.mean if r.mean is not None else float("-inf"), reverse=True
    )[:MAX_NETWORKS_IN_CHART]
    chart_results.reverse()  # barh dibuja de abajo a arriba

    labels = [f"{result.ssid} ({result.bssid[-8:]})" for result in chart_results]
    means = [result.mean if result.mean is not None else 0 for result in chart_results]
    errors = [result.stdev if result.stdev is not None else 0 for result in chart_results]

    ax.barh(labels, means, xerr=errors, color="#4a90d9", ecolor="#333333", capsize=3)
    ax.set_xlabel("RSSI medio (dBm)")
    ax.set_title("RSSI medio ± desviación típica por red", fontsize=10)
    ax.tick_params(axis="y", labelsize=7)
