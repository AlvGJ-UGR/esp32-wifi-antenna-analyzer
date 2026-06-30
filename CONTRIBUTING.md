# Guía de contribución

Gracias por el interés en mejorar el ESP32 Wi-Fi Antenna Analyzer.

## Estructura del repo

- `firmware/esp32_wifi_scanner/` — proyecto PlatformIO para el ESP32.
- `software/` — paquete Python instalable (`wifi_antenna_analyzer`).
- `docs/PLAN.md` — plan de desarrollo por fases, con checklist.
- `data/` — salida de CSVs de ejemplo (ignorado por git salvo `.gitkeep`).

## Entorno de desarrollo (software)

```bash
cd software
python -m venv .venv
source .venv/bin/activate   # En Windows: .venv\Scripts\activate
pip install -e ".[dev]"
```

Esto instala el paquete en modo editable más las herramientas de
desarrollo (pytest, ruff, black).

### Tests

```bash
pytest
```

### Lint y formato

```bash
ruff check .
black .
```

El CI (`.github/workflows/ci.yml`) ejecuta lo mismo en cada push/PR,
además de compilar el firmware con PlatformIO.

## Entorno de desarrollo (firmware)

```bash
cd firmware/esp32_wifi_scanner
pio run                    # compilar
pio run --target upload    # compilar y subir
pio device monitor         # monitor serie
```

## Convenciones de código

- Python: tipado con type hints, docstrings en los módulos/clases
  públicos, `black` para formato y `ruff` para lint. Evitar `print()`
  fuera de la CLI; usar el módulo `logging` en el resto del código.
- C++ (firmware): un único fichero `src/main.cpp` mientras el
  proyecto sea pequeño; si crece, separar en módulos bajo `src/` e
  `include/`. Constantes de configuración van en `include/config.h`,
  no como literales sueltos en el código.
- Commits descriptivos en español o inglés, indistintamente, pero
  consistentes dentro del mismo PR.

## Antes de abrir un PR

1. `pytest` y `ruff check .` en verde dentro de `software/`.
2. `pio run` en verde dentro de `firmware/esp32_wifi_scanner/`.
3. Actualiza `docs/PLAN.md` si tu cambio completa o modifica una fase.
