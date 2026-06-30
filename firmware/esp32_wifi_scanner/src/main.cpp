/**
 * ESP32 Wi-Fi Antenna Analyzer — Firmware
 * ------------------------------------------
 * Responsabilidad única: escanear redes Wi-Fi y enviar los
 * resultados por USB Serial en formato JSON, una red por línea.
 * Toda la inteligencia (guardado, estadísticas, comparación,
 * gráficas) vive en el programa de PC (ver software/).
 *
 * Formato de salida — una red detectada:
 *   {"scan":145,"ssid":"MiCasa","mac":"C8:3A:35:45:AA:90",
 *    "rssi":-61,"channel":6,"security":3}
 *
 * Formato de salida — fin de un escaneo:
 *   {"scan":145,"event":"scan_end","count":24}
 *
 * "security" es el valor numérico de wifi_auth_mode_t de
 * Arduino-ESP32 (0=OPEN, 1=WEP, 2=WPA_PSK, 3=WPA2_PSK,
 * 4=WPA_WPA2_PSK, 6=WPA3_PSK, 7=WPA2_WPA3_PSK, ...). El programa
 * de PC se encarga de traducirlo a texto.
 */

#include <Arduino.h>
#include <WiFi.h>

#include "config.h"

namespace {

unsigned long g_last_scan_time_ms = 0;
unsigned long g_scan_count = 0;

/// Escapa comillas y backslashes para que el SSID sea JSON válido.
String EscapeJsonString(String value) {
  value.replace("\\", "\\\\");
  value.replace("\"", "\\\"");
  return value;
}

void SendNetworkAsJson(unsigned long scan_id, int network_index) {
  const String ssid = EscapeJsonString(WiFi.SSID(network_index));

  uint8_t* bssid = WiFi.BSSID(network_index);
  char mac_str[18];
  snprintf(mac_str, sizeof(mac_str), "%02X:%02X:%02X:%02X:%02X:%02X", bssid[0],
           bssid[1], bssid[2], bssid[3], bssid[4], bssid[5]);

  Serial.print("{\"scan\":");
  Serial.print(scan_id);
  Serial.print(",\"ssid\":\"");
  Serial.print(ssid);
  Serial.print("\",\"mac\":\"");
  Serial.print(mac_str);
  Serial.print("\",\"rssi\":");
  Serial.print(WiFi.RSSI(network_index));
  Serial.print(",\"channel\":");
  Serial.print(WiFi.channel(network_index));
  Serial.print(",\"security\":");
  Serial.print(static_cast<int>(WiFi.encryptionType(network_index)));
  Serial.println("}");
}

void SendScanEndMarker(unsigned long scan_id, int network_count) {
  Serial.print("{\"scan\":");
  Serial.print(scan_id);
  Serial.print(",\"event\":\"scan_end\",\"count\":");
  Serial.print(network_count);
  Serial.println("}");
}

void PerformScan(unsigned long scan_id) {
  const int network_count =
      WiFi.scanNetworks(/*async=*/false, config::kShowHiddenNetworks);

  if (network_count < 0) {
    // WIFI_SCAN_FAILED (-2) u otro código de error: lo reportamos
    // como comentario de log, no como JSON, para no confundir al PC.
    Serial.print("# scan ");
    Serial.print(scan_id);
    Serial.print(" fallo, codigo ");
    Serial.println(network_count);
    return;
  }

  for (int i = 0; i < network_count; ++i) {
    SendNetworkAsJson(scan_id, i);
  }

  SendScanEndMarker(scan_id, network_count);
  WiFi.scanDelete();
}

}  // namespace

void setup() {
  Serial.begin(config::kBaudRate);
  delay(1000);

  WiFi.mode(WIFI_STA);
  WiFi.disconnect();
  delay(100);

  Serial.println("# ESP32 Wi-Fi Antenna Analyzer - listo");
}

void loop() {
  const unsigned long now = millis();
  if (now - g_last_scan_time_ms >= config::kScanIntervalMs) {
    g_last_scan_time_ms = now;
    ++g_scan_count;
    PerformScan(g_scan_count);
  }
}
