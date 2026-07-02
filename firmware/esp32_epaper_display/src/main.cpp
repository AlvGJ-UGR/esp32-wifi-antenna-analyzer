/**
 * ESP32 Wi-Fi Antenna Analyzer — Modo standalone con pantalla e-paper
 * --------------------------------------------------------------------
 * Firmware independiente del principal (firmware/esp32_wifi_scanner):
 * no envía nada por Serial en JSON, sino que escanea Wi-Fi
 * periódicamente y muestra las redes con mejor señal directamente en
 * una pantalla Waveshare 2.13" e-Paper HAT V3 (blanco y negro,
 * controlador SSD1680). Pensado para medir en campo sin necesitar el
 * portátil conectado: solo ESP32 + pantalla + batería.
 *
 * Ver README.md de esta carpeta para el cableado y para qué hacer si
 * tu pantalla es V2/V4 en vez de V3, o la variante tricolor (B).
 */

#include <Arduino.h>
#include <WiFi.h>

#include <algorithm>
#include <vector>

#include <GxEPD2_BW.h>
#include <Fonts/FreeMonoBold9pt7b.h>
#include <Fonts/FreeSans9pt7b.h>

#include "config.h"

namespace {

GxEPD2_BW<GxEPD2_213_BN, GxEPD2_213_BN::HEIGHT> g_display(
    GxEPD2_213_BN(config::kPinCs, config::kPinDc, config::kPinRst, config::kPinBusy));

unsigned long g_last_scan_time_ms = 0;
unsigned long g_scan_count = 0;

struct NetworkEntry {
  String ssid;
  int32_t rssi;
};

bool RssiDescending(const NetworkEntry& a, const NetworkEntry& b) {
  return a.rssi > b.rssi;
}

/// Escanea y devuelve las redes ordenadas de mejor a peor señal.
/// No incluye MAC/canal/seguridad (a diferencia del firmware
/// principal): en pantalla solo cabe SSID + RSSI con esta resolución.
std::vector<NetworkEntry> ScanNetworksSortedByRssi() {
  std::vector<NetworkEntry> networks;

  const int network_count =
      WiFi.scanNetworks(/*async=*/false, config::kShowHiddenNetworks);
  if (network_count <= 0) {
    WiFi.scanDelete();
    return networks;  // vacío: 0 redes, o -1/-2 = error de escaneo
  }

  networks.reserve(network_count);
  for (int i = 0; i < network_count; ++i) {
    NetworkEntry entry;
    entry.ssid = WiFi.SSID(i);
    if (entry.ssid.isEmpty()) {
      entry.ssid = "(oculta)";
    }
    entry.rssi = WiFi.RSSI(i);
    networks.push_back(entry);
  }
  WiFi.scanDelete();

  std::sort(networks.begin(), networks.end(), RssiDescending);
  return networks;
}

/// Recorta un SSID a `max_len` caracteres para que quepa en pantalla,
/// añadiendo "…" si se ha recortado.
String TruncateSsid(const String& ssid, size_t max_len) {
  if (ssid.length() <= max_len) {
    return ssid;
  }
  return ssid.substring(0, max_len - 1) + ".";
}

void DrawScreen(const std::vector<NetworkEntry>& networks) {
  g_display.fillScreen(GxEPD_WHITE);
  g_display.setTextColor(GxEPD_BLACK);

  g_display.setFont(&FreeMonoBold9pt7b);
  g_display.setCursor(2, 14);
  g_display.print("Antena: ");
  g_display.print(config::kAntennaLabel);

  g_display.setFont(&FreeSans9pt7b);
  int y = 34;
  const size_t shown =
      std::min(networks.size(), static_cast<size_t>(config::kMaxNetworksShown));

  if (shown == 0) {
    g_display.setCursor(2, y);
    g_display.print("Sin redes detectadas");
  }
  for (size_t i = 0; i < shown; ++i) {
    g_display.setCursor(2, y);
    const String ssid = TruncateSsid(networks[i].ssid, 15);
    g_display.printf("%-15s %4ddBm", ssid.c_str(), static_cast<int>(networks[i].rssi));
    y += 18;
  }

  g_display.setFont(nullptr);
  g_display.setCursor(2, g_display.height() - 4);
  g_display.printf("scan #%lu  (%u redes)", g_scan_count,
                    static_cast<unsigned>(networks.size()));
}

/// Redibuja la pantalla completa. `full_refresh` fuerza un refresco
/// completo (más lento, sin "fantasmas"); si no, usa refresco parcial
/// (rápido, pero acumula rastro con el tiempo — ver kFullRefreshEvery
/// en config.h).
void RefreshDisplay(const std::vector<NetworkEntry>& networks, bool full_refresh) {
  if (full_refresh) {
    g_display.setFullWindow();
  } else {
    g_display.setPartialWindow(0, 0, g_display.width(), g_display.height());
  }

  g_display.firstPage();
  do {
    DrawScreen(networks);
  } while (g_display.nextPage());
}

}  // namespace

void setup() {
  Serial.begin(config::kBaudRate);
  delay(1000);

  WiFi.mode(WIFI_STA);
  WiFi.disconnect();
  delay(100);

  g_display.init(115200, /*initial=*/true);
  g_display.setRotation(1);  // panel nativo 122x250 (vertical) -> 250x122 horizontal

  Serial.println("# ESP32 Wi-Fi Antenna Analyzer (modo e-paper) - listo");
  Serial.print("# Antena configurada: ");
  Serial.println(config::kAntennaLabel);
}

void loop() {
  const unsigned long now = millis();
  if (g_last_scan_time_ms != 0 && (now - g_last_scan_time_ms) < config::kScanIntervalMs) {
    delay(50);
    return;
  }
  g_last_scan_time_ms = now;
  ++g_scan_count;

  const std::vector<NetworkEntry> networks = ScanNetworksSortedByRssi();

  const bool full_refresh =
      (g_scan_count == 1) || (g_scan_count % config::kFullRefreshEvery == 0);
  RefreshDisplay(networks, full_refresh);

  Serial.print("# scan ");
  Serial.print(g_scan_count);
  Serial.print(": ");
  Serial.print(networks.size());
  Serial.println(" redes");
}
