"""Pestaña "Benchmark" de la GUI (Fase 3).

Componente de UI puro: no sabe nada de puertos serie ni de
BenchmarkSession. Expone un callback `on_start(duration_seconds)` que
la ventana principal (AnalyzerApp) usa para arrancar la sesión real,
y métodos `set_running` / `set_status` / `show_results` para que
AnalyzerApp la mantenga actualizada. Misma separación de
responsabilidades que ScannerTab en `app.py`.
"""

from __future__ import annotations

import tkinter as tk
from collections.abc import Callable
from tkinter import messagebox, ttk

from ..models import BenchmarkResult

DEFAULT_DURATION_SECONDS = 30


class BenchmarkTab(ttk.Frame):
    """Controles para lanzar un benchmark y tabla con el resumen por red."""

    COLUMNS = ("ssid", "bssid", "count", "mean", "stdev", "minimum", "maximum")

    def __init__(self, parent: tk.Widget, on_start: Callable[[float], None]) -> None:
        super().__init__(parent)
        self._on_start = on_start

        self._build_controls()
        self._build_table()

    # --- construcción de la UI -------------------------------------------------

    def _build_controls(self) -> None:
        bar = ttk.Frame(self)
        bar.pack(fill="x", padx=8, pady=8)

        ttk.Label(bar, text="Duración (s):").pack(side="left")
        self.duration_var = tk.StringVar(value=str(DEFAULT_DURATION_SECONDS))
        ttk.Entry(bar, textvariable=self.duration_var, width=6).pack(side="left", padx=(4, 12))

        self.start_button = ttk.Button(
            bar, text="Iniciar Benchmark", command=self._handle_start_click
        )
        self.start_button.pack(side="left")

        self.status_var = tk.StringVar(value="Conéctate a un ESP32 para empezar.")
        ttk.Label(bar, textvariable=self.status_var).pack(side="left", padx=(12, 0))

    def _build_table(self) -> None:
        container = ttk.Frame(self)
        container.pack(fill="both", expand=True, padx=8, pady=(0, 8))

        self.tree = ttk.Treeview(container, columns=self.COLUMNS, show="headings")
        headings = {
            "ssid": "SSID",
            "bssid": "MAC",
            "count": "Muestras",
            "mean": "RSSI medio",
            "stdev": "Desv. típica",
            "minimum": "Mín",
            "maximum": "Máx",
        }
        widths = {
            "ssid": 200,
            "bssid": 150,
            "count": 80,
            "mean": 90,
            "stdev": 90,
            "minimum": 60,
            "maximum": 60,
        }
        for col in self.COLUMNS:
            self.tree.heading(col, text=headings[col])
            self.tree.column(col, width=widths[col], anchor="w")

        scrollbar = ttk.Scrollbar(container, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.grid(row=0, column=0, sticky="nsew")
        scrollbar.grid(row=0, column=1, sticky="ns")
        container.columnconfigure(0, weight=1)
        container.rowconfigure(0, weight=1)

    # --- eventos -----------------------------------------------------------

    def _handle_start_click(self) -> None:
        try:
            duration = float(self.duration_var.get())
        except ValueError:
            messagebox.showwarning("Duración inválida", "Introduce un número de segundos.")
            return
        if duration <= 0:
            messagebox.showwarning("Duración inválida", "La duración debe ser mayor que 0.")
            return
        self._on_start(duration)

    # --- API usada por AnalyzerApp -------------------------------------------

    def set_running(self, running: bool) -> None:
        self.start_button.configure(state="disabled" if running else "normal")

    def set_status(self, text: str) -> None:
        self.status_var.set(text)

    def clear_results(self) -> None:
        for item in self.tree.get_children(""):
            self.tree.delete(item)

    def show_results(self, results: list[BenchmarkResult]) -> None:
        self.clear_results()
        for result in results:
            values = (
                result.ssid,
                result.bssid,
                result.count,
                f"{result.mean:.1f}" if result.mean is not None else "-",
                f"{result.stdev:.1f}" if result.stdev is not None else "-",
                result.minimum if result.minimum is not None else "-",
                result.maximum if result.maximum is not None else "-",
            )
            self.tree.insert("", "end", values=values)
