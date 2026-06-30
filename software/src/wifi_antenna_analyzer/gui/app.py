"""GUI Tkinter del Wi-Fi Antenna Analyzer — Fases 2 y 3 (Scanner + Benchmark).

Arquitectura: la lectura serie corre en un hilo aparte y publica
eventos en una cola; el hilo principal de Tkinter vacía la cola cada
100ms y actualiza la tabla. Así la UI nunca se congela esperando al
puerto serie. Cuando hay un benchmark activo, las mismas muestras se
reenvían también a la `BenchmarkSession` correspondiente. Las
pestañas de Comparador/Gráficas/Estadísticas (Fases 4-5) se añadirán
como módulos adicionales dentro de este paquete `gui/`, reutilizando
esta misma ventana principal.
"""

from __future__ import annotations

import logging
import queue
import threading
import time
import tkinter as tk
from tkinter import messagebox, ttk

from ..benchmark import BenchmarkSession
from ..models import NetworkSample, ScanEnd
from ..serial_link import SerialLink, SerialLinkError
from ..storage import BenchmarkCsvWriter, ScanCsvWriter
from .benchmark_tab import BenchmarkTab

logger = logging.getLogger(__name__)


def _list_serial_ports() -> list[str]:
    from serial.tools import list_ports

    return [info.device for info in list_ports.comports()]


class ScannerTab(ttk.Frame):
    """Tabla en vivo con las redes detectadas en el escaneo más reciente."""

    COLUMNS = ("ssid", "bssid", "rssi", "channel", "security")

    def __init__(self, parent: tk.Widget) -> None:
        super().__init__(parent)
        self._rows_by_bssid: dict[str, str] = {}  # bssid -> item id del Treeview

        self.tree = ttk.Treeview(self, columns=self.COLUMNS, show="headings")
        headings = {
            "ssid": "SSID",
            "bssid": "MAC",
            "rssi": "RSSI (dBm)",
            "channel": "Canal",
            "security": "Seguridad",
        }
        widths = {"ssid": 220, "bssid": 150, "rssi": 90, "channel": 60, "security": 130}
        for col in self.COLUMNS:
            self.tree.heading(col, text=headings[col], command=lambda c=col: self._sort_by(c))
            self.tree.column(col, width=widths[col], anchor="w")

        scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.grid(row=0, column=0, sticky="nsew")
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        self.summary_var = tk.StringVar(value="Sin datos todavía")
        ttk.Label(self, textvariable=self.summary_var).grid(
            row=1, column=0, columnspan=2, sticky="w", pady=(4, 0)
        )

    def upsert_sample(self, sample: NetworkSample) -> None:
        values = (sample.ssid, sample.bssid, sample.rssi, sample.channel, sample.security_name)
        if sample.bssid in self._rows_by_bssid:
            self.tree.item(self._rows_by_bssid[sample.bssid], values=values)
        else:
            item_id = self.tree.insert("", "end", values=values)
            self._rows_by_bssid[sample.bssid] = item_id

    def on_scan_end(self, event: ScanEnd) -> None:
        self.summary_var.set(
            f"Último escaneo #{event.scan_id}: {event.network_count} redes detectadas"
        )

    def _sort_by(self, column: str) -> None:
        items = [(self.tree.set(item, column), item) for item in self.tree.get_children("")]
        try:
            items.sort(key=lambda pair: float(pair[0]))
        except ValueError:
            items.sort(key=lambda pair: pair[0])
        for index, (_, item) in enumerate(items):
            self.tree.move(item, "", index)


class AnalyzerApp(ttk.Frame):
    """Ventana principal: barra de conexión + pestañas."""

    POLL_INTERVAL_MS = 100

    def __init__(self, master: tk.Tk) -> None:
        super().__init__(master)
        self.master = master
        self.master.title("ESP32 Wi-Fi Antenna Analyzer")
        self.master.geometry("780x520")

        self._event_queue: queue.Queue = queue.Queue()
        self._link: SerialLink | None = None
        self._csv_writer: ScanCsvWriter | None = None
        self._reader_thread: threading.Thread | None = None
        self._stop_flag = threading.Event()

        self._benchmark_session: BenchmarkSession | None = None
        self._benchmark_end_time: float | None = None

        self._build_connection_bar()
        self._build_tabs()

        self.pack(fill="both", expand=True)
        self.master.after(self.POLL_INTERVAL_MS, self._drain_queue)
        self.master.protocol("WM_DELETE_WINDOW", self._on_close)

    # --- construcción de la UI -------------------------------------------------

    def _build_connection_bar(self) -> None:
        bar = ttk.Frame(self)
        bar.pack(fill="x", padx=8, pady=8)

        ttk.Label(bar, text="Puerto:").pack(side="left")
        self.port_var = tk.StringVar()
        self.port_combo = ttk.Combobox(bar, textvariable=self.port_var, width=18, state="readonly")
        self.port_combo.pack(side="left", padx=(4, 4))
        self._refresh_ports()

        ttk.Button(bar, text="Refrescar", command=self._refresh_ports).pack(
            side="left", padx=(0, 12)
        )

        ttk.Label(bar, text="Antena:").pack(side="left")
        self.antenna_var = tk.StringVar(value="default")
        ttk.Entry(bar, textvariable=self.antenna_var, width=18).pack(side="left", padx=(4, 12))

        self.connect_button = ttk.Button(bar, text="Conectar", command=self._toggle_connection)
        self.connect_button.pack(side="left")

        self.status_var = tk.StringVar(value="Desconectado")
        ttk.Label(bar, textvariable=self.status_var).pack(side="right")

    def _build_tabs(self) -> None:
        notebook = ttk.Notebook(self)
        notebook.pack(fill="both", expand=True, padx=8, pady=(0, 8))

        self.scanner_tab = ScannerTab(notebook)
        notebook.add(self.scanner_tab, text="Scanner")

        self.benchmark_tab = BenchmarkTab(notebook, on_start=self._start_benchmark)
        notebook.add(self.benchmark_tab, text="Benchmark")

        # Próximas fases: Comparador, Gráficas, Estadísticas.
        placeholder = ttk.Frame(notebook)
        ttk.Label(
            placeholder,
            text="Próximamente: Comparador de antenas, Gráficas y Estadísticas (Fases 4-5)",
        ).pack(padx=20, pady=20)
        notebook.add(placeholder, text="Próximamente")

    def _refresh_ports(self) -> None:
        ports = _list_serial_ports()
        self.port_combo["values"] = ports
        if ports and not self.port_var.get():
            self.port_var.set(ports[0])

    # --- conexión / hilo de lectura ---------------------------------------------

    def _toggle_connection(self) -> None:
        if self._link is None:
            self._connect()
        else:
            self._disconnect()

    def _connect(self) -> None:
        port = self.port_var.get()
        if not port:
            messagebox.showwarning("Sin puerto", "Selecciona un puerto serie primero.")
            return

        antenna = self.antenna_var.get().strip() or "default"
        link = SerialLink(port=port, antenna=antenna)
        try:
            link.connect()
        except SerialLinkError as exc:
            messagebox.showerror("Error de conexión", str(exc))
            return

        self._link = link
        self._csv_writer = ScanCsvWriter(outdir="../data", antenna=antenna)
        self._stop_flag.clear()
        self._reader_thread = threading.Thread(target=self._read_loop, daemon=True)
        self._reader_thread.start()

        self.status_var.set(
            f"Conectado a {port} ({antenna}) — guardando en {self._csv_writer.path.name}"
        )
        self.connect_button.configure(text="Desconectar")

    def _disconnect(self) -> None:
        self._stop_flag.set()
        if self._link is not None:
            self._link.close()
            self._link = None
        if self._csv_writer is not None:
            self._csv_writer.close()
            self._csv_writer = None
        if self._benchmark_session is not None:
            self._cancel_benchmark("Desconectado: benchmark cancelado.")
        self.status_var.set("Desconectado")
        self.connect_button.configure(text="Conectar")

    def _read_loop(self) -> None:
        """Corre en un hilo aparte: lee del puerto y empuja eventos a la cola."""
        assert self._link is not None
        try:
            for event in self._link.read_events():
                if self._stop_flag.is_set():
                    break
                self._event_queue.put(event)
        except SerialLinkError as exc:
            logger.error("Error leyendo el puerto serie: %s", exc)
            self._event_queue.put(exc)

    def _drain_queue(self) -> None:
        """Corre en el hilo de Tkinter: aplica los eventos pendientes a la UI."""
        try:
            while True:
                item = self._event_queue.get_nowait()
                if isinstance(item, NetworkSample):
                    self.scanner_tab.upsert_sample(item)
                    if self._csv_writer is not None:
                        self._csv_writer.write(item)
                    if self._benchmark_session is not None:
                        self._benchmark_session.add_sample(item)
                elif isinstance(item, ScanEnd):
                    self.scanner_tab.on_scan_end(item)
                elif isinstance(item, Exception):
                    messagebox.showerror("Error de conexión", str(item))
                    self._disconnect()
        except queue.Empty:
            pass
        finally:
            self._tick_benchmark()
            self.master.after(self.POLL_INTERVAL_MS, self._drain_queue)

    # --- modo benchmark (Fase 3) ------------------------------------------------

    def _start_benchmark(self, duration_seconds: float) -> None:
        if self._link is None:
            messagebox.showwarning(
                "Sin conexión", "Conéctate a un ESP32 antes de iniciar un benchmark."
            )
            return

        antenna = self.antenna_var.get().strip() or "default"
        self._benchmark_session = BenchmarkSession(
            antenna=antenna, duration_seconds=duration_seconds
        )
        self._benchmark_end_time = time.monotonic() + duration_seconds

        self.benchmark_tab.clear_results()
        self.benchmark_tab.set_running(True)
        self.benchmark_tab.set_status(
            f"Benchmark en curso ({antenna})... {duration_seconds:.0f}s restantes"
        )

    def _tick_benchmark(self) -> None:
        if self._benchmark_session is None or self._benchmark_end_time is None:
            return

        remaining = self._benchmark_end_time - time.monotonic()
        if remaining <= 0:
            self._finish_benchmark()
            return

        self.benchmark_tab.set_status(
            f"Benchmark en curso... {remaining:.0f}s restantes "
            f"({self._benchmark_session.network_count} redes, "
            f"{self._benchmark_session.sample_count} muestras)"
        )

    def _finish_benchmark(self) -> None:
        assert self._benchmark_session is not None
        session = self._benchmark_session
        results = session.results()

        self.benchmark_tab.show_results(results)
        self.benchmark_tab.set_running(False)

        with BenchmarkCsvWriter(outdir="../data", antenna=session.antenna) as writer:
            writer.write_results(results)

        self.benchmark_tab.set_status(
            f"Benchmark completado: {len(results)} redes, {session.sample_count} muestras"
            f" — guardado en {writer.path.name}"
        )

        self._benchmark_session = None
        self._benchmark_end_time = None

    def _cancel_benchmark(self, reason: str) -> None:
        self.benchmark_tab.set_running(False)
        self.benchmark_tab.set_status(reason)
        self._benchmark_session = None
        self._benchmark_end_time = None

    def _on_close(self) -> None:
        self._disconnect()
        self.master.destroy()


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)-8s %(message)s")
    root = tk.Tk()
    AnalyzerApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
