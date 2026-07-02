"""Pestaña "Gráficas" de la GUI (Fase 5): RSSI vs tiempo por red.

Componente de UI: recibe `NetworkHistory` ya calculado por
`network_stats.ScanHistory` y lo dibuja con matplotlib embebido en
Tkinter (`FigureCanvasTkAgg`). El usuario elige qué redes mostrar
desde una lista con checkboxes; por defecto se muestran las mejores
(más redes a la vez satura el gráfico y lo hace ilegible).
"""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk

import matplotlib

matplotlib.use("TkAgg")
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

from ..network_stats import NetworkHistory

DEFAULT_VISIBLE_NETWORKS = 5


class ChartsTab(ttk.Frame):
    """Selector de redes + gráfico de líneas de RSSI vs tiempo."""

    def __init__(self, parent: tk.Widget) -> None:
        super().__init__(parent)
        self._histories: list[NetworkHistory] = []
        self._visible_bssids: set[str] = set()

        self._build_selector()
        self._build_chart()

    # --- construcción de la UI -------------------------------------------------

    def _build_selector(self) -> None:
        frame = ttk.LabelFrame(self, text="Redes a mostrar")
        frame.pack(side="left", fill="y", padx=8, pady=8)

        canvas = tk.Canvas(frame, width=220, highlightthickness=0)
        scrollbar = ttk.Scrollbar(frame, orient="vertical", command=canvas.yview)
        self._checklist_frame = ttk.Frame(canvas)
        self._checklist_frame.bind(
            "<Configure>", lambda _e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        canvas.create_window((0, 0), window=self._checklist_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        self._check_vars: dict[str, tk.BooleanVar] = {}

    def _build_chart(self) -> None:
        chart_frame = ttk.Frame(self)
        chart_frame.pack(side="left", fill="both", expand=True, padx=(0, 8), pady=8)

        self.figure = Figure(figsize=(6, 4), dpi=100)
        self.axes = self.figure.add_subplot(111)
        self.axes.set_xlabel("Hora")
        self.axes.set_ylabel("RSSI (dBm)")
        self.axes.set_title("RSSI vs tiempo")

        self.canvas = FigureCanvasTkAgg(self.figure, master=chart_frame)
        self.canvas.get_tk_widget().pack(fill="both", expand=True)

    # --- API usada por AnalyzerApp -------------------------------------------

    def update_data(self, histories: list[NetworkHistory]) -> None:
        """Refresca la lista de checkboxes (si hay redes nuevas) y redibuja."""
        self._histories = histories
        self._sync_checklist()
        self._redraw()

    def clear(self) -> None:
        self._histories = []
        self._visible_bssids = set()
        for widget in self._checklist_frame.winfo_children():
            widget.destroy()
        self._check_vars = {}
        self._redraw()

    # --- internos ------------------------------------------------------------

    def _sync_checklist(self) -> None:
        known_bssids = set(self._check_vars)
        current_bssids = {h.bssid for h in self._histories}
        new_bssids = current_bssids - known_bssids
        if not new_bssids:
            return

        # Las primeras DEFAULT_VISIBLE_NETWORKS redes nuevas (por orden de
        # llegada, que ya viene ordenado por mejor RSSI) arrancan marcadas;
        # el resto se puede activar a mano para no saturar el gráfico.
        for history in self._histories:
            if history.bssid not in new_bssids:
                continue
            default_on = len(self._visible_bssids) < DEFAULT_VISIBLE_NETWORKS
            var = tk.BooleanVar(value=default_on)
            if default_on:
                self._visible_bssids.add(history.bssid)
            self._check_vars[history.bssid] = var

            label = f"{history.ssid} ({history.bssid[-8:]})"
            ttk.Checkbutton(
                self._checklist_frame,
                text=label,
                variable=var,
                command=lambda bssid=history.bssid: self._toggle(bssid),
            ).pack(anchor="w", padx=4, pady=1)

    def _toggle(self, bssid: str) -> None:
        if self._check_vars[bssid].get():
            self._visible_bssids.add(bssid)
        else:
            self._visible_bssids.discard(bssid)
        self._redraw()

    def _redraw(self) -> None:
        self.axes.clear()
        self.axes.set_xlabel("Hora")
        self.axes.set_ylabel("RSSI (dBm)")
        self.axes.set_title("RSSI vs tiempo")

        any_plotted = False
        for history in self._histories:
            if history.bssid not in self._visible_bssids or not history.points:
                continue
            timestamps = [point[0] for point in history.points]
            rssi_values = [point[1] for point in history.points]
            self.axes.plot(timestamps, rssi_values, marker="o", markersize=3, label=history.ssid)
            any_plotted = True

        if any_plotted:
            self.axes.legend(loc="upper right", fontsize=8)
            self.figure.autofmt_xdate()
        self.canvas.draw_idle()
