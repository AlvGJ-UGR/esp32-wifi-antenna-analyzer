# Firmware — ESP32 Wi-Fi Antenna Analyzer

Proyecto [PlatformIO](https://platformio.org/) para ESP32. Escanea redes
Wi-Fi y envía los resultados por USB Serial en JSON (ver el formato
documentado en `src/main.cpp`).

## Compilar y subir con PlatformIO

```bash
# CLI de PlatformIO (pip install platformio), desde esta carpeta:
pio run                # compilar
pio run --target upload   # compilar y subir al ESP32
pio device monitor        # abrir monitor serie a 115200 baudios
```

También puedes usar la extensión de PlatformIO para VS Code y abrir
esta carpeta (`firmware/esp32_wifi_scanner/`) como proyecto.

## Usar Arduino IDE en su lugar

Si prefieres Arduino IDE: copia `src/main.cpp` y `include/config.h` a
una carpeta de sketch (renombrando `main.cpp` a
`esp32_wifi_scanner.ino`), y sube con la placa ESP32 seleccionada. El
código es C++ estándar de Arduino, no usa nada específico de PlatformIO.

## Notas de hardware

Si tu placa tiene conector de antena externa, comprueba que está
configurada para usarla (resistencia de selección 0-ohm o conector
U.FL/IPEX conmutado, según el modelo). Si sigue usando la antena PCB
interna, las mediciones no reflejarán el rendimiento de la antena
externa que estés probando.

## Configuración

Las constantes ajustables (velocidad serie, intervalo de escaneo,
redes ocultas) están centralizadas en `include/config.h`.
