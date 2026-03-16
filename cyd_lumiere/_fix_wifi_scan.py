path = r"C:\Users\ryb086\OneDrive - Groupe R.Y. Beaudoin\Bureau\CLAUDE_CODE\cyd_lumiere\src\main.cpp"
with open(path, 'r', encoding='utf-8') as f:
    code = f.read()

# Fix WiFi scan: stop BLE before scanning, restart after
old = '''void drawWifiListScreen() {
  tft.fillScreen(TFT_BLACK);
  tft.setTextFont(1);
  tft.setTextSize(2);
  tft.setTextDatum(MC_DATUM);
  tft.setTextColor(TFT_YELLOW, TFT_BLACK);
  tft.drawString("Scan WiFi...", SW / 2, SH / 2);

  int n = WiFi.scanNetworks();'''

new = '''void drawWifiListScreen() {
  tft.fillScreen(TFT_BLACK);
  tft.setTextFont(1);
  tft.setTextSize(2);
  tft.setTextDatum(MC_DATUM);
  tft.setTextColor(TFT_YELLOW, TFT_BLACK);
  tft.drawString("Scan WiFi...", SW / 2, SH / 2);

  // Stop BLE before WiFi scan (shared radio)
  if (bleInitDone) {
    NimBLEDevice::getScan()->stop();
    delay(100);
  }

  WiFi.mode(WIFI_STA);
  delay(100);
  int n = WiFi.scanNetworks();'''

code = code.replace(old, new)

with open(path, 'w', encoding='utf-8') as f:
    f.write(code)

print("WiFi scan fix applied — BLE stopped before scan")
