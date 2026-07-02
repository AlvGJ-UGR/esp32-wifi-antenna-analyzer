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

## Notas de hardware — ESP32-WROOM-32UE

El comportamiento del conector de antena depende del módulo exacto
que lleve tu placa:

- **ESP32-WROOM-32UE / -32U** (conector U.FL/IPEX, sin antena PCB):
  no hay resistencia de selección que mover ni nada que configurar —
  a diferencia del WROOM-32D/-32E, este módulo *no tiene* antena
  impresa en la placa, así que toda la señal sale siempre por el
  conector U.FL. **Importante:** el módulo se vende sin antena; si
  no le has conectado una, no transmite ni recibe nada útil. El
  conector es compatible indistintamente con U.FL (Hirose), MHF-I
  (I-PEX) y AMC (Amphenol) — son el mismo contacto con nombres
  comerciales distintos, cualquier antena/pigtail 2.4GHz con uno de
  esos tres conectores sirve. (Fuente: [datasheet oficial
  ESP32-WROOM-32E/-32UE](https://www.espressif.com/sites/default/files/documentation/esp32-wroom-32e_esp32-wroom-32ue_datasheet_en.pdf).)
- **ESP32-WROOM-32D / -32E / WROVER** (antena PCB de fábrica): si tu
  placa monta uno de estos y le has añadido un conector externo por
  tu cuenta, sí hay que comprobar la resistencia de selección de
  0-ohm entre antena PCB y conector — revisa la serigrafía de tu
  placa concreta, varía según el fabricante.

Si vas a publicar o vender algo basado en este proyecto (no aplica a
uso personal/laboratorio): la certificación FCC del WROOM-32UE se
hizo con una antena de 4.0 dBi de ganancia; usar una antena de
ganancia igual o menor mantiene el módulo dentro de su
precertificación. Ganancias mayores pueden requerir repetir pruebas
de EMC.

## Configuración

Las constantes ajustables (velocidad serie, intervalo de escaneo,
redes ocultas) están centralizadas en `include/config.h`.
