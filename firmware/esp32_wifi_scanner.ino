/*
 * ESP32 Wi-Fi Antenna Analyzer — Firmware (Fase 1)
 * --------------------------------------------------
 * El ESP32 solo escanea redes y manda los resultados por
 * USB Serial en formato JSON (una red por línea). Toda la
 * "inteligencia" (guardado, gráficas, comparación) vive en
 * el programa de PC.
 *
 * Formato de salida (una línea JSON por red detectada):
 *   {"scan":145,"ssid":"MiCasa","mac":"C8:3A:35:45:AA:90","rssi":-61,"channel":6,"security":3}
 *
 * Al terminar cada escaneo se manda un marcador:
 *   {"scan":145,"event":"scan_end","count":24}
 *
 * "security" es el valor numérico de wifi_auth_mode_t de Arduino-ESP32
 * (0=OPEN, 1=WEP, 2=WPA_PSK, 3=WPA2_PSK, 4=WPA_WPA2_PSK, ...).
 * El programa de PC se encarga de traducirlo a texto si hace falta.
 */

#include <WiFi.h>

const unsigned long SCAN_INTERVAL_MS = 1000; // tiempo entre escaneos
unsigned long lastScanTime = 0;
unsigned long scanCount = 0;

void setup() {
  Serial.begin(115200);
  delay(1000);

  WiFi.mode(WIFI_STA);
  WiFi.disconnect();
  delay(100);

  // Mensaje de arranque (no es JSON a propósito, así el PC sabe
  // distinguir "ruido" de líneas válidas si hace falta depurar)
  Serial.println("# ESP32 Wi-Fi Antenna Analyzer - Fase 1 - listo");
}

void loop() {
  unsigned long now = millis();
  if (now - lastScanTime >= SCAN_INTERVAL_MS) {
    lastScanTime = now;
    scanCount++;
    performScan(scanCount);
  }
}

void performScan(unsigned long scanId) {
  // show_hidden = true para no perder redes con SSID oculto
  int n = WiFi.scanNetworks(/*async=*/false, /*show_hidden=*/true);

  for (int i = 0; i < n; i++) {
    sendNetworkJson(scanId, i);
  }

  // Marcador de fin de escaneo: así el PC sabe cuándo "cerrar" la tabla
  Serial.print("{\"scan\":");
  Serial.print(scanId);
  Serial.print(",\"event\":\"scan_end\",\"count\":");
  Serial.print(n);
  Serial.println("}");

  WiFi.scanDelete();
}

void sendNetworkJson(unsigned long scanId, int idx) {
  String ssid = WiFi.SSID(idx);
  ssid.replace("\\", "\\\\");
  ssid.replace("\"", "\\\"");

  uint8_t* bssid = WiFi.BSSID(idx);
  char macStr[18];
  snprintf(macStr, sizeof(macStr), "%02X:%02X:%02X:%02X:%02X:%02X",
           bssid[0], bssid[1], bssid[2], bssid[3], bssid[4], bssid[5]);

  Serial.print("{\"scan\":");
  Serial.print(scanId);
  Serial.print(",\"ssid\":\"");
  Serial.print(ssid);
  Serial.print("\",\"mac\":\"");
  Serial.print(macStr);
  Serial.print("\",\"rssi\":");
  Serial.print(WiFi.RSSI(idx));
  Serial.print(",\"channel\":");
  Serial.print(WiFi.channel(idx));
  Serial.print(",\"security\":");
  Serial.print((int)WiFi.encryptionType(idx));
  Serial.println("}");
}
