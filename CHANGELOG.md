# Changelog

Todos los cambios notables de este proyecto se documentan en este
fichero. El formato sigue [Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/)
y el proyecto usa [versionado semántico](https://semver.org/lang/es/)
en la medida en que tiene sentido para una herramienta de laboratorio
(no una librería con API pública estable).

## [Sin publicar]

### Añadido
- README rehecho como documento de producto: capturas reales de la
  GUI (generadas ejecutando `AnalyzerApp` de verdad sobre Xvfb con
  datos sintéticos, no mockups — ver
  `software/scripts/generate_screenshots.py`), diagrama de
  arquitectura en SVG, tabla de hardware necesario, índice navegable
  y badges. El propio README se ha verificado con la librería real de
  GitHub (`cmarkgfm`) y con `github-slugger` (el algoritmo exacto que
  usa GitHub para los anchors de los encabezados) para confirmar que
  todo el markdown anidado en HTML y todos los enlaces del índice
  funcionan, en vez de darlo por hecho.
- Modo standalone con pantalla e-paper (Fase 6, opcional): firmware
  independiente en `firmware/esp32_epaper_display/` para quien tenga
  una Waveshare 2.13" e-Paper HAT (V3, blanco y negro, SSD1680).
  Escanea Wi-Fi y muestra las redes con mejor señal directamente en
  pantalla, sin depender del portátil. No se ha podido compilar de
  extremo a extremo en el entorno donde se escribió (sin acceso al
  registro de PlatformIO); se ha verificado la API usada contra el
  código fuente real de GxEPD2 y compilado con un harness de stubs a
  nivel de sintaxis/tipos — pendiente de que el propio CI (con acceso
  completo a internet) lo confirme, o de que el usuario lo pruebe en
  hardware real. Ver `firmware/esp32_epaper_display/README.md` para
  el detalle de qué se ha podido verificar y qué no.
- CI: job `firmware-epaper-build` que compila ese firmware en cada
  push/PR (con `continue-on-error`, para no bloquear el resto de la
  CI por un componente de hardware opcional).
- Corrección de hardware: la nota sobre configuración de antena
  externa (README raíz y `firmware/esp32_wifi_scanner/README.md`) era
  genérica y no aplicaba tal cual al ESP32-WROOM-32UE — ese módulo no
  tiene antena PCB ni resistencia de selección que mover, toda la
  señal sale siempre por el conector U.FL/IPEX. Corregido con la
  información específica de ese módulo (y de en qué caso sí aplicaría
  la nota original, con otros módulos WROOM-32D/E/WROVER).

### Aplazado
- Historial persistente entre sesiones de `waa-gui` (migración de CSV
  a SQLite). Ver la justificación en `docs/PLAN.md`, sección "Fase 5.1".

## [0.5.0] — 2026-07-01

### Añadido
- Pestaña **Gráficas**: RSSI vs tiempo por red, matplotlib embebido en
  Tkinter, selección de redes visibles mediante checkboxes.
- Pestaña **Estadísticas**: nº de redes, RSSI medio/mín/máx, canal más
  ocupado, desglose por canal y por tipo de seguridad — refrescada en
  vivo cada segundo mientras hay conexión activa.
- Botón **Exportar PDF** en la pestaña Benchmark: informe de una
  página (tabla de resultados + gráfico de barras con desviación
  típica) usando el backend PDF de matplotlib.
- Módulos nuevos: `network_stats.py` (estadísticas y series
  temporales) y `report.py` (export a PDF), ambos con tests.

### Corregido
- Placeholder `"Tu nombre aquí"` sin rellenar en `pyproject.toml` y en
  el copyright de `LICENSE`.

## [0.4.0] — 2026-07-01

### Añadido
- Pestaña **Comparador**: empareja dos benchmarks por BSSID (no por
  SSID), muestra la diferencia de RSSI en dB por red y distingue
  "peor señal" de "red no detectada" por una de las dos antenas.
- `comparator.py` (lógica pura) y `ComparisonCsvWriter` (export a
  `data/comparison_<A>_vs_<B>_<timestamp>.csv`).

## [0.3.0] — 2026-06-30

### Añadido
- Pestaña **Benchmark**: duración configurable, acumula RSSI por
  BSSID durante la ventana y muestra media/desviación típica/mín/máx
  por red al terminar. Export automático a
  `data/benchmark_<antena>_<timestamp>.csv`.
- `benchmark.py` (`BenchmarkSession`, lógica pura) y
  `BenchmarkCsvWriter`.

### Corregido
- Eliminados `software/serial_reader.py`, `firmware/esp32_wifi_scanner.ino`
  y el `requirements.txt` de la raíz: duplicaban `cli.py`, `main.cpp`
  y `pyproject.toml` respectivamente. El primero además rompía
  `ruff check .`, dejando la CI en rojo en `main` sin que constara en
  ningún sitio.

## [0.2.0] y anteriores — 2026-06-30

Estructura inicial del proyecto: firmware ESP32 (escaneo Wi-Fi +
envío por Serial en JSON), paquete Python instalable con capa de
lectura serie y almacenamiento en CSV testeada (`waa-scan`), y GUI
Tkinter con la pestaña **Scanner** en tiempo real (`waa-gui`). CI en
GitHub Actions (tests + lint Python, build del firmware con
PlatformIO).
