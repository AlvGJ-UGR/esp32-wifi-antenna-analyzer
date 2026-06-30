# ESP32 Wi-Fi Antenna Analyzer

Instrumento de medida (no un "WiFi hacker") para comparar antenas Wi-Fi
de forma objetiva usando un ESP32: cuántas redes detecta cada antena,
qué RSSI medio consigue, en qué canales rinde mejor, etc.

## Arquitectura

```
   Antena
      │
ESP32 Scanner  (firmware/)
      │
USB Serial 115200, JSON por línea
      │
Programa de PC (software/, Python)
      │
RSSI en tiempo real · Historial · Comparación · Export CSV/PDF
```

El ESP32 solo escanea y manda datos. Toda la inteligencia
(guardado, estadísticas, comparación, gráficas) vive en el PC.

## Estructura del repo

```
esp32-wifi-antenna-analyzer/
├── firmware/
│   └── esp32_wifi_scanner/
│       └── esp32_wifi_scanner.ino   # Fase 1: escaneo + envío JSON
├── software/
│   ├── serial_reader.py             # Fase 1-2: lector serial + CSV
│   └── requirements.txt
├── data/                            # CSVs generados (no versionar los grandes)
└── docs/
    └── PLAN.md                      # Plan de desarrollo por fases
```

## Cómo probar lo que hay ahora mismo (Fase 1)

1. Abre `firmware/esp32_wifi_scanner/esp32_wifi_scanner.ino` en Arduino IDE
   (o PlatformIO) y súbelo a tu ESP32.
   - **Importante**: si tu placa tiene conector de antena externa,
     comprueba que está configurada para usarla (resistencia de
     selección o conector U.FL/IPEX conmutado). Si no, estarás
     midiendo siempre la antena PCB interna.
2. Abre el Monitor Serie a 115200 baudios y comprueba que ves líneas JSON
   tipo `{"scan":1,"ssid":"...","mac":"...","rssi":-61,"channel":6,...}`.
3. Cierra el Monitor Serie (el puerto no puede estar abierto en dos sitios
   a la vez) e instala las dependencias de Python:
   ```bash
   cd software
   pip install -r requirements.txt
   ```
4. Ejecuta el lector:
   ```bash
   python serial_reader.py --port COM5 --antenna dipolo_5dbi
   ```
   (cambia `COM5` por tu puerto, en Linux/Mac suele ser algo como
   `/dev/ttyUSB0`)
5. Verás las redes detectadas en tiempo real y se irán guardando en
   `data/scan_<antena>_<fecha>.csv`.

## Estado del proyecto

Ver [docs/PLAN.md](docs/PLAN.md) para el detalle de fases y qué falta.

- [x] Fase 1 — Firmware ESP32 (escaneo + JSON por USB)
- [x] Fase 1.5 — Lector de PC mínimo (consola + CSV)
- [ ] Fase 2 — GUI en tiempo real (pestaña Scanner)
- [ ] Fase 3 — Modo Benchmark (30–60s, media/máx/mín/desviación)
- [ ] Fase 4 — Comparador de antenas por BSSID
- [ ] Fase 5 — Gráficas, export CSV/PDF, historial
- [ ] Fase 6 (opcional) — Modo promiscuo, análisis por canal, heatmap GPS, modo radar

## Licencia

Pendiente de decidir (sugerencia: MIT, para que cualquiera pueda usar
y mejorar el analizador).
