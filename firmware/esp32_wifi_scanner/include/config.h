#pragma once

// Configuración del firmware del Wi-Fi Antenna Analyzer.
// Centralizar estas constantes aquí facilita ajustar el
// comportamiento sin tocar la lógica en main.cpp.

namespace config {

// Velocidad del puerto serie hacia el PC.
constexpr unsigned long kBaudRate = 115200;

// Tiempo entre escaneos consecutivos, en milisegundos.
constexpr unsigned long kScanIntervalMs = 1000;

// Incluir redes con SSID oculto en los resultados del escaneo.
constexpr bool kShowHiddenNetworks = true;

}  // namespace config
