"""Pestaña "Estadísticas" de la GUI (Fase 5).

Componente de UI puro: recibe un `ScanStatistics` ya calculado
(por `network_stats.compute_scan_statistics`) y lo pinta. No sabe
nada del puerto serie ni de cómo se agregaron los datos.
"""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from ..network_stats import ScanStatistics


class StatisticsTab(ttk.Frame):
    """Resumen en vivo: nº de redes, RSSI medio/min/max, canal más ocupado, seguridad."""

    def __init__(self, parent: tk.Widget) -> None:
        super().__init__(parent)
        self._build_summary()
        self._build_breakdown_tables()
        self.show_statistics(
            ScanStatistics(
                network_count=0,
                rssi_mean=None,
                rssi_min=None,
                rssi_max=None,
                channel_counts={},
                security_counts={},
            )
        )

    # --- construcción de la UI -------------------------------------------------

    def _build_summary(self) -> None:
        frame = ttk.LabelFrame(self, text="Resumen")
        frame.pack(fill="x", padx=8, pady=8)

        self._summary_vars = {
            "network_count": tk.StringVar(),
            "rssi_mean": tk.StringVar(),
            "rssi_range": tk.StringVar(),
            "busiest_channel": tk.StringVar(),
        }
        labels = {
            "network_count": "Redes detectadas:",
            "rssi_mean": "RSSI medio:",
            "rssi_range": "Rango RSSI:",
            "busiest_channel": "Canal más ocupado:",
        }
        for row, key in enumerate(labels):
            ttk.Label(frame, text=labels[key]).grid(row=row, column=0, sticky="w", padx=8, pady=2)
            ttk.Label(frame, textvariable=self._summary_vars[key]).grid(
                row=row, column=1, sticky="w", padx=8, pady=2
            )

    def _build_breakdown_tables(self) -> None:
        container = ttk.Frame(self)
        container.pack(fill="both", expand=True, padx=8, pady=(0, 8))

        channel_frame = ttk.LabelFrame(container, text="Redes por canal")
        channel_frame.pack(side="left", fill="both", expand=True, padx=(0, 4))
        self.channel_tree = ttk.Treeview(
            channel_frame, columns=("channel", "count"), show="headings", height=8
        )
        self.channel_tree.heading("channel", text="Canal")
        self.channel_tree.heading("count", text="Redes")
        self.channel_tree.column("channel", width=80, anchor="w")
        self.channel_tree.column("count", width=80, anchor="w")
        self.channel_tree.pack(fill="both", expand=True, padx=4, pady=4)

        security_frame = ttk.LabelFrame(container, text="Redes por seguridad")
        security_frame.pack(side="left", fill="both", expand=True, padx=(4, 0))
        self.security_tree = ttk.Treeview(
            security_frame, columns=("security", "count"), show="headings", height=8
        )
        self.security_tree.heading("security", text="Seguridad")
        self.security_tree.heading("count", text="Redes")
        self.security_tree.column("security", width=140, anchor="w")
        self.security_tree.column("count", width=80, anchor="w")
        self.security_tree.pack(fill="both", expand=True, padx=4, pady=4)

    # --- API usada por AnalyzerApp -------------------------------------------

    def show_statistics(self, stats: ScanStatistics) -> None:
        self._summary_vars["network_count"].set(str(stats.network_count))

        if stats.rssi_mean is not None:
            self._summary_vars["rssi_mean"].set(f"{stats.rssi_mean:.1f} dBm")
            self._summary_vars["rssi_range"].set(f"{stats.rssi_min} a {stats.rssi_max} dBm")
        else:
            self._summary_vars["rssi_mean"].set("-")
            self._summary_vars["rssi_range"].set("-")

        if stats.busiest_channel is not None:
            self._summary_vars["busiest_channel"].set(
                f"Canal {stats.busiest_channel} ({stats.busiest_channel_count} redes)"
            )
        else:
            self._summary_vars["busiest_channel"].set("-")

        self._fill_tree(self.channel_tree, sorted(stats.channel_counts.items()))
        self._fill_tree(
            self.security_tree,
            sorted(stats.security_counts.items(), key=lambda item: item[1], reverse=True),
        )

    @staticmethod
    def _fill_tree(tree: ttk.Treeview, rows: list[tuple[object, int]]) -> None:
        for item in tree.get_children(""):
            tree.delete(item)
        for label, count in rows:
            tree.insert("", "end", values=(label, count))
