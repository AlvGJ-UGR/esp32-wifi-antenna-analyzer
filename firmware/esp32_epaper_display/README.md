# Modo standalone con pantalla e-paper (Fase 6, opcional)

Firmware alternativo para quien tenga una pantalla **Waveshare 2.13"
e-Paper HAT** conectada al ESP32. Escanea Wi-Fi periódicamente y
muestra las redes con mejor señal directamente en la pantalla — sin
depender del portátil ni de `waa-gui`. Pensado para medir en campo
(ir andando por un edificio con antena + ESP32 + pantalla + batería,
sin cable USB a un PC).

**Importante:** este es un proyecto PlatformIO **independiente** de
[`firmware/esp32_wifi_scanner/`](../esp32_wifi_scanner/) — vive en su
propia carpeta a propósito, para que quien no tenga la pantalla no
tenga que descargar sus librerías al compilar el firmware principal.
No son intercambiables: este firmware no envía el JSON por Serial que
espera `waa-scan`/`waa-gui`, así que no se puede usar con el software
de PC. Es un modo de uso alternativo, no un complemento del otro.

## Hardware probado

Desarrollado y verificado (a nivel de API, ver "Cómo se ha
verificado" más abajo) contra:

- **Waveshare 2.13" e-Paper HAT, versión V3** (blanco y negro,
  controlador SSD1680, cable plano marcado `FPC-7528B`) — la versión
  que pone en la etiqueta trasera de tu pantalla.
- ESP32-WROOM-32UE (aunque el código no depende de esa variante en
  concreto — cualquier ESP32 con SPI libre debería valer).

### Si tu pantalla es V2 o V4, o la variante tricolor (B)

- **V4**: según la propia documentación de Waveshare, el V4 es
  compatible con el driver del V3 — prueba primero sin cambiar nada.
- **V2**: usa un controlador distinto (no SSD1680) y necesita otra
  clase de GxEPD2. Cambia la clase `GxEPD2_213_BN` por la que
  corresponda a tu versión en `src/main.cpp` (dos sitios: el
  `#include` de fuentes no cambia, pero sí la declaración de
  `g_display` y su tipo) — consulta la lista completa en
  [`GxEPD2_display_selection_new_style.h`](https://github.com/ZinggJM/GxEPD2/blob/master/examples/GxEPD2_Example/GxEPD2_display_selection_new_style.h)
  del propio repositorio de GxEPD2, busca la línea que mencione tu
  modelo/controlador exacto (suele venir impreso en el propio panel o
  en su cable plano).
- **Tricolor "(B)"**: usa `GxEPD2_3C` en vez de `GxEPD2_BW` y una
  clase de driver distinta — no está soportado por este firmware tal
  cual, haría falta adaptar `DrawScreen()` para usar el color rojo
  además de blanco/negro.

## Cableado

| Pantalla   | ESP32          |
|------------|----------------|
| VCC        | 3.3V (¡nunca 5V!) |
| GND        | GND            |
| DIN (MOSI) | GPIO23 (VSPI MOSI) |
| CLK (SCK)  | GPIO18 (VSPI SCK)  |
| CS         | GPIO5          |
| DC         | GPIO17         |
| RST        | GPIO16         |
| BUSY       | GPIO4          |

MOSI/SCK usan el bus SPI por hardware del ESP32 (VSPI) y no deben
cambiarse sin tocar también el código. CS/DC/RST/BUSY sí se pueden
mover a otros GPIO libres — basta con editar las constantes
`kPinCs`/`kPinDc`/`kPinRst`/`kPinBusy` en `include/config.h`, no hace
falta tocar `main.cpp`.

## Configurar la antena a medir

Este firmware no tiene forma de recibir el nombre de la antena por
Serial (no depende de un PC para funcionar). Edita
`config::kAntennaLabel` en `include/config.h` con el nombre de la
antena que estás probando y vuelve a subir el firmware antes de cada
antena distinta — aparece en la primera línea de la pantalla.

## Compilar y subir

```bash
cd firmware/esp32_epaper_display
pio run --target upload
pio device monitor  # opcional: ver el log de cada escaneo por Serial
```

PlatformIO descarga solo `zinggjm/GxEPD2`, `adafruit/Adafruit GFX
Library` y `adafruit/Adafruit BusIO` la primera vez (no hacen falta
para el firmware principal).

## Cómo se ha verificado

El sandbox donde se escribió este firmware no tiene acceso al
registro de PlatformIO (`registry.platformio.org`), así que **no ha
podido compilarse de extremo a extremo** aquí — a diferencia del
resto del proyecto, donde sí se ejecutan tests y compilaciones reales
antes de entregar nada. En su lugar se ha verificado manualmente
línea a línea contra el código fuente real de GxEPD2 (descargado
directamente de GitHub): firma del constructor de `GxEPD2_213_BN`,
`WIDTH`/`HEIGHT` del panel, y las firmas de `init()`, `setFullWindow()`,
`setPartialWindow()`, `firstPage()`/`nextPage()` y `fillScreen()` que
usa `main.cpp`.

**Recomendación:** compílalo y súbelo tú antes de dar el hardware por
bueno, y si algo no compila o no dibuja bien, avisa — con esa
información concreta (error de compilación, o foto de lo que sale en
pantalla) se corrige mucho más rápido que adivinando a ciegas.

## Limitaciones conocidas / mejoras posibles

- El refresco parcial dibuja rápido (~0.3s) pero acumula "fantasmas"
  con el tiempo; cada 10 escaneos (`kFullRefreshEvery` en
  `config.h`) se fuerza un refresco completo (~2-4s) para limpiarlos.
- Solo muestra SSID + RSSI (no MAC/canal/seguridad) — no hay espacio
  en 250x122px para más columnas con una fuente legible.
- No implementa un "modo benchmark" en pantalla (media/desviación a
  lo largo de una ventana, como sí hace `waa-gui`) — cada refresco es
  una foto instantánea del escaneo actual. Sería una mejora natural:
  usar el botón BOOT (GPIO0) del ESP32 para arrancar una ventana de
  N escaneos y mostrar la media al terminar, reutilizando la misma
  lógica de agregación que `benchmark.py` en el lado Python (aunque
  aquí tocaría reimplementarla en C++, claro).
