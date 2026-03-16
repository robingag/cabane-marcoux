"""
Fix NimBLE 1.4.x API changes:
- onResult takes const pointer, need non-const cast
- getManufacturerData returns std::string
- setScanCallbacks -> setCallbacks
"""

PATH = r"C:\Users\ryb086\OneDrive - Groupe R.Y. Beaudoin\Bureau\CLAUDE_CODE\cyd_lumiere\src\main.cpp"

with open(PATH, 'r', encoding='utf-8') as f:
    code = f.read()

# Fix the entire BLE scan callback and init
old_ble = '''// ---- BLE Inkbird IBS-TH2 ----
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
}'''

new_ble = '''// ---- BLE Inkbird IBS-TH2 ----
class InkbirdScanCallback : public NimBLEScanCallbacks {
  void onResult(NimBLEAdvertisedDevice* device) override {
    // IBS-TH2 advertise comme "sps"
    std::string devName = device->getName();
    if (devName == "sps") {
      // Parser manufacturer data
      if (device->haveManufacturerData()) {
        std::string mfData = device->getManufacturerData();
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
  pScan->setCallbacks(&inkbirdCallback, false);
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
}'''

code = code.replace(old_ble, new_ble)

with open(PATH, 'w', encoding='utf-8') as f:
    f.write(code)

print("OK - API NimBLE 1.4.x fixee")
print("- onResult(NimBLEAdvertisedDevice*) sans const")
print("- std::string au lieu de String")
print("- setCallbacks au lieu de setScanCallbacks")
