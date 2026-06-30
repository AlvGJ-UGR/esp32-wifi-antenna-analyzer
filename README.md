## ESP32 Wi-Fi Antenna Analyzer

[![CI](https://github.com/TU_USUARIO/esp32-wifi-antenna-analyzer/actions/workflows/ci.yml/badge.svg)](https://github.com/AlvGJ-UGR/esp32-wifi-antenna-analyzer/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

Instrumento de medida (no un "Wi-Fi hacker") para comparar antenas
Wi-Fi de forma objetiva usando un ESP32 como sensor RSSI: cuántas
redes detecta cada antena, qué RSSI medio consigue, en qué canales
rinde mejor, etc.



### Arquitectura

```
   Antena
      │
ESP32 Scanner          firmware/esp32_wifi_scanner  (PlatformIO, C++)
      │
USB Serial 115200, JSON por línea
      │
Programa de PC         software/  (paquete Python "wifi_antenna_analyzer")
      │
RSSI en tiempo real · Historial · Comparación · Export CSV/PDF
```

El ESP32 solo escanea y manda datos por Serial; toda la inteligencia
(guardado, estadísticas, comparación, gráficas) vive en el PC. Esa
separación es deliberada: mantiene el firmware simple y testeable, y
permite iterar la lógica de análisis sin volver a flashear la placa.

### Estructura del repo

```
esp32-wifi-antenna-analyzer/
├── .github/workflows/ci.yml      # tests + lint + build del firmware en cada push
├── firmware/esp32_wifi_scanner/  # proyecto PlatformIO
│   ├── platformio.ini
│   ├── include/config.h          # constantes (baudrate, intervalo de escaneo...)
│   └── src/main.cpp
├── software/                     # paquete Python instalable
│   ├── pyproject.toml
│   ├── src/wifi_antenna_analyzer/
│   │   ├── models.py             # NetworkSample, ScanEnd, BenchmarkResult, SecurityType
│   │   ├── serial_link.py        # conexión + parseo del protocolo JSON
│   │   ├── storage.py            # persistencia (CSV hoy, SQLite en Fase 5)
│   │   ├── cli.py                # `waa-scan` — versión de consola
│   │   └── gui/app.py            # `waa-gui` — interfaz gráfica (Tkinter)
│   └── tests/                    # pytest, sin necesidad de hardware
├── data/                         # CSVs generados (ignorados por git salvo .gitkeep)
├── docs/PLAN.md                  # plan de desarrollo por fases
├── CONTRIBUTING.md
└── LICENSE                       # MIT
```

### Instalación rápida (software)

```bash
cd software
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
```

Esto instala el paquete y dos comandos:

- `waa-scan --port COM5 --antenna dipolo_5dbi` — lector de consola, guarda en `data/*.csv`.
- `waa-gui` — interfaz gráfica con la pestaña Scanner en tiempo real.

### Firmware (ESP32)

```bash
cd firmware/esp32_wifi_scanner
pio run --target upload   # requiere PlatformIO (pip install platformio)
pio device monitor
```

Detalles y alternativa con Arduino IDE en
[`firmware/esp32_wifi_scanner/README.md`](firmware/esp32_wifi_scanner/README.md).

**Importante:** si tu placa tiene conector de antena externa,
comprueba que está configurada para usarla (resistencia de selección
o conector U.FL/IPEX conmutado, según el modelo). Si sigue usando la
antena PCB interna, las mediciones no reflejarán la antena externa.

### Desarrollo y tests

Ver [CONTRIBUTING.md](CONTRIBUTING.md). En resumen:

```bash
cd software && pytest && ruff check . && black --check .
cd firmware/esp32_wifi_scanner && pio run
```

Todo esto se ejecuta automáticamente en CI en cada push/PR.

### Estado del proyecto

Ver [docs/PLAN.md](docs/PLAN.md) para el detalle completo.

- [x] Fase 1 — Firmware ESP32 (escaneo + JSON por USB), como proyecto PlatformIO
- [x] Fase 1.5 — Paquete Python con capa serial/storage testeada (`waa-scan`)
- [x] Fase 2 — GUI en tiempo real, pestaña Scanner (`waa-gui`)
- [ ] Fase 3 — Modo Benchmark (30–60s, media/máx/mín/desviación)
- [ ] Fase 4 — Comparador de antenas por BSSID
- [ ] Fase 5 — Gráficas, export CSV/PDF, historial (posible migración a SQLite)
- [ ] Fase 6 (opcional) — Modo promiscuo, análisis por canal, heatmap GPS, modo radar

### Licencia

MIT — ver [LICENSE](LICENSE). Recuerda rellenar tu nombre en el
copyright antes de publicar.
