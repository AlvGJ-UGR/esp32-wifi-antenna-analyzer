# Plan de desarrollo

Basado en la idea original. Cada fase debe quedar usable por sí sola
antes de pasar a la siguiente.

## Fase 1 — Firmware ESP32 ✅
- [x] Escanear redes Wi-Fi visibles (incluyendo ocultas)
- [x] Extraer SSID, BSSID/MAC, RSSI, canal, tipo de seguridad
- [x] Enviar cada red como JSON por Serial a 115200 baudios
- [x] Marcador de fin de escaneo (`event: scan_end`) con el conteo total
- [x] Reestructurado como proyecto PlatformIO (`platformio.ini`, `src/`, `include/`)
- [x] Manejo de error de escaneo (código negativo de `WiFi.scanNetworks`)
- [ ] (opcional) Configurable: intervalo de escaneo por comando serial

## Fase 1.5 — Paquete Python base ✅
- [x] `wifi_antenna_analyzer` como paquete instalable (`pyproject.toml`, `src/` layout)
- [x] `models.py`: `NetworkSample`, `ScanEnd`, `BenchmarkResult`, `SecurityType`
- [x] `serial_link.py`: conexión serie + parseo del protocolo, testeable sin hardware
      (`SerialLink.parse_line` es un método estático puro)
- [x] `storage.py`: `ScanCsvWriter`
- [x] `cli.py` → comando `waa-scan`
- [x] Tests con pytest (modelos, parseo, CSV) — `pytest` en verde
- [x] Lint (`ruff`) y formato (`black`) configurados y en verde
- [x] CI en GitHub Actions: tests Python + build del firmware con PlatformIO

## Fase 2 — GUI en tiempo real ✅ (versión inicial)
- [x] Framework elegido: Tkinter (sin dependencias extra, viene con Python)
- [x] `gui/app.py` → comando `waa-gui`
- [x] Pestaña "Scanner": tabla en vivo (SSID / MAC / RSSI / Canal / Seguridad),
      actualizada por BSSID (no se duplican filas)
- [x] Selector de puerto serie (con botón refrescar) y de antena actual
- [x] Botón conectar/desconectar; lectura en hilo aparte para no congelar la UI
- [x] Guardado automático a CSV mientras está conectado
- [ ] Pulir estilo visual / iconos (cosmético, baja prioridad)

## Fase 3 — Modo Benchmark (siguiente)
- [ ] Botón "Iniciar Benchmark" con duración configurable (default 30s) en la GUI
- [ ] Acumular muestras por red (por MAC) durante la ventana usando `BenchmarkResult`
      (ya definido en `models.py`, falta la lógica de orquestación)
- [ ] Mostrar resumen al terminar: media, desviación estándar, máximo, mínimo, nº muestras
- [ ] Tests del cálculo de estadísticas con datos sintéticos

## Fase 4 — Comparador de antenas (pendiente)
- [ ] Guardar resultados de benchmark etiquetados por nombre de antena
- [ ] Emparejar redes entre dos benchmarks por MAC (no por SSID)
- [ ] Calcular diferencia de RSSI (ganancia/pérdida en dB) y diferencia en nº de redes
- [ ] Pestaña "Comparador": vista "Antena A vs Antena B"

## Fase 5 — Gráficas, export e historial (pendiente)
- [ ] Pestaña "Gráficas": RSSI vs tiempo, una línea por red (matplotlib embebido en Tkinter)
- [ ] Pestaña "Estadísticas": redes detectadas, RSSI medio/máx/mín, canal más ocupado
- [ ] Exportar a PDF (resumen del benchmark)
- [ ] Historial persistente — valorar migrar de CSV a SQLite en este punto

## Fase 6 — Avanzado (opcional)
- [ ] Modo promiscuo en el ESP32 (captura pasiva de tramas, más muestras/s)
- [ ] Vista agrupada por canal (tabla + gráfico de barras)
- [ ] Modo Radar: RSSI vs ángulo, para antenas direccionales
- [ ] Heatmap con GPS (si se añade módulo GPS)

## Decisiones ya tomadas
- Framework de GUI: **Tkinter** (cero dependencias adicionales)
- Empaquetado Python: **src layout + pyproject.toml**, instalable con `pip install -e .`
- Firmware: **PlatformIO** como forma principal de compilar/subir (Arduino IDE sigue siendo compatible)
- Almacenamiento: **CSV** por ahora, con la interfaz pensada para migrar a SQLite en Fase 5
- Licencia: **MIT**

## Decisiones pendientes
- ¿Nombre definitivo del repo / del proyecto?
- ¿Publicar el paquete en PyPI en algún momento, o quedarse solo en GitHub?
