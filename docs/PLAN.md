# Plan de desarrollo

Basado en la idea original. Cada fase debe quedar usable por sí sola
antes de pasar a la siguiente.

## Fase 1 — Firmware ESP32 ✅
- [x] Escanear redes Wi-Fi visibles (incluyendo ocultas)
- [x] Extraer SSID, BSSID/MAC, RSSI, canal, tipo de seguridad
- [x] Enviar cada red como JSON por Serial a 115200 baudios
- [x] Marcador de fin de escaneo (`event: scan_end`) con el conteo total
- [ ] (opcional) Configurable: intervalo de escaneo por comando serial

## Fase 1.5 — Lector de PC mínimo ✅
- [x] Leer JSON línea a línea desde el puerto serie
- [x] Mostrar redes detectadas en consola
- [x] Guardar todo en CSV con timestamp y nombre de antena

## Fase 2 — GUI en tiempo real (pendiente)
- [ ] Elegir framework: Tkinter (más simple, sin dependencias extra) vs
      algo más moderno (PySide6/CustomTkinter)
- [ ] Pestaña "Scanner": tabla en vivo con SSID / RSSI / Canal / Seguridad / MAC
- [ ] Selector de puerto serie y botón conectar/desconectar
- [ ] Selector de "antena actual" (texto libre o lista guardada)

## Fase 3 — Modo Benchmark (pendiente)
- [ ] Botón "Iniciar Benchmark" con duración configurable (default 30s)
- [ ] Acumular todas las muestras de cada red (por MAC) durante la ventana
- [ ] Calcular por red: media, desviación estándar, máximo, mínimo, nº de muestras
- [ ] Mostrar resumen al terminar

## Fase 4 — Comparador de antenas (pendiente)
- [ ] Guardar resultados de benchmark etiquetados por nombre de antena
- [ ] Emparejar redes entre dos benchmarks por MAC (no por SSID)
- [ ] Calcular diferencia de RSSI (ganancia/pérdida en dB) por red
- [ ] Calcular diferencia en nº de redes detectadas
- [ ] Vista tipo "Antena A vs Antena B" con la ganancia destacada

## Fase 5 — Gráficas, export e historial (pendiente)
- [ ] Pestaña "Gráficas": RSSI vs tiempo, una línea por red (matplotlib)
- [ ] Pestaña "Estadísticas": redes detectadas, RSSI medio/máx/mín,
      canal más ocupado, mejor/peor canal
- [ ] Exportar a CSV (ya tenemos la base) y a PDF (resumen del benchmark)
- [ ] Historial persistente (no borrar pruebas anteriores) — valorar
      pasar de CSV a SQLite aquí

## Fase 6 — Avanzado (opcional)
- [ ] Modo promiscuo en el ESP32 (captura pasiva de tramas, más muestras/s)
- [ ] Vista agrupada por canal (tabla + gráfico de barras)
- [ ] Modo Radar: RSSI vs ángulo, para antenas direccionales
- [ ] Heatmap con GPS (si se añade módulo GPS)

## Decisiones pendientes de tomar contigo
- Framework de GUI: ¿Tkinter (cero dependencias) o algo más vistoso?
- ¿CSV simple o SQLite desde ya? (se puede empezar en CSV y migrar en Fase 5)
- ¿Nombre definitivo del repo / del proyecto?
- ¿Licencia (MIT sugerida)?
