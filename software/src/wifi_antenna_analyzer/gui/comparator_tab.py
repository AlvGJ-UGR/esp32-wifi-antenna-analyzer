"""Pestaña "Comparador" de la GUI (Fase 4).

Igual que BenchmarkTab, es un componente de UI puro: no sabe nada de
BenchmarkSession ni de comparator.py. Recibe la lista de antenas
disponibles (las que ya tienen al menos un benchmark completado) y,
al pulsar "Comparar", delega en el callback `on_compare(antenna_a,
antenna_b)`. AnalyzerApp es quien guarda el historial de resultados
y hace la comparación real con `comparator.compare_antennas`.
"""

from __future__ import annotations

import tkinter as tk
from collections.abc import Callable
from tkinter import messagebox, ttk

from ..models import AntennaComparisonRow


class ComparatorTab(ttk.Frame):
    """Selector de dos antenas + tabla con la diferencia de RSSI red a red."""

    COLUMNS = ("ssid", "bssid", "mean_a", "mean_b", "diff")

    def __init__(self, parent: tk.Widget, on_compare: Callable[[str, str], None]) -> None:
        super().__init__(parent)
        self._on_compare = on_compare
        self._label_a = "A"
        self._label_b = "B"

        self._build_controls()
        self._build_table()

    # --- construcción de la UI -------------------------------------------------

    def _build_controls(self) -> None:
        bar = ttk.Frame(self)
        bar.pack(fill="x", padx=8, pady=8)

        ttk.Label(bar, text="Antena A:").pack(side="left")
        self.antenna_a_var = tk.StringVar()
        self.antenna_a_combo = ttk.Combobox(
            bar, textvariable=self.antenna_a_var, width=16, state="readonly"
        )
        self.antenna_a_combo.pack(side="left", padx=(4, 12))

        ttk.Label(bar, text="Antena B:").pack(side="left")
        self.antenna_b_var = tk.StringVar()
        self.antenna_b_combo = ttk.Combobox(
            bar, textvariable=self.antenna_b_var, width=16, state="readonly"
        )
        self.antenna_b_combo.pack(side="left", padx=(4, 12))

        ttk.Button(bar, text="Comparar", command=self._handle_compare_click).pack(side="left")

        self.status_var = tk.StringVar(
            value="Completa al menos dos benchmarks (con distinto nombre de antena) para comparar."
        )
        ttk.Label(bar, textvariable=self.status_var).pack(side="left", padx=(12, 0))

    def _build_table(self) -> None:
        container = ttk.Frame(self)
        container.pack(fill="both", expand=True, padx=8, pady=(0, 8))

        self.tree = ttk.Treeview(container, columns=self.COLUMNS, show="headings")
        self._headings = {
            "ssid": "SSID",
            "bssid": "MAC",
            "mean_a": "RSSI A",
            "mean_b": "RSSI B",
            "diff": "Diferencia (B-A)",
        }
        widths = {"ssid": 200, "bssid": 150, "mean_a": 90, "mean_b": 90, "diff": 130}
        for col in self.COLUMNS:
            self.tree.heading(col, text=self._headings[col])
            self.tree.column(col, width=widths[col], anchor="w")

        scrollbar = ttk.Scrollbar(container, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.grid(row=0, column=0, sticky="nsew")
        scrollbar.grid(row=0, column=1, sticky="ns")
        container.columnconfigure(0, weight=1)
        container.rowconfigure(0, weight=1)

    # --- eventos -----------------------------------------------------------

    def _handle_compare_click(self) -> None:
        antenna_a = self.antenna_a_var.get()
        antenna_b = self.antenna_b_var.get()
        if not antenna_a or not antenna_b:
            messagebox.showwarning("Faltan antenas", "Selecciona una antena en A y otra en B.")
            return
        if antenna_a == antenna_b:
            messagebox.showwarning("Antenas iguales", "Elige dos antenas distintas para comparar.")
            return
        self._on_compare(antenna_a, antenna_b)

    # --- API usada por AnalyzerApp -------------------------------------------

    def set_available_antennas(self, antennas: list[str]) -> None:
        """Actualiza las opciones de los desplegables tras cada benchmark nuevo."""
        self.antenna_a_combo["values"] = antennas
        self.antenna_b_combo["values"] = antennas

    def set_status(self, text: str) -> None:
        self.status_var.set(text)

    def clear_results(self) -> None:
        for item in self.tree.get_children(""):
            self.tree.delete(item)

    def show_results(
        self, rows: list[AntennaComparisonRow], antenna_a: str, antenna_b: str
    ) -> None:
        self._label_a, self._label_b = antenna_a, antenna_b
        self.tree.heading("mean_a", text=f"RSSI {antenna_a}")
        self.tree.heading("mean_b", text=f"RSSI {antenna_b}")
        self.tree.heading("diff", text=f"Diferencia ({antenna_b} - {antenna_a})")

        self.clear_results()
        for row in rows:
            values = (
                row.ssid,
                row.bssid,
                f"{row.mean_a:.1f}" if row.mean_a is not None else "no detectada",
                f"{row.mean_b:.1f}" if row.mean_b is not None else "no detectada",
                f"{row.diff_db:+.1f}" if row.diff_db is not None else "-",
            )
            self.tree.insert("", "end", values=values)
