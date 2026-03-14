path = r"C:\Users\ryb086\OneDrive - Groupe R.Y. Beaudoin\Bureau\CLAUDE_CODE\cyd_lumiere\src\main.cpp"
with open(path, 'r', encoding='utf-8') as f:
    code = f.read()

old = '''  // Stop BLE before WiFi scan (shared radio)
  if (bleInitDone) {
    NimBLEDevice::getScan()->stop();
    delay(100);
  }

  WiFi.mode(WIFI_STA);
  delay(100);
  int n = WiFi.scanNetworks();'''

new = '''  // Stop BLE before WiFi scan (shared radio)
  if (bleInitDone) {
    NimBLEDevice::getScan()->stop();
    NimBLEDevice::deinit(true);
    bleInitDone = false;
    delay(200);
    Serial.println("BLE stopped for WiFi scan");
  }

  WiFi.disconnect(true);
  delay(100);
  WiFi.mode(WIFI_STA);
  delay(500);
  Serial.println("Starting WiFi scan...");
  int n = WiFi.scanNetworks();
  Serial.printf("WiFi scan result: %d networks\n", n);'''

code = code.replace(old, new)

with open(path, 'w', encoding='utf-8') as f:
    f.write(code)

print("WiFi scan v2 fix: BLE deinit + WiFi disconnect before scan")
