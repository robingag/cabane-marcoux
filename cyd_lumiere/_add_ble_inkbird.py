"""
Ajouter BLE NimBLE scan pour Inkbird IBS-TH2 (temperature + humidite ambiante)
- Scan BLE toutes les 30 secondes
- Parse manufacturer data des capteurs "sps" (Inkbird)
- Publie temp + humidity via MQTT
- Affiche sur ecran TFT
"""
import re

PATH = r"C:\Users\ryb086\OneDrive - Groupe R.Y. Beaudoin\Bureau\CLAUDE_CODE\cyd_lumiere\src\main.cpp"

with open(PATH, 'r', encoding='utf-8') as f:
    code = f.read()

# 1. Ajouter #include NimBLE apres #include <qrcode.h>
code = code.replace(
    '#include <qrcode.h>',
    '#include <qrcode.h>\n#include <NimBLEDevice.h>'
)

# 2. Ajouter variables BLE et humidity apres "float temperature = 0.0;"
code = code.replace(
    'float temperature = 0.0;',
    'float temperature = 0.0;\n'
    'float humidity = 0.0;\n'
    'int bleBattery = -1;\n'
    'unsigned long lastBleScan = 0;\n'
    'const unsigned long BLE_SCAN_INTERVAL = 30000; // 30 sec\n'
    'bool bleInitDone = false;\n'
    'String mqttTopicHumidity;'
)

# 3. Ajouter MQTT topic humidity dans setup (apres mqttTopicTemp)
code = code.replace(
    'mqttTopicTemp = "cyd/" + deviceId + "/temp";',
    'mqttTopicTemp = "cyd/" + deviceId + "/temp";\n'
    '  mqttTopicHumidity = "cyd/" + deviceId + "/humidity";'
)

# 4. Ajouter publish humidity dans publishState
code = code.replace(
    '    mqtt.publish(mqttTopicTemp.c_str(), String(temperature, 1).c_str(), true);',
    '    mqtt.publish(mqttTopicTemp.c_str(), String(temperature, 1).c_str(), true);\n'
    '    mqtt.publish(mqttTopicHumidity.c_str(), String(humidity, 1).c_str(), true);'
)

# 5. Ajouter forward declaration pour BLE
code = code.replace(
    'void drawTempCard();',
    'void drawTempCard();\n'
    'void bleScanInkbird();'
)

# 6. Ajouter la fonction BLE scan avant "// ---- Setup ----"
ble_scan_func = '''
// ---- BLE Inkbird IBS-TH2 ----
class InkbirdScanCallback : public NimBLEScanCallbacks {
  void onResult(const NimBLEAdvertisedDevice* device) override {
    // IBS-TH2 advertise comme "sps"
    if (device->getName() == "sps") {
      // Parser manufacturer data
      if (device->haveManufacturerData()) {
        String mfData = device->getManufacturerData();
        if (mfData.length() >= 9) {
          // UUID (2 premiers bytes, little endian) = temperature * 100
          int16_t rawTemp = (uint8_t)mfData[0] | ((uint8_t)mfData[1] << 8);
          float temp = rawTemp / 100.0f;
          // Humidity: bytes 2-3 (little endian) / 100
          uint16_t rawHum = (uint8_t)mfData[2] | ((uint8_t)mfData[3] << 8);
          float hum = rawHum / 100.0f;
          // Battery: byte 7
          int bat = (uint8_t)mfData[7];

          // Valider les donnees
          if (temp > -40.0 && temp < 80.0 && hum >= 0 && hum <= 100) {
            temperature = temp;
            humidity = hum;
            bleBattery = bat;
            Serial.printf("BLE Inkbird: %.1fC, %.1f%%, bat=%d%%\\n", temp, hum, bat);
          }
        }
      }
    }
  }
};

InkbirdScanCallback inkbirdCallback;

void bleInitInkbird() {
  NimBLEDevice::init("CYD");
  NimBLEDevice::setPower(ESP_PWR_LVL_P3);
  NimBLEScan* pScan = NimBLEDevice::getScan();
  pScan->setScanCallbacks(&inkbirdCallback, false);
  pScan->setActiveScan(true);
  pScan->setInterval(100);
  pScan->setWindow(99);
  bleInitDone = true;
  Serial.println("BLE NimBLE init OK - scan Inkbird IBS-TH2");
}

void bleScanInkbird() {
  if (!bleInitDone) return;
  NimBLEScan* pScan = NimBLEDevice::getScan();
  // Scan async pendant 5 secondes
  pScan->start(5, false);
}

'''

code = code.replace(
    '// ---- Setup ----',
    ble_scan_func + '// ---- Setup ----'
)

# 7. Ajouter BLE init dans setup (apres MQTT setup)
code = code.replace(
    '  // Web server routes',
    '  // BLE Inkbird init\n'
    '  bleInitInkbird();\n\n'
    '  // Web server routes'
)

# 8. Ajouter BLE scan periodique dans loop (avant lecture ultrasonique)
code = code.replace(
    '  // Lecture periodique capteur ultrasonique',
    '  // BLE scan periodique Inkbird\n'
    '  if (millis() - lastBleScan >= BLE_SCAN_INTERVAL) {\n'
    '    lastBleScan = millis();\n'
    '    bleScanInkbird();\n'
    '    // Publier temp + humidity via MQTT\n'
    '    if (mqtt.connected()) {\n'
    '      mqtt.publish(mqttTopicTemp.c_str(), String(temperature, 1).c_str(), true);\n'
    '      mqtt.publish(mqttTopicHumidity.c_str(), String(humidity, 1).c_str(), true);\n'
    '    }\n'
    '    // Rafraichir ecran\n'
    '    if (currentScreen == SCREEN_MAIN && !menuOpen) drawTempCard();\n'
    '  }\n\n'
    '  // Lecture periodique capteur ultrasonique'
)

# 9. Modifier drawTempCard pour afficher aussi l'humidite
old_temp_card = '''void drawTempCard() {
  int cx = 162, cy = 34, cw = 154, ch = 34;
  tft.fillRect(cx, cy, cw, 2, C_CYAN);
  tft.fillRoundRect(cx, cy + 2, cw, ch - 2, 4, C_CARD);
  tft.drawRoundRect(cx, cy + 2, cw, ch - 2, 4, C_BORDER);
  tft.setTextFont(1); tft.setTextSize(1);
  tft.setTextDatum(TL_DATUM);
  tft.setTextColor(C_TXT_GRAY, C_CARD);
  tft.drawString("TEMPERATURE", cx + 8, cy + 5);
  tft.setTextSize(2);
  tft.setTextDatum(MC_DATUM);
  tft.setTextColor(C_CYAN, C_CARD);
  String tempStr = String(temperature, 1) + "C";
  tft.drawString(tempStr.c_str(), cx + cw / 2, cy + 24);
}'''

new_temp_card = '''void drawTempCard() {
  int cx = 162, cy = 34, cw = 154, ch = 34;
  tft.fillRect(cx, cy, cw, 2, C_CYAN);
  tft.fillRoundRect(cx, cy + 2, cw, ch - 2, 4, C_CARD);
  tft.drawRoundRect(cx, cy + 2, cw, ch - 2, 4, C_BORDER);
  tft.setTextFont(1); tft.setTextSize(1);
  tft.setTextDatum(TL_DATUM);
  tft.setTextColor(C_TXT_GRAY, C_CARD);
  tft.drawString("TEMP / HUMID", cx + 8, cy + 5);
  tft.setTextSize(2);
  tft.setTextDatum(MC_DATUM);
  tft.setTextColor(C_CYAN, C_CARD);
  String tempStr = String(temperature, 1) + "C";
  if (humidity > 0) {
    tempStr += " " + String((int)humidity) + "%";
  }
  tft.drawString(tempStr.c_str(), cx + cw / 2, cy + 24);
}'''

code = code.replace(old_temp_card, new_temp_card)

with open(PATH, 'w', encoding='utf-8') as f:
    f.write(code)

print("OK - BLE Inkbird IBS-TH2 ajoute au firmware")
print("- #include NimBLEDevice.h")
print("- Variables: humidity, bleBattery, lastBleScan")
print("- MQTT topic: cyd/{id}/humidity")
print("- BLE scan toutes les 30 sec, parse 'sps' devices")
print("- Ecran: TEMP / HUMID avec temperature + humidite")
print("")
print("Prochaine etape: pio run --target upload")
