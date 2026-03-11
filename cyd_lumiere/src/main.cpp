#include <Arduino.h>
#include <SPI.h>
#include <TFT_eSPI.h>
#include <WiFi.h>
#include <WebServer.h>
#include <Preferences.h>
#include <PubSubClient.h>
#include <qrcode.h>

TFT_eSPI tft = TFT_eSPI();
WebServer server(80);
Preferences prefs;

// MQTT
// SECURITE: broker public sans TLS/auth. Tout appareil connaissant le deviceId
// peut publier/souscrire. Pour un usage production, utiliser un broker prive
// avec TLS (port 8883) et authentification username/password.
WiFiClient mqttWifi;
PubSubClient mqtt(mqttWifi);
String deviceId;         // Last 6 hex of MAC (unique ID)
String mqttTopicState;   // cyd/{id}/state
String mqttTopicCmd;     // cyd/{id}/cmd
String mqttTopicDompeur; // cyd/{id}/dompeur
String mqttTopicTemp;    // cyd/{id}/temp
String mqttTopicBasin1;  // cyd/{id}/basin1
String mqttTopicBasin2;  // cyd/{id}/basin2
String mqttTopicBasin3;  // cyd/{id}/basin3
const char* MQTT_BROKER = "broker.hivemq.com";
const int MQTT_PORT = 1883;
unsigned long lastMqttRetry = 0;

// CYD XPT2046 touch pins (VSPI bus)
#define T_CLK  25
#define T_CS   33
#define T_DIN  32
#define T_DO   39
#define T_IRQ  36

SPIClass touchSPI(VSPI);

// Screen (landscape)
const int SW = 320;
const int SH = 240;

// Color palette (industrial dark theme - matches HTML dashboard)
const uint16_t C_BG       = 0x0841;  // #080a0e deep black
const uint16_t C_CARD     = 0x0883;  // #0c1018 dark card
const uint16_t C_BORDER   = 0x1986;  // #1a2332 border
const uint16_t C_HEADER   = 0x08A4;  // #0d1520 dark header
const uint16_t C_AMBER    = 0xF4E1;  // #f59e0b amber accent
const uint16_t C_CYAN     = 0x35FF;  // #38bdf8 temperature
const uint16_t C_GREEN    = 0x2629;  // #22c55e green
const uint16_t C_RED      = 0xEA28;  // #ef4444 red
const uint16_t C_YELLOW   = 0xF4E1;  // same as amber
const uint16_t C_BLUE     = 0x3C1E;  // #3b82f6 graph accent
const uint16_t C_TXT      = 0xF7BE;  // #f1f5f9 white text
const uint16_t C_TXT_GRAY = 0x63B1;  // #64748b labels
const uint16_t C_TXT_DIM  = 0x4B10;  // #4a6080 status
const uint16_t C_LABEL    = 0x9517;  // #94a3b8 basin names
const uint16_t C_SB_BG    = 0x0042;  // #060810 status bar bg
const uint16_t C_HDL_BG   = 0x1927;  // #1c2538 handle bg
const uint16_t C_HDL_BD   = 0x2A0A;  // #2a3a52 handle border


// Maple leaf bitmap 11x13 (1=red pixel)
const uint16_t C_MAPLE = 0xE000; // bright red
const unsigned char mapleLeaf[] = {
  0b00100000, 0b00000000,  // row 0:    .....X.....
  0b01110000, 0b00000000,  // row 1:    ....XXX....
  0b01110000, 0b00000000,  // row 2:    ....XXX....
  0b11111110, 0b00000000,  // row 3:    .XXXXXXX...
  0b11111111, 0b00000000,  // row 4:    XXXXXXXX...
  0b01111111, 0b10000000,  // row 5:    .XXXXXXXXX.
  0b00111111, 0b00000000,  // row 6:    ..XXXXXXX..
  0b00011111, 0b00000000,  // row 7:    ...XXXXX...
  0b00111111, 0b00000000,  // row 8:    ..XXXXXXX..
  0b01111111, 0b10000000,  // row 9:    .XXXXXXXXX.
  0b00011110, 0b00000000,  // row 10:   ...XXXX....
  0b00001100, 0b00000000,  // row 11:   ....XX.....
  0b00001100, 0b00000000,  // row 12:   ....XX.....
};
#define MAPLE_W 11
#define MAPLE_H 13

void drawMapleLeaf(int x, int y, int scale) {
  for (int row = 0; row < MAPLE_H; row++) {
    uint16_t rowBits = (mapleLeaf[row * 2] << 8) | mapleLeaf[row * 2 + 1];
    for (int col = 0; col < MAPLE_W; col++) {
      if (rowBits & (0x8000 >> col)) {
        tft.fillRect(x + col * scale, y + row * scale, scale, scale, C_MAPLE);
      }
    }
  }
}

bool lightOn = false;

// Sensor data
String dompeurTime = "--:--";
float temperature = 0.0;
int basin1 = 0;  // 0-100%
int basin2 = 0;
int basin3 = 0;

// Dompeur trend graph
#define GRAPH_MAX 30
int dompeurHist[GRAPH_MAX];
int graphCount = 0;

void addDompeurPoint(int seconds) {
  if (graphCount < GRAPH_MAX) {
    dompeurHist[graphCount++] = seconds;
  } else {
    memmove(dompeurHist, dompeurHist + 1, (GRAPH_MAX - 1) * sizeof(int));
    dompeurHist[GRAPH_MAX - 1] = seconds;
  }
}

// ---- Screen states ----
enum Screen { SCREEN_MAIN, SCREEN_WIFI_LIST, SCREEN_WIFI_PASS, SCREEN_WIFI_CONNECTING, SCREEN_WIFI_FAIL, SCREEN_QR_LOCAL, SCREEN_QR_REMOTE, SCREEN_INFO };
Screen currentScreen = SCREEN_MAIN;

// Non-blocking WiFi connection
unsigned long wifiConnectStart = 0;
const unsigned long WIFI_CONNECT_TIMEOUT = 15000; // 15s max

// Dropdown menu
bool menuOpen = false;
#define MENU_ITEMS   4
#define MENU_X       2
#define MENU_Y       28
#define MENU_W       140
#define MENU_ITEM_H  32
#define MENU_H       (MENU_ITEMS * MENU_ITEM_H + 2)
const char* menuLabels[MENU_ITEMS] = { "WiFi", "QR Local", "QR Remote", "Infos" };

// WiFi scan results
#define WIFI_MAX_SCAN 5
String wifiNames[WIFI_MAX_SCAN];
int wifiRSSI[WIFI_MAX_SCAN];
int wifiCount = 0;

// Selected SSID + password input
String selectedSSID = "";
String inputPassword = "";
bool shiftOn = false;

// Keyboard layout
const char* kbRow0 = "1234567890";
const char* kbRow1 = "qwertyuiop";
const char* kbRow2 = "asdfghjkl";
const char* kbRow3 = "zxcvbnm";

const int KB_Y0 = 75;
const int KB_KH = 30;
const int KB_KW = 28;
const int KB_GAP = 2;

// Forward declarations
void drawMainScreen();
void drawMapleLeaf(int x, int y, int scale = 2);
void drawDropdownMenu();
void closeDropdownMenu();
void handleDropdownTouch(int tx, int ty);
void drawQRScreen(bool isLocal);
void drawInfoScreen();
void handleQRTouch(int tx, int ty);
void handleInfoTouch(int tx, int ty);
void drawVacuumBtn();
void drawDompeurCard();
void drawTempCard();
void drawTrendGraph();
void drawBasinCards();

// ---- MQTT ----
void publishState() {
  if (mqtt.connected()) {
    mqtt.publish(mqttTopicState.c_str(), lightOn ? "1" : "0", true);
    mqtt.publish(mqttTopicDompeur.c_str(), dompeurTime.c_str(), true);
    mqtt.publish(mqttTopicTemp.c_str(), String(temperature, 1).c_str(), true);
    mqtt.publish(mqttTopicBasin1.c_str(), String(basin1).c_str(), true);
    mqtt.publish(mqttTopicBasin2.c_str(), String(basin2).c_str(), true);
    mqtt.publish(mqttTopicBasin3.c_str(), String(basin3).c_str(), true);
  }
}

void mqttCallback(char* topic, byte* payload, unsigned int length) {
  String msg;
  for (unsigned int i = 0; i < length; i++) msg += (char)payload[i];
  Serial.printf("MQTT recv: %s = %s\n", topic, msg.c_str());

  if (String(topic) == mqttTopicCmd) {
    if (msg == "toggle") {
      lightOn = !lightOn;
      if (currentScreen == SCREEN_MAIN && !menuOpen) drawVacuumBtn();
      publishState();
      Serial.printf(">>> MQTT: Vacuum %s\n", lightOn ? "ON" : "OFF");
    } else if (msg == "on") {
      lightOn = true;
      if (currentScreen == SCREEN_MAIN && !menuOpen) drawVacuumBtn();
      publishState();
    } else if (msg == "off") {
      lightOn = false;
      if (currentScreen == SCREEN_MAIN && !menuOpen) drawVacuumBtn();
      publishState();
    }
  }
}

void mqttConnect() {
  if (WiFi.status() != WL_CONNECTED) return;
  if (mqtt.connected()) return;

  // Rate limit reconnect attempts
  if (millis() - lastMqttRetry < 5000) return;
  lastMqttRetry = millis();

  String clientId = "cyd-" + deviceId + "-" + String(random(1000));
  Serial.printf("MQTT: connexion a %s...\n", MQTT_BROKER);

  if (mqtt.connect(clientId.c_str())) {
    Serial.println("MQTT: connecte!");
    mqtt.subscribe(mqttTopicCmd.c_str());
    publishState();
  } else {
    Serial.printf("MQTT: echec (rc=%d)\n", mqtt.state());
  }
}

// ---- Touch ----
// XPT2046 commands: 0xD0 = read X position, 0x90 = read Y position
uint16_t touchReadChannel(uint8_t cmd) {
  touchSPI.transfer(cmd);
  uint8_t hi = touchSPI.transfer(0);
  uint8_t lo = touchSPI.transfer(0);
  return ((uint16_t)hi << 8 | lo) >> 3;
}

bool readTouch(int &sx, int &sy) {
  if (digitalRead(T_IRQ) == HIGH) return false;

  touchSPI.beginTransaction(SPISettings(1000000, MSBFIRST, SPI_MODE0));
  digitalWrite(T_CS, LOW);

  int32_t sumX = 0, sumY = 0;
  int valid = 0;

  for (int i = 0; i < 4; i++) {
    uint16_t rawX = touchReadChannel(0xD0);
    uint16_t rawY = touchReadChannel(0x90);
    if (rawX > 100 && rawX < 4000 && rawY > 100 && rawY < 4000) {
      sumX += rawX;
      sumY += rawY;
      valid++;
    }
  }

  touchSPI.transfer(0x00);
  digitalWrite(T_CS, HIGH);
  touchSPI.endTransaction();

  if (valid == 0) return false;

  uint16_t avgX = sumX / valid;
  uint16_t avgY = sumY / valid;

  // Map raw touch to screen (landscape: axes swapped)
  sx = map(avgY, 100, 3700, 0, SW);
  sy = map(avgX, 300, 3900, 0, SH);
  sx = constrain(sx, 0, SW - 1);
  sy = constrain(sy, 0, SH - 1);
  return true;
}

// ---- Drawing: Professional Dashboard ----
void drawMenuIcon() {
  for (int i = 0; i < 3; i++) {
    tft.fillRect(294, 5 + i * 5, 16, 2, C_TXT_GRAY);
  }
}

void drawSectionDiv(int y, const char* txt) {
  tft.setTextFont(1); tft.setTextSize(1);
  tft.setTextDatum(ML_DATUM);
  tft.setTextColor(C_TXT_GRAY, C_BG);
  tft.drawString(txt, 6, y + 4);
  int tw = tft.textWidth(txt) + 12;
  tft.drawFastHLine(tw, y + 4, SW - tw - 6, C_BORDER);
}

void drawHeader() {
  tft.fillRect(0, 0, SW, 22, C_HEADER);
  tft.fillRect(0, 22, SW, 2, C_AMBER);
  // Amber maple leaf box
  tft.fillRoundRect(4, 2, 18, 18, 3, C_AMBER);
  drawMapleLeaf(5, 3, 1);
  // Title
  tft.setTextFont(1); tft.setTextSize(1);
  tft.setTextDatum(TL_DATUM);
  tft.setTextColor(C_TXT, C_HEADER);
  tft.drawString("CABANE MARCOUX", 26, 3);
  tft.setTextColor(C_TXT_GRAY, C_HEADER);
  tft.drawString("SYSTEME DE CONTROLE", 26, 13);
  // Menu icon (right side)
  drawMenuIcon();
  // WiFi dot
  uint16_t wc = (WiFi.status() == WL_CONNECTED) ? C_GREEN : C_RED;
  tft.fillCircle(316, 11, 3, wc);
}

void drawDompeurCard() {
  int cx = 4, cy = 34, cw = 154, ch = 34;
  tft.fillRect(cx, cy, cw, 2, C_AMBER);
  tft.fillRoundRect(cx, cy + 2, cw, ch - 2, 4, C_CARD);
  tft.drawRoundRect(cx, cy + 2, cw, ch - 2, 4, C_BORDER);
  tft.setTextFont(1); tft.setTextSize(1);
  tft.setTextDatum(TL_DATUM);
  tft.setTextColor(C_TXT_GRAY, C_CARD);
  tft.drawString("DOMPEUR", cx + 8, cy + 5);
  tft.setTextSize(2);
  tft.setTextDatum(MC_DATUM);
  tft.setTextColor(C_AMBER, C_CARD);
  tft.drawString(dompeurTime.c_str(), cx + cw / 2, cy + 24);
}

void drawTempCard() {
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
}

// ---- Trend Graph ----
void drawTrendGraph() {
  int gx = 4, gy = 78, gw = SW - 8, gh = 44;
  tft.fillRect(gx, gy, 2, gh, C_BLUE);
  tft.fillRoundRect(gx + 2, gy, gw - 2, gh, 4, C_CARD);
  tft.drawRoundRect(gx + 2, gy, gw - 2, gh, 4, C_BORDER);
  tft.setTextFont(1); tft.setTextSize(1);
  tft.setTextDatum(TL_DATUM);
  tft.setTextColor(C_TXT_GRAY, C_CARD);
  tft.drawString("Tendance", gx + 8, gy + 3);

  if (graphCount < 2) {
    tft.setTextDatum(MC_DATUM);
    tft.setTextColor(tft.color565(80, 80, 80), C_CARD);
    tft.drawString("En attente de donnees...", gx + gw / 2, gy + gh / 2 + 4);
    return;
  }

  // Chart area (leave room for title and Y labels)
  int cx = gx + 28, cy2 = gy + 14, cw = gw - 34, ch = gh - 18;

  // Find min/max
  int minV = dompeurHist[0], maxV = dompeurHist[0];
  for (int i = 1; i < graphCount; i++) {
    if (dompeurHist[i] < minV) minV = dompeurHist[i];
    if (dompeurHist[i] > maxV) maxV = dompeurHist[i];
  }
  int range = maxV - minV;
  if (range < 10) {
    int expand = (10 - range + 1) / 2;
    maxV += expand;
    minV = (minV - expand > 0) ? minV - expand : 0;
    range = maxV - minV;
  }

  // Grid lines (3 horizontal)
  for (int i = 0; i <= 2; i++) {
    int y = cy2 + ch * i / 2;
    for (int x = cx; x < cx + cw; x += 4) {
      tft.drawPixel(x, y, C_BORDER);
    }
  }

  // Y-axis labels
  tft.setTextSize(1);
  tft.setTextDatum(MR_DATUM);
  tft.setTextColor(tft.color565(80, 80, 100), C_CARD);
  tft.drawString(String(maxV), cx - 2, cy2);
  tft.drawString(String(minV), cx - 2, cy2 + ch);

  // Draw line
  int n = graphCount;
  for (int i = 1; i < n; i++) {
    int x1 = cx + (long)(i - 1) * cw / (n - 1);
    int y1 = cy2 + ch - (long)(dompeurHist[i - 1] - minV) * ch / range;
    int x2 = cx + (long)i * cw / (n - 1);
    int y2 = cy2 + ch - (long)(dompeurHist[i] - minV) * ch / range;
    // Color: green if going down, red if going up
    uint16_t lc = (dompeurHist[i] <= dompeurHist[i - 1]) ? C_GREEN : C_RED;
    tft.drawLine(x1, y1, x2, y2, lc);
    tft.drawLine(x1, y1 + 1, x2, y2 + 1, lc); // thicker
  }

  // Trend arrow (last vs first)
  bool up = dompeurHist[n - 1] > dompeurHist[0];
  uint16_t arrowC = up ? C_RED : C_GREEN;
  int ax = gx + gw - 16, ay = gy + 3;
  if (up) { // arrow up = bad (time increasing)
    tft.fillTriangle(ax, ay + 2, ax - 4, ay + 8, ax + 4, ay + 8, arrowC);
  } else { // arrow down = good
    tft.fillTriangle(ax, ay + 8, ax - 4, ay + 2, ax + 4, ay + 2, arrowC);
  }
}

// ---- Basins (horizontal bars) ----
void drawBasinBar(int y, const char* name, int level) {
  int nameX = 10, barX = 62, barW = 210, barH = 14;
  // Name
  tft.setTextFont(1); tft.setTextSize(1);
  tft.setTextDatum(ML_DATUM);
  tft.setTextColor(C_LABEL, C_CARD);
  tft.drawString(name, nameX, y + 9);
  // Bar wrapper
  tft.fillRect(barX, y + 2, barW, barH, C_BG);
  tft.drawRect(barX, y + 2, barW, barH, C_BORDER);
  // Fill
  int fillW = (barW - 2) * level / 100;
  if (fillW > 0) {
    uint16_t bc = C_GREEN;
    if (level >= 50) bc = C_RED;
    else if (level >= 25) bc = C_AMBER;
    tft.fillRect(barX + 1, y + 3, fillW, barH - 2, bc);
  }
  // Percentage
  tft.setTextDatum(MR_DATUM);
  tft.setTextColor(C_TXT_DIM, C_CARD);
  String pct = String(level) + "%";
  tft.drawString(pct.c_str(), SW - 10, y + 9);
}

void drawBasinCards() {
  int cy = 132, ch = 64;
  tft.fillRoundRect(4, cy, SW - 8, ch, 4, C_CARD);
  tft.drawRoundRect(4, cy, SW - 8, ch, 4, C_BORDER);
  drawBasinBar(cy + 2, "BASSIN 1", basin1);
  drawBasinBar(cy + 22, "BASSIN 2", basin2);
  drawBasinBar(cy + 42, "BASSIN 3", basin3);
}

void drawVacuumBtn() {
  int sx = 4, sy = 204, sw = SW - 8, sh = 22;
  int hdlW = 36, hdlH = 18;
  // Track
  uint16_t brd = lightOn ? C_GREEN : C_BORDER;
  tft.fillRoundRect(sx, sy, sw, sh, 4, C_BG);
  tft.drawRoundRect(sx, sy, sw, sh, 4, brd);
  // Handle
  int hx = lightOn ? (sx + sw - hdlW - 2) : (sx + 2);
  int hy = sy + (sh - hdlH) / 2;
  tft.fillRoundRect(hx, hy, hdlW, hdlH, 3, C_HDL_BG);
  tft.drawRoundRect(hx, hy, hdlW, hdlH, 3, C_HDL_BD);
  // Lightning bolt "Z" on handle
  tft.setTextFont(1); tft.setTextSize(1);
  tft.setTextDatum(MC_DATUM);
  tft.setTextColor(C_AMBER, C_HDL_BG);
  tft.drawString("Z", hx + hdlW / 2, hy + hdlH / 2);
  // Hint text
  tft.setTextSize(1);
  if (!lightOn) {
    tft.setTextDatum(ML_DATUM);
    tft.setTextColor(tft.color565(180, 50, 50), C_BG);
    tft.drawString("> VACUUM ON", sx + hdlW + 10, sy + sh / 2);
  } else {
    tft.setTextDatum(MR_DATUM);
    tft.setTextColor(C_GREEN, C_BG);
    tft.drawString("VACUUM OFF <", sx + sw - hdlW - 10, sy + sh / 2);
  }
}

void drawStatusBar() {
  int sy = 228;
  tft.fillRoundRect(4, sy, SW - 8, 12, 3, C_SB_BG);
  tft.drawRoundRect(4, sy, SW - 8, 12, 3, C_BORDER);
  tft.setTextFont(1); tft.setTextSize(1);
  tft.setTextDatum(ML_DATUM);
  if (WiFi.status() == WL_CONNECTED) {
    tft.fillCircle(12, sy + 6, 2, C_GREEN);
    tft.setTextColor(C_TXT_DIM, C_SB_BG);
    tft.drawString(WiFi.localIP().toString().c_str(), 18, sy + 6);
  } else {
    tft.fillCircle(12, sy + 6, 2, C_RED);
    tft.setTextColor(C_TXT_DIM, C_SB_BG);
    tft.drawString("Deconnecte", 18, sy + 6);
  }
  tft.setTextDatum(MR_DATUM);
  tft.setTextColor(C_TXT_DIM, C_SB_BG);
  String idStr = "ID: " + deviceId;
  tft.drawString(idStr.c_str(), SW - 10, sy + 6);
}

void updateDompeurTime(String newTime) {
  dompeurTime = newTime;
  // Parse mm:ss to seconds and add to graph
  int colonIdx = newTime.indexOf(':');
  if (colonIdx > 0) {
    int mins = newTime.substring(0, colonIdx).toInt();
    int secs = newTime.substring(colonIdx + 1).toInt();
    addDompeurPoint(mins * 60 + secs);
  }
  if (mqtt.connected()) {
    mqtt.publish(mqttTopicDompeur.c_str(), dompeurTime.c_str(), true);
  }
  if (currentScreen == SCREEN_MAIN && !menuOpen) {
    drawDompeurCard();
    drawTrendGraph();
  }
}

void drawMainScreen() {
  tft.fillScreen(C_BG);
  drawHeader();
  drawSectionDiv(24, "MESURES TEMPS REEL");
  drawDompeurCard();
  drawTempCard();
  drawSectionDiv(70, "TENDANCE DOMPEUR");
  drawTrendGraph();
  drawSectionDiv(124, "NIVEAU DES BASSINS");
  drawBasinCards();
  drawSectionDiv(198, "CONTROLE VACUUM");
  drawVacuumBtn();
  drawStatusBar();
}

// ---- Drawing: WiFi list screen ----
void drawWifiListScreen() {
  tft.fillScreen(TFT_BLACK);
  tft.setTextFont(1);
  tft.setTextSize(2);
  tft.setTextDatum(MC_DATUM);
  tft.setTextColor(TFT_YELLOW, TFT_BLACK);
  tft.drawString("Scan WiFi...", SW / 2, SH / 2);

  int n = WiFi.scanNetworks();
  wifiCount = (n > WIFI_MAX_SCAN) ? WIFI_MAX_SCAN : n;
  for (int i = 0; i < wifiCount; i++) {
    wifiNames[i] = WiFi.SSID(i);
    wifiRSSI[i] = WiFi.RSSI(i);
  }
  WiFi.scanDelete();

  Serial.printf("Scan: %d reseaux\n", wifiCount);

  tft.fillScreen(TFT_BLACK);

  // Title bar
  uint16_t titleBg = tft.color565(0, 60, 120);
  tft.fillRect(0, 0, SW, 28, titleBg);
  tft.setTextFont(1);
  tft.setTextSize(2);
  tft.setTextDatum(MC_DATUM);
  tft.setTextColor(TFT_WHITE, titleBg);
  tft.drawString("Reseaux WiFi", SW / 2, 14);

  // Draw networks
  for (int i = 0; i < wifiCount; i++) {
    int y = 34 + i * 34;
    uint16_t rowBg = (i % 2 == 0) ? tft.color565(20, 20, 40) : TFT_BLACK;
    tft.fillRect(0, y, SW, 32, rowBg);

    // Signal bars
    int bars = 1;
    if (wifiRSSI[i] > -50) bars = 4;
    else if (wifiRSSI[i] > -60) bars = 3;
    else if (wifiRSSI[i] > -70) bars = 2;

    for (int b = 0; b < bars; b++) {
      int bh = 6 + b * 5;
      tft.fillRect(6 + b * 7, y + 26 - bh, 4, bh, TFT_GREEN);
    }

    // SSID name
    tft.setTextFont(1);
    tft.setTextSize(2);
    tft.setTextDatum(ML_DATUM);
    tft.setTextColor(TFT_WHITE, rowBg);
    tft.drawString(wifiNames[i].substring(0, 18).c_str(), 38, y + 16);
  }

  if (wifiCount == 0) {
    tft.setTextFont(1);
    tft.setTextSize(2);
    tft.setTextDatum(MC_DATUM);
    tft.setTextColor(TFT_RED, TFT_BLACK);
    tft.drawString("Aucun reseau", SW / 2, SH / 2);
  }

  // Back button
  uint16_t btnBg = tft.color565(80, 80, 80);
  tft.fillRoundRect(SW / 2 - 60, SH - 34, 120, 30, 5, btnBg);
  tft.setTextFont(1);
  tft.setTextSize(2);
  tft.setTextDatum(MC_DATUM);
  tft.setTextColor(TFT_WHITE, btnBg);
  tft.drawString("Retour", SW / 2, SH - 19);
}

// ---- Drawing: Keyboard screen ----
void drawKeyRow(const char* row, int rowLen, int y, int xOffset) {
  uint16_t keyBg = tft.color565(50, 50, 70);
  for (int i = 0; i < rowLen; i++) {
    int x = xOffset + i * (KB_KW + KB_GAP);
    tft.fillRoundRect(x, y, KB_KW, KB_KH - 2, 3, keyBg);
    tft.drawRoundRect(x, y, KB_KW, KB_KH - 2, 3, tft.color565(100, 100, 120));

    char c = row[i];
    if (shiftOn && c >= 'a' && c <= 'z') c -= 32;
    char buf[2] = { c, 0 };

    tft.setTextColor(TFT_WHITE, keyBg);
    tft.setTextSize(1);
    tft.setTextDatum(MC_DATUM);
    tft.drawString(buf, x + KB_KW / 2, y + (KB_KH - 2) / 2);
  }
}

void drawPasswordField() {
  uint16_t fieldBg = tft.color565(30, 30, 50);
  tft.fillRect(5, 40, SW - 10, 22, fieldBg);
  tft.drawRect(5, 40, SW - 10, 22, TFT_WHITE);

  tft.setTextColor(TFT_WHITE, fieldBg);
  tft.setTextSize(1);
  tft.setTextDatum(ML_DATUM);
  String display = inputPassword;
  if (display.length() > 35) display = ".." + display.substring(display.length() - 33);
  tft.drawString(display.c_str(), 10, 51);

  int curX = 10 + display.length() * 6;
  if (curX < SW - 15) {
    tft.fillRect(curX, 44, 2, 14, TFT_WHITE);
  }
}

void drawKeyboardScreen() {
  tft.fillScreen(TFT_BLACK);

  uint16_t kbTitleBg = tft.color565(0, 60, 120);
  tft.fillRect(0, 0, SW, 18, kbTitleBg);
  tft.setTextColor(TFT_WHITE, kbTitleBg);
  tft.setTextSize(1);
  tft.setTextDatum(ML_DATUM);
  String title = "WiFi: " + selectedSSID;
  if (title.length() > 40) title = title.substring(0, 40) + "..";
  tft.drawString(title.c_str(), 5, 9);

  tft.setTextColor(TFT_CYAN, TFT_BLACK);
  tft.setTextDatum(ML_DATUM);
  tft.drawString("Mot de passe:", 5, 30);

  drawPasswordField();

  int row0Len = strlen(kbRow0);
  int row1Len = strlen(kbRow1);
  int row2Len = strlen(kbRow2);
  int row3Len = strlen(kbRow3);

  int xOff0 = (SW - row0Len * (KB_KW + KB_GAP)) / 2;
  int xOff1 = (SW - row1Len * (KB_KW + KB_GAP)) / 2;
  int xOff2 = (SW - row2Len * (KB_KW + KB_GAP)) / 2;
  int xOff3 = (SW - row3Len * (KB_KW + KB_GAP)) / 2;

  drawKeyRow(kbRow0, row0Len, KB_Y0, xOff0);
  drawKeyRow(kbRow1, row1Len, KB_Y0 + KB_KH, xOff1);
  drawKeyRow(kbRow2, row2Len, KB_Y0 + KB_KH * 2, xOff2);
  drawKeyRow(kbRow3, row3Len, KB_Y0 + KB_KH * 3, xOff3);

  int by = KB_Y0 + KB_KH * 4 + 2;

  uint16_t majColor = shiftOn ? TFT_YELLOW : tft.color565(70, 70, 90);
  tft.fillRoundRect(5, by, 50, KB_KH - 2, 3, majColor);
  tft.setTextColor(shiftOn ? TFT_BLACK : TFT_WHITE, majColor);
  tft.setTextDatum(MC_DATUM);
  tft.drawString("MAJ", 30, by + (KB_KH - 2) / 2);

  uint16_t espBg = tft.color565(50, 50, 70);
  tft.fillRoundRect(60, by, 120, KB_KH - 2, 3, espBg);
  tft.setTextColor(TFT_WHITE, espBg);
  tft.drawString("ESPACE", 120, by + (KB_KH - 2) / 2);

  uint16_t bsBg = tft.color565(120, 50, 50);
  tft.fillRoundRect(185, by, 50, KB_KH - 2, 3, bsBg);
  tft.setTextColor(TFT_WHITE, bsBg);
  tft.drawString("<-", 210, by + (KB_KH - 2) / 2);

  uint16_t okBg = tft.color565(0, 140, 60);
  tft.fillRoundRect(240, by, 75, KB_KH - 2, 3, okBg);
  tft.setTextColor(TFT_WHITE, okBg);
  tft.drawString("OK", 277, by + (KB_KH - 2) / 2);
}

// ---- Touch handlers ----
char getKeyFromRow(const char* row, int rowLen, int xOffset, int ty, int rowY, int tx) {
  if (ty < rowY || ty > rowY + KB_KH) return 0;
  for (int i = 0; i < rowLen; i++) {
    int x = xOffset + i * (KB_KW + KB_GAP);
    if (tx >= x && tx <= x + KB_KW) {
      char c = row[i];
      if (shiftOn && c >= 'a' && c <= 'z') c -= 32;
      return c;
    }
  }
  return 0;
}

void handleKeyboardTouch(int tx, int ty) {
  int row0Len = strlen(kbRow0);
  int row1Len = strlen(kbRow1);
  int row2Len = strlen(kbRow2);
  int row3Len = strlen(kbRow3);

  int xOff0 = (SW - row0Len * (KB_KW + KB_GAP)) / 2;
  int xOff1 = (SW - row1Len * (KB_KW + KB_GAP)) / 2;
  int xOff2 = (SW - row2Len * (KB_KW + KB_GAP)) / 2;
  int xOff3 = (SW - row3Len * (KB_KW + KB_GAP)) / 2;

  char key = 0;
  if (!key) key = getKeyFromRow(kbRow0, row0Len, xOff0, ty, KB_Y0, tx);
  if (!key) key = getKeyFromRow(kbRow1, row1Len, xOff1, ty, KB_Y0 + KB_KH, tx);
  if (!key) key = getKeyFromRow(kbRow2, row2Len, xOff2, ty, KB_Y0 + KB_KH * 2, tx);
  if (!key) key = getKeyFromRow(kbRow3, row3Len, xOff3, ty, KB_Y0 + KB_KH * 3, tx);

  if (key) {
    if (inputPassword.length() < 64) {
      inputPassword += key;
      drawPasswordField();
    }
    return;
  }

  int by = KB_Y0 + KB_KH * 4 + 2;
  if (ty >= by && ty <= by + KB_KH) {
    if (tx >= 5 && tx <= 55) {
      shiftOn = !shiftOn;
      drawKeyboardScreen();
      return;
    }
    if (tx >= 60 && tx <= 180) {
      if (inputPassword.length() < 64) {
        inputPassword += ' ';
        drawPasswordField();
      }
      return;
    }
    if (tx >= 185 && tx <= 235) {
      if (inputPassword.length() > 0) {
        inputPassword.remove(inputPassword.length() - 1);
        drawPasswordField();
      }
      return;
    }
    // Bouton OK: lancer connexion WiFi non-bloquante
    if (tx >= 240 && tx <= 315) {
      tft.fillScreen(TFT_BLACK);
      tft.setTextColor(TFT_CYAN, TFT_BLACK);
      tft.setTextSize(2);
      tft.setTextDatum(MC_DATUM);
      tft.drawString("Connexion...", SW / 2, SH / 2 - 10);
      tft.setTextSize(1);
      tft.drawString(selectedSSID.c_str(), SW / 2, SH / 2 + 15);

      WiFi.disconnect();
      delay(100);
      WiFi.begin(selectedSSID.c_str(), inputPassword.c_str());
      wifiConnectStart = millis();
      currentScreen = SCREEN_WIFI_CONNECTING;
      return;
    }
  }
}

void handleWifiListTouch(int tx, int ty) {
  if (ty >= SH - 34 && tx >= SW / 2 - 60 && tx <= SW / 2 + 60) {
    currentScreen = SCREEN_MAIN;
    drawMainScreen();
    return;
  }

  for (int i = 0; i < wifiCount; i++) {
    int ny = 34 + i * 34;
    if (ty >= ny && ty < ny + 32) {
      selectedSSID = wifiNames[i];
      inputPassword = "";
      shiftOn = false;
      currentScreen = SCREEN_WIFI_PASS;
      drawKeyboardScreen();
      return;
    }
  }
}

void handleMainTouch(int tx, int ty) {
  // Si le menu deroulant est ouvert, deleguer
  if (menuOpen) {
    handleDropdownTouch(tx, ty);
    return;
  }
  // Menu icon (top-right)
  if (tx >= 280 && ty <= 24) {
    drawDropdownMenu();
    return;
  }
  // Vacuum slider (full width)
  if (ty >= 204 && ty <= 226) {
    lightOn = !lightOn;
    drawVacuumBtn();
    publishState();
    Serial.printf(">>> Touch: Vacuum %s\n", lightOn ? "ON" : "OFF");
  }
}

// ---- Dropdown Menu ----
void drawDropdownMenu() {
  menuOpen = true;
  // Fond du menu
  tft.fillRect(MENU_X, MENU_Y, MENU_W, MENU_H, C_CARD);
  tft.drawRect(MENU_X, MENU_Y, MENU_W, MENU_H, C_AMBER);

  for (int i = 0; i < MENU_ITEMS; i++) {
    int itemY = MENU_Y + 1 + i * MENU_ITEM_H;
    // Separateur
    if (i > 0) {
      tft.drawFastHLine(MENU_X + 4, itemY, MENU_W - 8, C_BORDER);
    }
    // Texte grise si QR Local sans WiFi
    uint16_t textColor = TFT_WHITE;
    if (i == 1 && WiFi.status() != WL_CONNECTED) {
      textColor = tft.color565(80, 80, 80);
    }
    tft.setTextFont(1);
    tft.setTextSize(2);
    tft.setTextDatum(ML_DATUM);
    tft.setTextColor(textColor, C_CARD);
    tft.drawString(menuLabels[i], MENU_X + 10, itemY + MENU_ITEM_H / 2);
  }
}

void closeDropdownMenu() {
  menuOpen = false;
  drawMainScreen();
}

void handleDropdownTouch(int tx, int ty) {
  // Touch dans le menu?
  if (tx >= MENU_X && tx <= MENU_X + MENU_W &&
      ty >= MENU_Y && ty <= MENU_Y + MENU_H) {
    int idx = (ty - MENU_Y - 1) / MENU_ITEM_H;
    if (idx < 0) idx = 0;
    if (idx >= MENU_ITEMS) idx = MENU_ITEMS - 1;

    switch (idx) {
      case 0: // WiFi
        menuOpen = false;
        currentScreen = SCREEN_WIFI_LIST;
        drawWifiListScreen();
        break;
      case 1: // QR Local
        if (WiFi.status() == WL_CONNECTED) {
          menuOpen = false;
          currentScreen = SCREEN_QR_LOCAL;
          drawQRScreen(true);
        }
        break;
      case 2: // QR Remote
        menuOpen = false;
        currentScreen = SCREEN_QR_REMOTE;
        drawQRScreen(false);
        break;
      case 3: // Infos
        menuOpen = false;
        currentScreen = SCREEN_INFO;
        drawInfoScreen();
        break;
    }
  } else {
    // Tap hors du menu -> fermer
    closeDropdownMenu();
  }
}

// ---- QR Code Screen ----
void drawQRScreen(bool isLocal) {
  tft.fillScreen(C_BG);

  // Header
  tft.fillRect(0, 0, SW, 22, C_HEADER);
  tft.fillRect(0, 22, SW, 2, C_AMBER);
  tft.setTextFont(1);
  tft.setTextSize(2);
  tft.setTextDatum(MC_DATUM);
  tft.setTextColor(C_TXT, C_HEADER);
  tft.drawString(isLocal ? "QR Local" : "QR Remote", SW / 2, 11);

  // Construire l URL
  String url;
  if (isLocal) {
    url = "http://" + WiFi.localIP().toString() + "/remote";
  } else {
    url = "https://robingag.github.io/cabane-marcoux/?id=" + deviceId;
  }

  // Afficher l URL en petit
  tft.setTextSize(1);
  tft.setTextDatum(TC_DATUM);
  tft.setTextColor(C_AMBER, C_BG);
  String displayUrl = url;
  if (displayUrl.length() > 50) displayUrl = displayUrl.substring(0, 47) + "...";
  tft.drawString(displayUrl.c_str(), SW / 2, 32);

  // Generer le QR code (version 3: 29x29, capacite 77 bytes ECC_LOW)
  QRCode qrcode;
  uint8_t qrcodeData[qrcode_getBufferSize(3)];
  qrcode_initText(&qrcode, qrcodeData, 3, ECC_LOW, url.c_str());

  // Pixels plus gros pour meilleure lisibilite
  int pixelSize = 4;
  int qrW = qrcode.size * pixelSize;
  int qrX = (SW - qrW) / 2;
  int qrY = 44;

  // Grande zone blanche (quiet zone) pour scanner facilement
  int pad = pixelSize * 4;  // 4 modules de marge = standard QR
  tft.fillRect(qrX - pad, qrY - pad, qrW + pad * 2, qrW + pad * 2, TFT_WHITE);

  // Dessiner les modules
  for (uint8_t y = 0; y < qrcode.size; y++) {
    for (uint8_t x = 0; x < qrcode.size; x++) {
      if (qrcode_getModule(&qrcode, x, y)) {
        tft.fillRect(qrX + x * pixelSize, qrY + y * pixelSize,
                     pixelSize, pixelSize, TFT_BLACK);
      }
    }
  }

  // Instruction
  tft.setTextSize(1);
  tft.setTextDatum(TC_DATUM);
  tft.setTextColor(tft.color565(120, 120, 120), C_BG);
  tft.drawString("Scannez avec votre telephone", SW / 2, qrY + qrW + pad + 4);

  // Bouton Retour
  uint16_t btnBg = tft.color565(80, 80, 80);
  tft.fillRoundRect(SW / 2 - 60, SH - 36, 120, 30, 5, btnBg);
  tft.setTextSize(2);
  tft.setTextDatum(MC_DATUM);
  tft.setTextColor(TFT_WHITE, btnBg);
  tft.drawString("Retour", SW / 2, SH - 21);
}

void handleQRTouch(int tx, int ty) {
  if (ty >= SH - 36 && tx >= SW / 2 - 60 && tx <= SW / 2 + 60) {
    currentScreen = SCREEN_MAIN;
    drawMainScreen();
  }
}

// ---- Info Screen ----
void drawInfoScreen() {
  tft.fillScreen(C_BG);

  // Header
  tft.fillRect(0, 0, SW, 22, C_HEADER);
  tft.fillRect(0, 22, SW, 2, C_AMBER);
  tft.setTextFont(1);
  tft.setTextSize(2);
  tft.setTextDatum(MC_DATUM);
  tft.setTextColor(C_TXT, C_HEADER);
  tft.drawString("Informations", SW / 2, 11);

  // Donnees
  String ipStr = (WiFi.status() == WL_CONNECTED)
                 ? WiFi.localIP().toString() : "Non connecte";
  String mqttStr = mqtt.connected() ? "Connecte" : "Deconnecte";
  String rssiStr = (WiFi.status() == WL_CONNECTED)
                   ? String(WiFi.RSSI()) + " dBm" : "N/A";
  String heapStr = String(ESP.getFreeHeap()) + " oct";

  unsigned long sec = millis() / 1000;
  char uptimeBuf[20];
  snprintf(uptimeBuf, sizeof(uptimeBuf), "%luh %02lum %02lus",
           sec / 3600, (sec % 3600) / 60, sec % 60);

  const char* labels[] = { "Adresse IP", "Device ID", "MQTT Status",
                           "MQTT Broker", "WiFi RSSI", "Heap libre", "Uptime" };
  String values[] = { ipStr, deviceId, mqttStr,
                      String(MQTT_BROKER), rssiStr, heapStr, String(uptimeBuf) };

  int startY = 36;
  int rowH = 22;
  for (int i = 0; i < 7; i++) {
    int y = startY + i * rowH;
    tft.setTextFont(1);
    tft.setTextSize(1);
    tft.setTextDatum(ML_DATUM);
    tft.setTextColor(C_AMBER, C_BG);
    tft.drawString(labels[i], 10, y + 6);
    tft.setTextDatum(MR_DATUM);
    tft.setTextColor(TFT_WHITE, C_BG);
    tft.drawString(values[i].c_str(), SW - 10, y + 6);
    if (i < 6) {
      tft.drawFastHLine(6, y + rowH - 1, SW - 12, C_BORDER);
    }
  }

  // Bouton Retour
  uint16_t btnBg = tft.color565(80, 80, 80);
  tft.fillRoundRect(SW / 2 - 60, SH - 36, 120, 30, 5, btnBg);
  tft.setTextSize(2);
  tft.setTextDatum(MC_DATUM);
  tft.setTextColor(TFT_WHITE, btnBg);
  tft.drawString("Retour", SW / 2, SH - 21);
}

void handleInfoTouch(int tx, int ty) {
  if (ty >= SH - 36 && tx >= SW / 2 - 60 && tx <= SW / 2 + 60) {
    currentScreen = SCREEN_MAIN;
    drawMainScreen();
  }
}

// ---- Web page (local) ----
const char WEBPAGE[] PROGMEM = R"rawliteral(
<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>CYD Lumiere</title>
<style>
  * { margin:0; padding:0; box-sizing:border-box; }
  body {
    font-family: Arial, sans-serif;
    background: #1a1a2e;
    color: white;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    height: 100vh;
    user-select: none;
  }
  h2 { margin-bottom: 30px; font-size: 18px; color: #aaa; }
  .light {
    width: 150px; height: 150px;
    border-radius: 50%;
    background: #333;
    border: 4px solid #555;
    margin-bottom: 40px;
    transition: all 0.3s ease;
  }
  .light.on {
    background: #ffdd00;
    box-shadow: 0 0 60px #ffdd00, 0 0 120px #ffaa00;
    border-color: #ffaa00;
  }
  .btn {
    padding: 18px 50px;
    font-size: 22px;
    font-weight: bold;
    border: none;
    border-radius: 12px;
    color: white;
    cursor: pointer;
    transition: all 0.2s;
    min-width: 160px;
  }
  .btn.off { background: #0078d7; }
  .btn.off:active { background: #005a9e; }
  .btn.on { background: #e94560; }
  .btn.on:active { background: #c73650; }
  .status {
    margin-top: 20px;
    font-size: 12px;
    color: #666;
  }
</style>
</head>
<body>
  <h2>CYD Controleur (Local)</h2>
  <div class="light" id="light"></div>
  <button class="btn off" id="btn" onclick="toggle()">ON</button>
  <div class="status" id="status">Connecte</div>
<script>
  let state = false;
  function updateUI(on) {
    state = on;
    const light = document.getElementById('light');
    const btn = document.getElementById('btn');
    if (on) {
      light.classList.add('on');
      btn.textContent = 'OFF';
      btn.className = 'btn on';
    } else {
      light.classList.remove('on');
      btn.textContent = 'ON';
      btn.className = 'btn off';
    }
  }
  function toggle() {
    fetch('/toggle').then(r => r.json()).then(d => updateUI(d.on));
  }
  setInterval(() => {
    fetch('/state').then(r => r.json()).then(d => updateUI(d.on));
  }, 500);
</script>
</body>
</html>
)rawliteral";

// MQTT Remote page (served by ESP32, works from anywhere via MQTT)
const char REMOTEPAGE[] PROGMEM = R"rawliteral(
<!DOCTYPE html>
<html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="apple-mobile-web-app-capable" content="yes"><meta name="theme-color" content="#0a0a1a">
<title>Cabane Marcoux</title><style>
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:Arial;background:#0a0a1a;color:#fff;user-select:none}
.hd{background:#0a3d7a;padding:12px 16px;display:flex;align-items:center;justify-content:space-between}
.hd h1{font-size:16px;letter-spacing:1px}
.dt{width:8px;height:8px;border-radius:50%;background:#f44}.dt.ok{background:#4f4}.dt.w{background:#ff4}
.w{max-width:460px;margin:0 auto;padding:10px}
.r{display:flex;gap:8px;margin-bottom:8px}
.cd{background:#1a1a2e;border:1px solid #2a2a4e;border-radius:8px;padding:12px;flex:1}
.cd .lb{font-size:10px;color:#888;text-transform:uppercase;letter-spacing:1px;margin-bottom:6px}
.cd .vl{font-family:monospace;font-size:24px;font-weight:700;text-align:center}
.cd.dm .vl{color:#0ff}.cd.tp .vl{color:#fd20}
.gc{background:#1a1a2e;border:1px solid #2a2a4e;border-radius:8px;padding:8px;margin-bottom:8px}
.gc .gl{font-size:10px;color:#0ff;text-transform:uppercase;letter-spacing:1px;margin-bottom:4px;display:flex;justify-content:space-between}
.gc .ar{font-size:14px;font-weight:700}.gc .ar.u{color:#f44}.gc .ar.d{color:#4f4}
.gc canvas{width:100%;height:90px;display:block;border-radius:4px}
.bc{background:#1a1a2e;border:1px solid #2a2a4e;border-radius:8px;padding:8px 12px;margin-bottom:8px}
.br{display:flex;align-items:center;gap:6px;margin-bottom:4px}.br:last-child{margin:0}
.br .nl{font-size:10px;color:#6bf;width:52px}.br .bw{flex:1;background:#111;border-radius:3px;height:8px;overflow:hidden}
.br .bf{height:100%;border-radius:3px;transition:width .5s}.bf.h{background:#4f4}.bf.m{background:#ff4}.bf.l{background:#f44}
.br .pc{font-family:monospace;font-size:12px;width:30px;text-align:right}
.vb{width:100%;padding:14px;border:none;border-radius:10px;font-size:18px;font-weight:700;color:#fff;cursor:pointer;margin-bottom:8px;display:flex;align-items:center;justify-content:center;gap:10px}
.vb.off{background:#0a6dd9}.vb.on{background:#e94560}.vb:disabled{background:#333}
.vd{width:12px;height:12px;border-radius:50%;border:2px solid #fff4}.vd.a{background:#4f4;box-shadow:0 0 8px #4f4}
.sb{background:#111;border-radius:6px;padding:6px 12px;display:flex;justify-content:space-between;font-size:11px;color:#666}
</style></head><body>
<div class="hd"><h1>CABANE MARCOUX</h1><div class="dt w" id="dt"></div></div>
<div class="w">
<div class="r"><div class="cd dm"><div class="lb">Dompeur</div><div class="vl" id="dmp">--:--</div></div><div class="cd tp"><div class="lb">Temperature</div><div class="vl" id="tmp">--.-°C</div></div></div>
<div class="gc"><div class="gl"><span>Tendance</span><span class="ar" id="ar"></span></div><canvas id="gr" height="90"></canvas></div>
<div class="bc"><div class="br"><span class="nl">Bassin 1</span><div class="bw"><div class="bf" id="bf1"></div></div><span class="pc" id="bp1">--%</span></div><div class="br"><span class="nl">Bassin 2</span><div class="bw"><div class="bf" id="bf2"></div></div><span class="pc" id="bp2">--%</span></div><div class="br"><span class="nl">Bassin 3</span><div class="bw"><div class="bf" id="bf3"></div></div><span class="pc" id="bp3">--%</span></div></div>
<button class="vb off" id="vb" onclick="tg()" disabled><span class="vd" id="vd"></span><span id="vt">VACUUM ON</span></button>
<div class="sb"><span id="st">Connexion...</span><span>ID: <span id="did">---</span></span></div>
</div>
<script src="https://cdnjs.cloudflare.com/ajax/libs/mqtt/5.3.5/mqtt.min.js"></script>
<script>
var c,id=new URLSearchParams(window.location.search).get("id")||"a48c",hist=[];
document.getElementById("did").textContent=id;
function sv(on){document.getElementById("vb").className="vb "+(on?"on":"off");document.getElementById("vd").className="vd"+(on?" a":"");document.getElementById("vt").textContent=on?"VACUUM OFF":"VACUUM ON"}
function sba(n,v){var l=parseInt(v)||0;var f=document.getElementById("bf"+n);f.style.width=l+"%";f.className="bf "+(l>=50?"h":l>=25?"m":"l");document.getElementById("bp"+n).textContent=l+"%"}
function dg(){var cv=document.getElementById("gr"),ctx=cv.getContext("2d"),dp=window.devicePixelRatio||1;cv.width=cv.offsetWidth*dp;cv.height=90*dp;ctx.scale(dp,dp);var W=cv.offsetWidth,H=90;ctx.clearRect(0,0,W,H);ctx.fillStyle="#111";ctx.fillRect(0,0,W,H);if(hist.length<2){ctx.fillStyle="#444";ctx.font="12px Arial";ctx.textAlign="center";ctx.fillText("En attente...",W/2,H/2+4);document.getElementById("ar").textContent="";return}var n=hist.length,mn=Math.min.apply(null,hist),mx=Math.max.apply(null,hist),rg=mx-mn;if(rg<10){mn-=5;mx+=5;rg=mx-mn}var p={l:30,r:8,t:6,b:14},cw=W-p.l-p.r,ch=H-p.t-p.b;ctx.strokeStyle="#2a2a4e";ctx.setLineDash([3,3]);for(var i=0;i<=2;i++){var y=p.t+ch*i/2;ctx.beginPath();ctx.moveTo(p.l,y);ctx.lineTo(p.l+cw,y);ctx.stroke()}ctx.setLineDash([]);ctx.fillStyle="#556";ctx.font="9px monospace";ctx.textAlign="right";ctx.fillText(mx+"s",p.l-3,p.t+7);ctx.fillText(mn+"s",p.l-3,p.t+ch+3);ctx.lineWidth=2;ctx.lineJoin="round";for(var i=1;i<n;i++){var x1=p.l+(i-1)*cw/(n-1),y1=p.t+ch-(hist[i-1]-mn)*ch/rg,x2=p.l+i*cw/(n-1),y2=p.t+ch-(hist[i]-mn)*ch/rg;ctx.strokeStyle=hist[i]<=hist[i-1]?"#4f4":"#f44";ctx.beginPath();ctx.moveTo(x1,y1);ctx.lineTo(x2,y2);ctx.stroke()}var a=document.getElementById("ar");if(hist[n-1]>hist[0]){a.textContent="\u25B2";a.className="ar u"}else{a.textContent="\u25BC";a.className="ar d"}}
function od(v){document.getElementById("dmp").textContent=v;var p=v.split(":");if(p.length===2){var s=parseInt(p[0])*60+parseInt(p[1]);if(s>0){hist.push(s);if(hist.length>30)hist.shift();dg()}}}
function ss(t,cl){document.getElementById("st").textContent=t;document.getElementById("dt").className="dt "+cl}
function tg(){if(c&&c.connected)c.publish("cyd/"+id+"/cmd","toggle")}
function go(){ss("Connexion...","w");var urls=["wss://broker.hivemq.com:8884/mqtt","ws://broker.hivemq.com:8000/mqtt"];var ui=0;function tc(){if(ui>=urls.length)ui=0;c=mqtt.connect(urls[ui],{clientId:"r-"+id+"-"+Math.random().toString(16).substr(2,4),clean:true,connectTimeout:8000,reconnectPeriod:0});c.on("connect",function(){ss("Connecte","ok");document.getElementById("vb").disabled=false;var p="cyd/"+id+"/";["state","dompeur","temp","basin1","basin2","basin3"].forEach(function(t){c.subscribe(p+t)})});c.on("message",function(tp,m){var v=m.toString(),p="cyd/"+id+"/";if(tp===p+"state")sv(v==="1");if(tp===p+"dompeur")od(v);if(tp===p+"temp")document.getElementById("tmp").innerHTML=v+"&deg;C";if(tp===p+"basin1")sba(1,v);if(tp===p+"basin2")sba(2,v);if(tp===p+"basin3")sba(3,v)});c.on("error",function(){ss("Essai...","w");c.end(true);ui++;setTimeout(tc,1000)});c.on("close",function(){ss("Deconnecte","er");document.getElementById("vb").disabled=true})}tc()}
go();dg();document.addEventListener("visibilitychange",function(){if(!document.hidden&&(!c||!c.connected))go()});
</script></body></html>
)rawliteral";

// ---- Web handlers ----
void handleRoot() {
  server.send(200, "text/html", WEBPAGE);
}

void handleRemote() {
  // Redirect to page with device ID as parameter
  String url = "/remote-app?id=" + deviceId;
  server.sendHeader("Location", url, true);
  server.send(302, "text/plain", "");
}

void handleRemoteApp() {
  server.send_P(200, "text/html", REMOTEPAGE);
}

void handleState() {
  String json = "{\"on\":" + String(lightOn ? "true" : "false") + "}";
  server.send(200, "application/json", json);
}

void handleToggle() {
  lightOn = !lightOn;
  if (currentScreen == SCREEN_MAIN) drawVacuumBtn();
  publishState();
  Serial.printf(">>> Web: Vacuum %s\n", lightOn ? "ON" : "OFF");
  String json = "{\"on\":" + String(lightOn ? "true" : "false") + "}";
  server.send(200, "application/json", json);
}

// ---- Setup ----
void setup() {
  Serial.begin(115200);
  delay(100);

  // Derive device ID from MAC address
  uint8_t mac[6];
  WiFi.macAddress(mac);
  // 6 hex = 3 bytes = 16M combinaisons (vs 4 hex = 65K avant)
  char idBuf[7];
  snprintf(idBuf, sizeof(idBuf), "%02x%02x%02x", mac[3], mac[4], mac[5]);
  deviceId = String(idBuf);
  mqttTopicState = "cyd/" + deviceId + "/state";
  mqttTopicCmd = "cyd/" + deviceId + "/cmd";
  mqttTopicDompeur = "cyd/" + deviceId + "/dompeur";
  mqttTopicTemp = "cyd/" + deviceId + "/temp";
  mqttTopicBasin1 = "cyd/" + deviceId + "/basin1";
  mqttTopicBasin2 = "cyd/" + deviceId + "/basin2";
  mqttTopicBasin3 = "cyd/" + deviceId + "/basin3";
  Serial.printf("Device ID: %s\n", deviceId.c_str());
  Serial.printf("MQTT topics: %s, %s\n", mqttTopicState.c_str(), mqttTopicCmd.c_str());

  // Touch SPI
  touchSPI.begin(T_CLK, T_DO, T_DIN, T_CS);
  pinMode(T_CS, OUTPUT);
  digitalWrite(T_CS, HIGH);
  pinMode(T_IRQ, INPUT);

  // Display
  tft.init();
  tft.setRotation(1);
  tft.fillScreen(TFT_BLACK);
  pinMode(TFT_BL, OUTPUT);
  digitalWrite(TFT_BL, HIGH);

  // MQTT setup
  mqtt.setServer(MQTT_BROKER, MQTT_PORT);
  mqtt.setCallback(mqttCallback);

  // Web server routes
  server.on("/", handleRoot);
  server.on("/remote", handleRemote);
  server.on("/remote-app", handleRemoteApp);
  server.on("/state", handleState);
  server.on("/toggle", handleToggle);

  // NVS
  String savedSSID = "";
  String savedPass = "";
  if (prefs.begin("wifi", false)) {
    savedSSID = prefs.getString("ssid", "");
    savedPass = prefs.getString("pass", "");
    prefs.end();
    Serial.printf("NVS: ssid='%s'\n", savedSSID.c_str());
  } else {
    Serial.println("NVS: init premiere fois");
    prefs.end();
  }

  Serial.println("Dessin ecran principal...");
  drawMainScreen();
  Serial.println("Ecran dessine!");

  // Auto-connect WiFi
  if (savedSSID.length() > 0) {
    WiFi.begin(savedSSID.c_str(), savedPass.c_str());
    Serial.printf("Connexion a %s", savedSSID.c_str());

    int tries = 0;
    while (WiFi.status() != WL_CONNECTED && tries < 20) {
      delay(500);
      Serial.print(".");
      tries++;
    }

    if (WiFi.status() == WL_CONNECTED) {
      Serial.printf("\nConnecte! IP: %s\n", WiFi.localIP().toString().c_str());
      server.begin();
      mqttConnect();
      drawMainScreen();  // Redraw to update WiFi indicator
    } else {
      Serial.println("\nEchec WiFi auto-connect");
    }

  }

  Serial.println("=== CYD Bouton + Lumiere + WiFi + MQTT ===");
}

// ---- Loop ----
bool wasTouched = false;

void loop() {
  if (WiFi.status() == WL_CONNECTED) {
    server.handleClient();

    // MQTT keep-alive and reconnect
    if (mqtt.connected()) {
      mqtt.loop();
    } else {
      mqttConnect();
    }
  }

  // Connexion WiFi non-bloquante (depuis ecran clavier)
  if (currentScreen == SCREEN_WIFI_CONNECTING) {
    if (WiFi.status() == WL_CONNECTED) {
      prefs.begin("wifi", false);
      prefs.putString("ssid", selectedSSID);
      prefs.putString("pass", inputPassword);
      prefs.end();

      Serial.printf("WiFi connecte! IP: %s\n", WiFi.localIP().toString().c_str());
      server.begin();
      mqttConnect();

      currentScreen = SCREEN_MAIN;
      drawMainScreen();
    } else if (millis() - wifiConnectStart > WIFI_CONNECT_TIMEOUT) {
      currentScreen = SCREEN_WIFI_FAIL;
      tft.fillScreen(TFT_BLACK);
      tft.setTextColor(TFT_RED, TFT_BLACK);
      tft.setTextSize(2);
      tft.setTextDatum(MC_DATUM);
      tft.drawString("Echec WiFi!", SW / 2, SH / 2 - 10);
      tft.setTextSize(1);
      tft.setTextColor(TFT_WHITE, TFT_BLACK);
      tft.drawString("Touche pour revenir", SW / 2, SH / 2 + 15);
    }
  }

  int sx, sy;
  bool touched = readTouch(sx, sy);

  if (touched && !wasTouched) {
    switch (currentScreen) {
      case SCREEN_MAIN:
        handleMainTouch(sx, sy);
        break;
      case SCREEN_WIFI_LIST:
        handleWifiListTouch(sx, sy);
        break;
      case SCREEN_WIFI_PASS:
        handleKeyboardTouch(sx, sy);
        break;
      case SCREEN_WIFI_FAIL:
        currentScreen = SCREEN_WIFI_PASS;
        drawKeyboardScreen();
        break;
      case SCREEN_QR_LOCAL:
      case SCREEN_QR_REMOTE:
        handleQRTouch(sx, sy);
        break;
      case SCREEN_INFO:
        handleInfoTouch(sx, sy);
        break;
      default:
        break;
    }
  }

  wasTouched = touched;
  delay(30);
}
