#pragma once

// Configuración del firmware standalone con pantalla e-paper.
// Ver README.md de esta carpeta para el cableado completo.

namespace config {

// --- Wi-Fi / escaneo (mismos valores que firmware/esp32_wifi_scanner) ---

constexpr unsigned long kBaudRate = 115200;
constexpr unsigned long kScanIntervalMs = 3000;  // más lento que el firmware
                                                  // principal: cada escaneo
                                                  // implica redibujar la
                                                  // pantalla, y el e-paper
                                                  // no tiene sentido
                                                  // refrescarlo cada 1s.
constexpr bool kShowHiddenNetworks = true;

// Nombre de la antena que se está probando. No hay forma de teclearlo
// en este firmware standalone (no depende de un PC ni de Serial para
// funcionar) — edítalo aquí y vuelve a subir el firmware antes de
// probar cada antena distinta.
constexpr const char* kAntennaLabel = "sin_etiquetar";

// --- Pantalla ---

// Cuántas redes (las de mejor señal) se muestran a la vez. La
// pantalla es de 250x122px; con la fuente usada caben ~5 líneas
// cómodamente sin apretar el texto.
constexpr int kMaxNetworksShown = 5;

// El refresco parcial deja rastro ("fantasmas") tras muchos
// ciclos, es una limitación conocida de los paneles e-paper con
// refresco parcial (recomendación habitual de Waveshare). Cada
// kFullRefreshEvery escaneos se fuerza un refresco completo (más
// lento, ~2s, pero limpia la pantalla del todo) en vez de parcial
// (~0.3s).
constexpr unsigned long kFullRefreshEvery = 10;

// --- Pines (ESP32 VSPI estándar, wiring recomendado por la librería
//     GxEPD2 para el HAT de Waveshare sobre un ESP32 DevKit) ---
//
//   Pantalla    ESP32
//   VCC      -> 3.3V   (¡nunca 5V!)
//   GND      -> GND
//   DIN/MOSI -> GPIO23 (VSPI MOSI, hardware SPI, no cambiar sin tocar
//                        también el código)
//   CLK/SCK  -> GPIO18 (VSPI SCK, ídem)
//   CS       -> GPIO5
//   DC       -> GPIO17
//   RST      -> GPIO16
//   BUSY     -> GPIO4
//
// CS/DC/RST/BUSY sí se pueden mover a otros GPIO libres si tu
// cableado lo necesita — basta con cambiar las constantes de abajo,
// no hace falta tocar main.cpp.
constexpr int kPinCs = 5;
constexpr int kPinDc = 17;
constexpr int kPinRst = 16;
constexpr int kPinBusy = 4;

}  // namespace config
