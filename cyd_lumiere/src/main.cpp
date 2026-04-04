#include <Arduino.h>
#include <SPI.h>
#include <TFT_eSPI.h>
#include <WiFi.h>
#include <WebServer.h>
#include <Preferences.h>
#include <PubSubClient.h>
#include <qrcode.h>
#include <NimBLEDevice.h>

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
String mqttTopicDompeurLive; // cyd/{id}/dompeur/live
String mqttTopicTemp;    // cyd/{id}/temp
String mqttTopicBasin1;  // cyd/{id}/basin1
String mqttTopicBasin2;  // cyd/{id}/basin2
String mqttTopicBasin3;  // cyd/{id}/basin3
String mqttTopicBasin4;  // cyd/{id}/basin4
String mqttTopicCal;     // cyd/{id}/cmd/cal
const char* MQTT_BROKER = "broker.hivemq.com";
const int MQTT_PORT = 1883;
unsigned long lastMqttRetry = 0;

// CYD XPT2046 touch pins (VSPI bus)
#define T_CLK  25
#define T_CS   33
#define T_DIN  32
#define T_DO   39
#define T_IRQ  36

// Limit switch for dompeur timing (GPIO 27, P3 connector)
// REMOVED: dompeur sensor moved to WROOM Hub
// #define LIMIT_SW_PIN 27

// JSN-SR04T ultrasonic sensor
// Bassin 1: 2-wire on GPIO 22 (CN1/P3 connector)
// JSN-SR04T ultrasonic sensor
// Bassin 1: 4-wire on GPIO 22 (Trig) + GPIO 35 (Echo) - P3 connector
// REMOVED: ultrasonic sensor moved to WROOM Hub
// #define US1_TRIG 22
// #define US1_ECHO 35

// Simulateur de pulses dompeur (P3 connecteur)
// REMOVED: simulator moved to WROOM Hub
// #define SIM_PULSE_PIN 1

// Display-only: dompeur data comes from MQTT/BLE
unsigned long lsLastEdge = 0;  // virtual edge time from Hub
// volatile unsigned long lsCycleMs = 0;  // REMOVED
// volatile bool lsNewCycle = false;  // REMOVED

// Simulation pulses: true=actif, false=capteur reel
// REMOVED: simPulse variables (Hub handles sensors)

// REMOVED: limitSwitchISR() - dompeur handled by WROOM Hub

SPIClass touchSPI(VSPI);

// Screen (landscape)
const int SW = 320;
const int SH = 240;

// Color palette (interface1 blue/cyan theme)
const uint16_t C_BG       = 0x0843;  // #0a0a1a deep dark
const uint16_t C_CARD     = 0x18C5;  // #1a1a2e dark card
const uint16_t C_BORDER   = 0x2949;  // #2a2a4e border
const uint16_t C_HEADER   = 0x09EF;  // #0a3d7a blue header
const uint16_t C_AMBER    = 0x07FF;  // #00ffff cyan (replaces amber)
const uint16_t C_CYAN     = 0x07FF;  // #00ffff cyan
const uint16_t C_GREEN    = 0x47E8;  // #44ff44 bright green
const uint16_t C_RED      = 0xFA28;  // #ff4444 bright red
const uint16_t C_YELLOW   = 0xFFE8;  // #ffff44 bright yellow
const uint16_t C_BLUE     = 0x65DF;  // #66bbff light blue
const uint16_t C_TXT      = 0xFFFF;  // #ffffff white text
const uint16_t C_TXT_GRAY = 0x8410;  // #808080 labels
const uint16_t C_TXT_DIM  = 0x632C;  // #666666 status
const uint16_t C_LABEL    = 0x65DF;  // #66bbff basin names (blue)
const uint16_t C_SB_BG    = 0x1082;  // #111111 status bar bg
const uint16_t C_HDL_BG   = 0x18C5;  // #1a1a2e handle bg
const uint16_t C_HDL_BD   = 0x2949;  // #2a2a4e handle border


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
#define VACUUM_PIN 4
// PIN reason: 0=calibration, 1=vacuum
int pinReason = 0;
const char* VACUUM_PIN_CODE = "777";

// Sensor data
String dompeurTime = "--:--";
bool dompeurReset = false;  // true = reset apres 30 min
#define DOMPEUR_ALERT_MS  (15UL * 60 * 1000)  // 15 min
#define DOMPEUR_RESET_MS  (30UL * 60 * 1000)  // 30 min
float temperature = 0.0;
float humidity = 0.0;
int bleBattery = -1;
unsigned long lastBleScan = 0;
const unsigned long BLE_SCAN_INTERVAL = 20000; // 20s entre scans // 30 sec
bool bleInitDone = false;
String mqttTopicHumidity;
int basin1 = 0;  // 0-100%
int basin2 = 0;
int basin3 = 0;
int basin4 = 0;
int rawBasin[4] = {0, 0, 0, 0};  // raw sensor values
int calLow[4]  = {-1, -1, -1, -1}; // calibration low points (-1 = not set)
int calHigh[4] = {-1, -1, -1, -1}; // calibration high points
// HTML-style calibration: refRaw (cm) + refInches (po)
int calRefRaw[4] = {-1, -1, -1, -1};
int calRefInches[4] = {-1, -1, -1, -1};
// Cache to avoid flicker
int prevBasinLevel[4] = {-1, -1, -1, -1};
int prevRawBasin[4] = {-1, -1, -1, -1};

// PIN entry
String pinCode = "";
const char* CAL_PIN = "123";

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

// REMOVED: ultrasonic read interval (Hub handles sensors)

// REMOVED: readUltrasonic4Wire() - sensor moved to WROOM Hub

// REMOVED: distanceToPercent() - calculation moved to WROOM Hub

// ---- Screen states ----
enum Screen { SCREEN_MAIN, SCREEN_WIFI_LIST, SCREEN_WIFI_PASS, SCREEN_WIFI_CONNECTING, SCREEN_WIFI_FAIL, SCREEN_QR_LOCAL, SCREEN_QR_REMOTE, SCREEN_INFO, SCREEN_PIN, SCREEN_CALIB };
Screen currentScreen = SCREEN_MAIN;

// Non-blocking WiFi connection
unsigned long wifiConnectStart = 0;
const unsigned long WIFI_CONNECT_TIMEOUT = 15000; // 15s max

// Dropdown menu
bool menuOpen = false;
#define MENU_ITEMS   5
#define MENU_X       2
#define MENU_Y       28
#define MENU_W       140
#define MENU_ITEM_H  32
#define MENU_H       (MENU_ITEMS * MENU_ITEM_H + 2)
const char* menuLabels[MENU_ITEMS] = { "WiFi", "QR WiFi", "QR Remote", "Infos", "Calibration" };

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
void bleScanInkbird();
void drawTrendGraph();
void drawBasinCards();
void drawBasinFrames();
void drawBasinValues();

// ---- MQTT ----
void publishState() {
  if (mqtt.connected()) {
    // Display-only: only publish vacuum state, Hub publishes sensor data
    mqtt.publish(mqttTopicState.c_str(), lightOn ? "1" : "0", true);
  }
}

void mqttCallback(char* topic, byte* payload, unsigned int length) {
  String msg;
  for (unsigned int i = 0; i < length; i++) msg += (char)payload[i];
  Serial.printf("MQTT recv: %s = %s\n", topic, msg.c_str());

  if (String(topic) == mqttTopicCmd) {
    if (msg == "toggle") {
      lightOn = !lightOn;
      digitalWrite(VACUUM_PIN, lightOn ? HIGH : LOW);
      publishState();
      Serial.printf(">>> MQTT: Vacuum %s, GPIO4 %s\n", lightOn ? "ON" : "OFF", lightOn ? "HIGH" : "LOW");
    } else if (msg == "on") {
      lightOn = true;
      digitalWrite(VACUUM_PIN, HIGH);
      publishState();
    } else if (msg == "off") {
      lightOn = false;
      digitalWrite(VACUUM_PIN, LOW);
      publishState();
    }
  }
  // Donnees capteurs entrantes
  // Dompeur MQTT callback removed
  else if (String(topic) == mqttTopicTemp) {
    temperature = msg.toFloat();
    Serial.printf(">>> MQTT: Temp = %.1f\n", temperature);
    if (currentScreen == SCREEN_MAIN && !menuOpen) drawTempCard();
  }
  else if (String(topic) == mqttTopicBasin1) {
    basin1 = msg.toInt();
    Serial.printf(">>> MQTT: Basin1 = %d%%\n", basin1);
    if (currentScreen == SCREEN_MAIN && !menuOpen) drawBasinValues();
  }
  else if (String(topic) == mqttTopicBasin2) {
    basin2 = msg.toInt();
    Serial.printf(">>> MQTT: Basin2 = %d%%\n", basin2);
    if (currentScreen == SCREEN_MAIN && !menuOpen) drawBasinValues();
  }
  else if (String(topic) == mqttTopicBasin3) {
    basin3 = msg.toInt();
    Serial.printf(">>> MQTT: Basin3 = %d%%\n", basin3);
    if (currentScreen == SCREEN_MAIN && !menuOpen) drawBasinValues();
  }
  else if (String(topic) == mqttTopicBasin4) {
    basin4 = msg.toInt();
    Serial.printf(">>> MQTT: Basin4 = %d%%\n", basin4);
    if (currentScreen == SCREEN_MAIN && !menuOpen) drawBasinValues();
  }
  // Calibration command from MQTT dashboard
  else if (String(topic) == mqttTopicCal) {
    Serial.printf(">>> MQTT: cmd/cal = %s\n", msg.c_str());
    // Parse JSON: {"basin":1,"point":"low"} or {"basin":1,"point":"high"}
    int bIdx = msg.indexOf("\"basin\":");
    int pIdx = msg.indexOf("\"point\":");
    if (bIdx >= 0 && pIdx >= 0) {
      int basin = msg.substring(bIdx + 8, msg.indexOf(',', bIdx)).toInt();
      String point = "";
      int pStart = msg.indexOf('"', pIdx + 8) + 1;
      int pEnd = msg.indexOf('"', pStart);
      if (pStart > 0 && pEnd > pStart) point = msg.substring(pStart, pEnd);

      if (basin >= 1 && basin <= 4) {
        int idx = basin - 1;
        if (point == "low") {
          calLow[idx] = rawBasin[idx];
          Serial.printf("CAL MQTT: Basin %d LOW = %d\n", basin, rawBasin[idx]);
        } else if (point == "high") {
          calHigh[idx] = rawBasin[idx];
          Serial.printf("CAL MQTT: Basin %d HIGH = %d\n", basin, rawBasin[idx]);
        }
        // Save to NVS
        Preferences calPrefs;
        if (calPrefs.begin("calib", false)) {
          String kl = "lo" + String(idx);
          String kh = "hi" + String(idx);
          calPrefs.putInt(kl.c_str(), calLow[idx]);
          calPrefs.putInt(kh.c_str(), calHigh[idx]);
          calPrefs.end();
        }
        // Publish cal data back to MQTT
        String calJson = "{\"low\":" + (calLow[idx] >= 0 ? String(calLow[idx]) : String("null")) +
                         ",\"high\":" + (calHigh[idx] >= 0 ? String(calHigh[idx]) : String("null")) + "}";
        String calTopic = "cyd/" + deviceId + "/basin" + String(basin) + "/cal";
        mqtt.publish(calTopic.c_str(), calJson.c_str(), true);
        Serial.printf("CAL MQTT: published %s = %s\n", calTopic.c_str(), calJson.c_str());

        // Publish raw value
        String rawTopic = "cyd/" + deviceId + "/basin" + String(basin) + "/raw";
        mqtt.publish(rawTopic.c_str(), String(rawBasin[idx]).c_str(), true);

        // Redraw if on main screen
        if (currentScreen == SCREEN_MAIN && !menuOpen) drawBasinValues();
      }
    }
  }
  else {
    String topicStr = String(topic);
    for (int i = 0; i < 4; i++) {
      // Handle raw basin topics
      String rawTopic = "cyd/" + deviceId + "/basin" + String(i + 1) + "/raw";
      if (topicStr == rawTopic) {
        rawBasin[i] = msg.toInt();
        Serial.printf(">>> MQTT: Basin%d raw = %dcm\n", i + 1, rawBasin[i]);
        if (currentScreen == SCREEN_MAIN && !menuOpen) drawBasinValues();
        break;
      }
      // Handle cal topics: {"refRaw":XX,"refInches":YY}
      String calTopic = "cyd/" + deviceId + "/basin" + String(i + 1) + "/cal";
      if (topicStr == calTopic) {
        int rr = msg.indexOf("\"refRaw\":");
        int ri = msg.indexOf("\"refInches\":");
        if (rr >= 0 && ri >= 0) {
          calRefRaw[i] = msg.substring(rr + 9, msg.indexOf(',', rr)).toInt();
          calRefInches[i] = msg.substring(ri + 12, msg.indexOf('}', ri)).toInt();
          Serial.printf(">>> MQTT: Basin%d cal refRaw=%d refInches=%d\n", i + 1, calRefRaw[i], calRefInches[i]);
          // Invalidate cache to force redraw with new calibration
          prevRawBasin[i] = -999;
          if (currentScreen == SCREEN_MAIN && !menuOpen) drawBasinValues();
        }
        break;
      }
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
    // mqtt.subscribe(mqttTopicDompeur.c_str()); // removed
    mqtt.subscribe(mqttTopicTemp.c_str());
    mqtt.subscribe(mqttTopicBasin1.c_str());
    mqtt.subscribe(mqttTopicBasin2.c_str());
    mqtt.subscribe(mqttTopicBasin3.c_str());
    mqtt.subscribe(mqttTopicBasin4.c_str());
    mqtt.subscribe(mqttTopicCal.c_str());
    // mqtt.subscribe(mqttTopicDompeurLive.c_str()); // removed
    mqtt.subscribe(mqttTopicHumidity.c_str());
    // Subscribe to raw basin values for calibration screen
    String rawSub1 = "cyd/" + deviceId + "/basin1/raw";
    String rawSub2 = "cyd/" + deviceId + "/basin2/raw";
    String rawSub3 = "cyd/" + deviceId + "/basin3/raw";
    String rawSub4 = "cyd/" + deviceId + "/basin4/raw";
    mqtt.subscribe(rawSub1.c_str());
    mqtt.subscribe(rawSub2.c_str());
    mqtt.subscribe(rawSub3.c_str());
    mqtt.subscribe(rawSub4.c_str());
    // Subscribe to cal topics (refRaw/refInches from HTML dashboard)
    for (int i = 1; i <= 4; i++) {
      String calSub = "cyd/" + deviceId + "/basin" + String(i) + "/cal";
      mqtt.subscribe(calSub.c_str());
    }
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
    tft.fillRect(294, 7 + i * 5, 16, 2, C_TXT);
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
  tft.fillRect(0, 0, SW, 24, C_HEADER);
  // Title
  tft.setTextFont(1); tft.setTextSize(2);
  tft.setTextDatum(ML_DATUM);
  tft.setTextColor(C_TXT, C_HEADER);
  tft.drawString("CABANE MARCOUX", 8, 12);
  // Menu icon (right side)
  drawMenuIcon();
  // WiFi dot
  uint16_t wc = (WiFi.status() == WL_CONNECTED) ? C_GREEN : C_RED;
  tft.fillCircle(316, 12, 3, wc);
}

void drawDompeurCard() {
  int cx = 4, cy = 4, cw = 154, ch = 68;
  tft.fillRoundRect(cx, cy, cw, ch, 6, C_CARD);
  tft.drawRoundRect(cx, cy, cw, ch, 6, C_BORDER);
  tft.fillRect(cx, cy, cw, 2, C_AMBER);
  tft.setTextFont(1); tft.setTextSize(1);
  tft.setTextDatum(TL_DATUM);
  tft.setTextColor(C_TXT_GRAY, C_CARD);
  tft.drawString("DOMPEUR", cx + 8, cy + 5);

  unsigned long elapsedMs = (lsLastEdge > 0) ? (millis() - lsLastEdge) : 0;
  unsigned long elapsed = elapsedMs / 1000;
  int eMin = elapsed / 60;
  int eSec = elapsed % 60;

  // Dernier cycle
  tft.setTextSize(2);
  tft.setTextDatum(MC_DATUM);
  if (dompeurReset) {
    tft.setTextColor(C_TXT_GRAY, C_CARD);
    tft.drawString("--:--", cx + cw / 2, cy + 28);
  } else if (lsLastEdge > 0 && elapsedMs >= DOMPEUR_ALERT_MS) {
    bool blink = (millis() / 500) % 2;
    tft.setTextColor(blink ? C_RED : C_CARD, C_CARD);
    tft.drawString(dompeurTime.c_str(), cx + cw / 2, cy + 28);
  } else {
    tft.setTextColor(C_CYAN, C_CARD);
    tft.drawString(dompeurTime.c_str(), cx + cw / 2, cy + 28);
  }

  // Compteur temps reel
  char eBuf[8];
  if (dompeurReset || lsLastEdge == 0) {
    snprintf(eBuf, sizeof(eBuf), "--:--");
    tft.setTextSize(2);
    tft.setTextColor(C_TXT_GRAY, C_CARD);
  } else if (elapsedMs >= DOMPEUR_ALERT_MS) {
    snprintf(eBuf, sizeof(eBuf), "%02d:%02d", eMin, eSec);
    bool blink = (millis() / 500) % 2;
    tft.setTextSize(2);
    tft.setTextColor(blink ? C_RED : C_CARD, C_CARD);
  } else {
    snprintf(eBuf, sizeof(eBuf), "%02d:%02d", eMin, eSec);
    tft.setTextSize(2);
    tft.setTextColor(C_GREEN, C_CARD);
  }
  tft.drawString(eBuf, cx + cw / 2, cy + 52);
}

void drawTempCard() {
  int cx = 162, cy = 4, cw = 154, ch = 68;
  tft.fillRoundRect(cx, cy, cw, ch, 6, C_CARD);
  tft.drawRoundRect(cx, cy, cw, ch, 6, C_BORDER);
  tft.fillRect(cx, cy, cw, 2, C_CYAN);
  tft.setTextFont(1); tft.setTextSize(1);
  tft.setTextDatum(TL_DATUM);
  tft.setTextColor(C_TXT_GRAY, C_CARD);
  tft.drawString("TEMPERATURE", cx + 8, cy + 5);
  tft.setTextSize(3);
  tft.setTextDatum(MC_DATUM);
  tft.setTextColor(C_CYAN, C_CARD);
  String tempStr = String(temperature, 1) + " C";
  tft.drawString(tempStr.c_str(), cx + cw / 2, cy + 40);
}

// ---- Trend Graph ----
void drawTrendGraph() {
  int gx = 4, gy = 100, gw = SW - 8, gh = 44;
  tft.fillRect(gx, gy, 2, gh, C_BLUE);
  tft.fillRoundRect(gx + 2, gy, gw - 2, gh, 4, C_CARD);
  tft.drawRoundRect(gx + 2, gy, gw - 2, gh, 4, C_BORDER);
  tft.setTextFont(1); tft.setTextSize(1);
  tft.setTextDatum(TL_DATUM);
  tft.setTextColor(C_TXT_GRAY, C_CARD);
  tft.drawString("Historique - 30 pts", gx + 8, gy + 3);

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
    // Color: green if going up, red if going down
    uint16_t lc = (dompeurHist[i] >= dompeurHist[i - 1]) ? C_GREEN : C_RED;
    tft.drawLine(x1, y1, x2, y2, lc);
    tft.drawLine(x1, y1 + 1, x2, y2 + 1, lc); // thicker
  }

  // Trend arrow (last vs first)
  bool up = dompeurHist[n - 1] > dompeurHist[0];
  uint16_t arrowC = up ? C_GREEN : C_RED;
  int ax = gx + gw - 16, ay = gy + 3;
  if (up) { // arrow up = good (time increasing)
    tft.fillTriangle(ax, ay + 2, ax - 4, ay + 8, ax + 4, ay + 8, arrowC);
  } else { // arrow down = bad (time decreasing)
    tft.fillTriangle(ax, ay + 8, ax - 4, ay + 2, ax + 4, ay + 2, arrowC);
  }
}

// ---- Basins (horizontal bars) ----
// Draw static frame (called once)
void drawBasinTankFrame(int cx, int tankW, int tankH, int topY, const char* name) {
  tft.setTextFont(2); tft.setTextSize(1);
  tft.setTextDatum(TC_DATUM);
  tft.setTextColor(C_LABEL, C_CARD);
  tft.drawString(name, cx + tankW / 2, topY);
  int ty = topY + 16;
  tft.fillRect(cx, ty, tankW, tankH, C_SB_BG);
  tft.drawRect(cx, ty, tankW, tankH, C_BORDER);
  for (int g = 1; g <= 3; g++) {
    int gy = ty + tankH - (tankH * g * 25 / 100);
    tft.drawFastHLine(cx + 1, gy, 4, C_BORDER);
    tft.drawFastHLine(cx + tankW - 5, gy, 4, C_BORDER);
  }
}

// Update fill + percentage only (no flicker)
void drawBasinTankValue(int cx, int tankW, int tankH, int topY, int level) {
  int ty = topY + 16;
  // Clear inside tank (keep border)
  tft.fillRect(cx + 1, ty + 1, tankW - 2, tankH - 2, C_SB_BG);
  // Redraw graduation lines over cleared area
  for (int g = 1; g <= 3; g++) {
    int gy = ty + tankH - (tankH * g * 25 / 100);
    tft.drawFastHLine(cx + 1, gy, 4, C_BORDER);
    tft.drawFastHLine(cx + tankW - 5, gy, 4, C_BORDER);
  }
  // Fill from bottom
  int fillH = (tankH - 2) * level / 100;
  if (fillH > 0) {
    uint16_t bc = C_GREEN;
    if (level >= 90) bc = C_RED;
    else if (level >= 61) bc = C_YELLOW;
    tft.fillRect(cx + 1, ty + tankH - 1 - fillH, tankW - 2, fillH, bc);
  }
  // Percentage below tank (overwrite with background color)
  tft.setTextDatum(TC_DATUM);
  tft.setTextFont(2); tft.setTextSize(1);
  // Clear old text area
  tft.fillRect(cx, ty + tankH + 2, tankW, 18, C_CARD);
  tft.setTextColor(C_TXT, C_CARD);
  String pct = String(level) + "%";
  tft.drawString(pct.c_str(), cx + tankW / 2, ty + tankH + 3);
}

// Convert raw cm to inches using HTML-style calibration
float rawToInches(int basinIdx, int rawCm) {
  if (calRefRaw[basinIdx] >= 0 && calRefInches[basinIdx] >= 0) {
    // Same formula as HTML: deltaRaw = refRaw - currentRaw; deltaInches = deltaRaw / 2.54; result = refInches + deltaInches
    float deltaRaw = calRefRaw[basinIdx] - rawCm;
    float deltaInches = deltaRaw / 2.54;
    return calRefInches[basinIdx] + deltaInches;
  }
  // Fallback: simple conversion
  return rawCm / 2.54;
}

// Update fill + percentage + inches
void drawBasinTankValueInches(int cx, int tankW, int tankH, int topY, int level, int rawCm, int basinIdx) {
  drawBasinTankValue(cx, tankW, tankH, topY, level);
  // Overwrite percentage with inches
  int ty = topY + 16;
  tft.fillRect(cx, ty + tankH + 2, tankW, 18, C_CARD);
  tft.setTextDatum(TC_DATUM);
  tft.setTextFont(2); tft.setTextSize(1);
  tft.setTextColor(C_TXT, C_CARD);
  float inches = rawToInches(basinIdx, rawCm);
  int roundedInches = (int)round(inches);
  String inStr = String(roundedInches) + " po";
  tft.drawString(inStr.c_str(), cx + tankW / 2, ty + tankH + 3);
}

// Legacy compat wrapper
void drawBasinTank(int cx, int tankW, int tankH, int topY, const char* name, int level) {
  drawBasinTankFrame(cx, tankW, tankH, topY, name);
  drawBasinTankValue(cx, tankW, tankH, topY, level);
}

void drawGearIcon(int x, int y) {
  // 24x24 gear icon
  tft.fillCircle(x + 12, y + 12, 9, C_TXT_GRAY);
  tft.fillCircle(x + 12, y + 12, 4, C_CARD);
  // Teeth (4 cardinal)
  for (int a = 0; a < 4; a++) {
    int dx[] = {0, 11, 0, -11};
    int dy[] = {-11, 0, 11, 0};
    tft.fillRect(x + 12 + dx[a] - 2, y + 12 + dy[a] - 2, 5, 5, C_TXT_GRAY);
  }
}

// Basin layout constants
const int BASIN_CY = 76, BASIN_CH = 160;
const int BASIN_TW = 60, BASIN_TH = 110;

int basinGap() { return (SW - 8 - 4 * BASIN_TW) / 5; }
int basinTopY() { return BASIN_CY + 6; }
int basinX(int i) { return 4 + basinGap() * (i + 1) + BASIN_TW * i; }

// Draw static frames (call once at screen init)
void drawBasinFrames() {
  tft.fillRoundRect(4, BASIN_CY, SW - 8, BASIN_CH, 6, C_CARD);
  tft.drawRoundRect(4, BASIN_CY, SW - 8, BASIN_CH, 6, C_BORDER);
  int ty = basinTopY();
  drawBasinTankFrame(basinX(0), BASIN_TW, BASIN_TH, ty, "Eau");
  drawBasinTankFrame(basinX(1), BASIN_TW, BASIN_TH, ty, "Concentre");
  drawBasinTankFrame(basinX(2), BASIN_TW, BASIN_TH, ty, "Reserve");
  drawBasinTankFrame(basinX(3), BASIN_TW, BASIN_TH, ty, "Permeat");
}

// Update values only (no flicker)
void drawBasinValues() {
  int ty = basinTopY();
  int levels[4] = {basin1, basin2, basin3, basin4};
  for (int i = 0; i < 4; i++) {
    if (levels[i] != prevBasinLevel[i] || rawBasin[i] != prevRawBasin[i]) {
      drawBasinTankValueInches(basinX(i), BASIN_TW, BASIN_TH, ty, levels[i], rawBasin[i], i);
      prevBasinLevel[i] = levels[i];
      prevRawBasin[i] = rawBasin[i];
    }
  }
}

// Full draw (frame + values) - for initial screen
void drawBasinCards() {
  drawBasinFrames();
  drawBasinValues();
}

void drawVacuumBtn() {
  int sx = 4, sy = 214, sw = SW - 8, sh = 22;
  int hdlW = 36, hdlH = 18;
  // Track
  uint16_t brd = lightOn ? C_GREEN : C_RED;
  uint16_t trackFill = lightOn ? tft.color565(0, 40, 0) : tft.color565(40, 0, 0);
  tft.fillRoundRect(sx, sy, sw, sh, 4, trackFill);
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
    tft.setTextColor(C_RED, trackFill);
    tft.drawString("> VACUUM ON", sx + hdlW + 10, sy + sh / 2);
  } else {
    tft.setTextDatum(MR_DATUM);
    tft.setTextColor(C_GREEN, trackFill);
    tft.drawString("VACUUM OFF <", sx + sw - hdlW - 10, sy + sh / 2);
  }
}

void drawStatusBar() {
  int sy = 216, sh = 20;
  tft.fillRoundRect(4, sy, SW - 8, sh, 6, C_SB_BG);
  tft.drawRoundRect(4, sy, SW - 8, sh, 6, C_BORDER);
  tft.setTextFont(1); tft.setTextSize(1);
  tft.setTextDatum(ML_DATUM);
  if (WiFi.status() == WL_CONNECTED) {
    tft.fillCircle(14, sy + sh / 2, 3, C_GREEN);
    tft.setTextColor(C_TXT_DIM, C_SB_BG);
    tft.drawString("Connecte", 22, sy + sh / 2);
  } else {
    tft.fillCircle(14, sy + sh / 2, 3, C_RED);
    tft.setTextColor(C_TXT_DIM, C_SB_BG);
    tft.drawString("Deconnecte", 22, sy + sh / 2);
  }
  // Temperature au centre
  tft.setTextDatum(MC_DATUM);
  tft.setTextColor(C_CYAN, C_SB_BG);
  String tempStr = String(temperature, 1) + "C";
  tft.drawString(tempStr.c_str(), SW / 2, sy + sh / 2);
  // Device ID a droite
  tft.setTextDatum(MR_DATUM);
  tft.setTextColor(C_TXT_DIM, C_SB_BG);
  String idStr = "ID: " + deviceId;
  tft.drawString(idStr.c_str(), SW - 10, sy + sh / 2);
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
  }
}

// Forward declarations
void drawCalibScreen();
void drawPinScreen();

// ---- PIN Screen ----
void drawPinScreen() {
  tft.fillScreen(C_BG);
  tft.fillRect(0, 0, SW, 24, C_HEADER);
  tft.setTextFont(1); tft.setTextSize(1);
  tft.setTextDatum(MC_DATUM);
  tft.setTextColor(C_CYAN, C_HEADER);
  tft.drawString(pinReason == 1 ? "NIP VACUUM" : "NIP CALIBRATION", SW / 2, 12);

  // PIN dots
  for (int i = 0; i < 3; i++) {
    int dx = SW / 2 - 30 + i * 30;
    if ((int)pinCode.length() > i) {
      tft.fillCircle(dx, 40, 7, C_CYAN);
    } else {
      tft.drawCircle(dx, 40, 7, C_BORDER);
    }
  }

  // Keypad 3x4
  const char keys[] = "123456789*0#";
  for (int r = 0; r < 4; r++) {
    for (int col = 0; col < 3; col++) {
      int kx = 50 + col * 80;
      int ky = 62 + r * 38;
      char k = keys[r * 3 + col];
      if (k == '*') {
        // Delete key
        tft.fillRoundRect(kx, ky, 68, 32, 6, C_CARD);
        tft.setTextDatum(MC_DATUM);
        tft.setTextColor(C_RED, C_CARD);
        tft.setTextSize(1);
        tft.drawString("DEL", kx + 34, ky + 16);
      } else if (k == '#') {
        // Empty
        tft.fillRoundRect(kx, ky, 68, 32, 6, C_CARD);
      } else {
        tft.fillRoundRect(kx, ky, 68, 32, 6, C_BORDER);
        tft.setTextFont(1); tft.setTextSize(2);
        tft.setTextDatum(MC_DATUM);
        tft.setTextColor(C_TXT, C_BORDER);
        char buf[2] = {k, 0};
        tft.drawString(buf, kx + 34, ky + 16);
      }
    }
  }

  // Annuler button
  tft.fillRoundRect(SW / 2 - 55, 218, 110, 20, 6, C_CARD);
  tft.setTextFont(1); tft.setTextSize(1);
  tft.setTextDatum(MC_DATUM);
  tft.setTextColor(C_TXT_GRAY, C_CARD);
  tft.drawString("ANNULER", SW / 2, 228);
}

void handlePinTouch(int tx, int ty) {
  // Annuler
  if (ty >= 218) {
    pinCode = "";
    pinReason = 0;
    currentScreen = SCREEN_MAIN;
    drawMainScreen();
    return;
  }
  // Keypad
  const char keys[] = "123456789*0#";
  for (int r = 0; r < 4; r++) {
    for (int col = 0; col < 3; col++) {
      int kx = 50 + col * 80;
      int ky = 62 + r * 38;
      if (tx >= kx && tx <= kx + 68 && ty >= ky && ty <= ky + 32) {
        char k = keys[r * 3 + col];
        if (k == '*') {
          // Delete
          if (pinCode.length() > 0) pinCode.remove(pinCode.length() - 1);
          drawPinScreen();
        } else if (k == '#') {
          // Nothing
        } else if (pinCode.length() < 3) {
          pinCode += k;
          drawPinScreen();
          if (pinCode.length() == 3) {
            delay(200);
            if (pinReason == 1 && pinCode == String(VACUUM_PIN_CODE)) {
              // Vacuum toggle confirmed
              pinCode = "";
              lightOn = !lightOn;
              digitalWrite(VACUUM_PIN, lightOn ? HIGH : LOW);
              publishState();
              Serial.printf(">>> PIN: Vacuum %s, GPIO4 %s\n", lightOn ? "ON" : "OFF", lightOn ? "HIGH" : "LOW");
              // Feedback screen
              tft.fillScreen(C_BG);
              tft.setTextFont(1); tft.setTextSize(2);
              tft.setTextDatum(MC_DATUM);
              if (lightOn) {
                tft.setTextColor(C_GREEN, C_BG);
                tft.drawString("VACUUM ON", SW / 2, SH / 2 - 10);
              } else {
                tft.setTextColor(C_RED, C_BG);
                tft.drawString("VACUUM OFF", SW / 2, SH / 2 - 10);
              }
              tft.setTextSize(1);
              tft.setTextColor(C_TXT_GRAY, C_BG);
              tft.drawString(lightOn ? "GPIO 4 = HIGH" : "GPIO 4 = LOW", SW / 2, SH / 2 + 15);
              delay(1200);
              pinReason = 0;
              currentScreen = SCREEN_MAIN;
              drawMainScreen();
            } else if (pinReason == 0 && pinCode == String(CAL_PIN)) {
              pinCode = "";
              currentScreen = SCREEN_CALIB;
              drawCalibScreen();
            } else {
              // Wrong PIN - show error briefly
              tft.setTextFont(1); tft.setTextSize(1);
              tft.setTextDatum(MC_DATUM);
              tft.setTextColor(C_RED, C_BG);
              tft.drawString("Code incorrect", SW / 2, 54);
              delay(800);
              pinCode = "";
              drawPinScreen();
            }
          }
        }
        return;
      }
    }
  }
}

// ---- Calibration Screen (2-point, like HTML) ----
void drawCalibScreen() {
  tft.fillScreen(C_BG);
  tft.fillRect(0, 0, SW, 24, C_HEADER);
  tft.setTextFont(1); tft.setTextSize(1);
  tft.setTextDatum(MC_DATUM);
  tft.setTextColor(C_CYAN, C_HEADER);
  tft.drawString("CALIBRATION BASSINS", SW / 2, 12);

  const char* names[] = {"Bassin 1", "Bassin 2", "Bassin 3"};

  for (int i = 0; i < 3; i++) {
    int ry = 30 + i * 60;
    // Basin name + raw value
    tft.setTextFont(1); tft.setTextSize(1);
    tft.setTextDatum(ML_DATUM);
    tft.setTextColor(C_LABEL, C_BG);
    tft.drawString(names[i], 10, ry + 4);
    tft.setTextDatum(MR_DATUM);
    tft.setTextColor(C_AMBER, C_BG);
    String rawStr = "Brut: " + String(rawBasin[i]);
    tft.drawString(rawStr.c_str(), SW - 10, ry + 4);

    // Calibration info
    tft.setTextDatum(ML_DATUM);
    tft.setTextColor(C_TXT_DIM, C_BG);
    String info = "Bas: " + (calLow[i] >= 0 ? String(calLow[i]) : String("--")) +
                  " | Haut: " + (calHigh[i] >= 0 ? String(calHigh[i]) : String("--"));
    tft.drawString(info.c_str(), 10, ry + 18);

    // Bas Niveau button (red)
    tft.fillRoundRect(10, ry + 30, 140, 22, 4, C_RED);
    tft.setTextDatum(MC_DATUM);
    tft.setTextColor(C_TXT, C_RED);
    tft.drawString("BAS NIVEAU", 80, ry + 41);

    // Haut Niveau button (blue)
    uint16_t btnBlue = tft.color565(30, 64, 175);
    tft.fillRoundRect(168, ry + 30, 140, 22, 4, btnBlue);
    tft.setTextColor(C_TXT, btnBlue);
    tft.drawString("HAUT NIVEAU", 238, ry + 41);
  }

  // Fermer button
  tft.fillRoundRect(SW / 2 - 55, 215, 110, 22, 6, C_CARD);
  tft.setTextFont(1); tft.setTextSize(1);
  tft.setTextDatum(MC_DATUM);
  tft.setTextColor(C_TXT_GRAY, C_CARD);
  tft.drawString("FERMER", SW / 2, 226);
}

void handleCalibTouch(int tx, int ty) {
  // Fermer button
  if (ty >= 215) {
    // Save calibration to Preferences
    prefs.begin("calib", false);
    for (int i = 0; i < 3; i++) {
      String kl = "lo" + String(i);
      String kh = "hi" + String(i);
      prefs.putInt(kl.c_str(), calLow[i]);
      prefs.putInt(kh.c_str(), calHigh[i]);
    }
    prefs.end();
    currentScreen = SCREEN_MAIN;
    drawMainScreen();
    return;
  }
  // Bas/Haut buttons for each basin
  for (int i = 0; i < 3; i++) {
    int ry = 30 + i * 60;
    if (ty >= ry + 30 && ty <= ry + 52) {
      if (tx >= 10 && tx <= 150) {
        // Bas Niveau - capture raw value
        calLow[i] = rawBasin[i];
        Serial.printf(">>> Calib Basin %d LOW = %d\n", i + 1, rawBasin[i]);
        // Publish MQTT calibration command
        if (mqtt.connected()) {
          String cmd = "{\"basin\":" + String(i + 1) + ",\"point\":\"low\"}";
          String topic = "cyd/" + deviceId + "/cmd/cal";
          mqtt.publish(topic.c_str(), cmd.c_str());
        }
        drawCalibScreen();
        return;
      }
      if (tx >= 168 && tx <= 308) {
        // Haut Niveau - capture raw value
        calHigh[i] = rawBasin[i];
        Serial.printf(">>> Calib Basin %d HIGH = %d\n", i + 1, rawBasin[i]);
        if (mqtt.connected()) {
          String cmd = "{\"basin\":" + String(i + 1) + ",\"point\":\"high\"}";
          String topic = "cyd/" + deviceId + "/cmd/cal";
          mqtt.publish(topic.c_str(), cmd.c_str());
        }
        drawCalibScreen();
        return;
      }
    }
  }
}

void drawMainScreen() {
  tft.fillScreen(C_BG);
  drawDompeurCard();
  drawTempCard();
  drawBasinCards();
}

// ---- Drawing: WiFi list screen ----
void drawWifiListScreen() {
  tft.fillScreen(TFT_BLACK);
  tft.setTextFont(1);
  tft.setTextSize(2);
  tft.setTextDatum(MC_DATUM);
  tft.setTextColor(TFT_YELLOW, TFT_BLACK);
  tft.drawString("Scan WiFi...", SW / 2, SH / 2);

  // Stop BLE before WiFi scan (shared radio)
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
  Serial.print("WiFi scan result: "); Serial.println(n);
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
  // Vacuum slider removed from TFT
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
      case 1: // QR WiFi
        menuOpen = false;
        currentScreen = SCREEN_QR_LOCAL;
        drawQRScreen(true);
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
      case 4: // Calibration
        menuOpen = false;
        pinCode = "";
        currentScreen = SCREEN_PIN;
        drawPinScreen();
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
  tft.drawString(isLocal ? "QR WiFi" : "QR Remote", SW / 2, 11);

  // Construire l URL
  String url;
  if (isLocal) {
    url = "WIFI:T:WPA;S:Cabane Marcoux;P:Cabane2025;;";
  } else {
    url = "https://robingag.github.io/cabane-marcoux/cyd_lumiere/index.html?id=" + deviceId;
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
<div class="r"><div class="cd dm"><div class="lb">Dompeur</div><div class="vl" id="dmp">--:--</div><div style="font-size:14px;color:#4f4;margin-top:4px" id="dlv">--:--</div></div><div class="cd tp"><div class="lb">Temperature</div><div class="vl" id="tmp">--.-°C</div></div></div>
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
function sba(n,v){var l=parseInt(v)||0;var f=document.getElementById("bf"+n);f.style.width=l+"%";f.className="bf "+(l>=91?"h":l>=61?"m":"l");document.getElementById("bp"+n).textContent=l+"%"}
function dg(){var cv=document.getElementById("gr"),ctx=cv.getContext("2d"),dp=window.devicePixelRatio||1;cv.width=cv.offsetWidth*dp;cv.height=90*dp;ctx.scale(dp,dp);var W=cv.offsetWidth,H=90;ctx.clearRect(0,0,W,H);ctx.fillStyle="#111";ctx.fillRect(0,0,W,H);if(hist.length<2){ctx.fillStyle="#444";ctx.font="12px Arial";ctx.textAlign="center";ctx.fillText("En attente...",W/2,H/2+4);document.getElementById("ar").textContent="";return}var n=hist.length,mn=Math.min.apply(null,hist),mx=Math.max.apply(null,hist),rg=mx-mn;if(rg<10){mn-=5;mx+=5;rg=mx-mn}var p={l:30,r:8,t:6,b:14},cw=W-p.l-p.r,ch=H-p.t-p.b;ctx.strokeStyle="#2a2a4e";ctx.setLineDash([3,3]);for(var i=0;i<=2;i++){var y=p.t+ch*i/2;ctx.beginPath();ctx.moveTo(p.l,y);ctx.lineTo(p.l+cw,y);ctx.stroke()}ctx.setLineDash([]);ctx.fillStyle="#556";ctx.font="9px monospace";ctx.textAlign="right";ctx.fillText(mx+"s",p.l-3,p.t+7);ctx.fillText(mn+"s",p.l-3,p.t+ch+3);ctx.lineWidth=2;ctx.lineJoin="round";for(var i=1;i<n;i++){var x1=p.l+(i-1)*cw/(n-1),y1=p.t+ch-(hist[i-1]-mn)*ch/rg,x2=p.l+i*cw/(n-1),y2=p.t+ch-(hist[i]-mn)*ch/rg;ctx.strokeStyle=hist[i]>=hist[i-1]?"#4f4":"#f44";ctx.beginPath();ctx.moveTo(x1,y1);ctx.lineTo(x2,y2);ctx.stroke()}var a=document.getElementById("ar");if(hist[n-1]>hist[0]){a.textContent="\u25B2";a.className="ar d"}else{a.textContent="\u25BC";a.className="ar u"}}
function od(v){document.getElementById("dmp").textContent=v;var p=v.split(":");if(p.length===2){var s=parseInt(p[0])*60+parseInt(p[1]);if(s>0){hist.push(s);if(hist.length>30)hist.shift();dg()}}}
function ss(t,cl){document.getElementById("st").textContent=t;document.getElementById("dt").className="dt "+cl}
function tg(){if(c&&c.connected)c.publish("cyd/"+id+"/cmd","toggle")}
function go(){ss("Connexion...","w");var urls=["wss://broker.hivemq.com:8884/mqtt","ws://broker.hivemq.com:8000/mqtt"];var ui=0;function tc(){if(ui>=urls.length)ui=0;c=mqtt.connect(urls[ui],{clientId:"r-"+id+"-"+Math.random().toString(16).substr(2,4),clean:true,connectTimeout:8000,reconnectPeriod:0});c.on("connect",function(){ss("Connecte","ok");document.getElementById("vb").disabled=false;var p="cyd/"+id+"/";["state","dompeur","dompeur/live","temp","humidity","basin1","basin2","basin3"].forEach(function(t){c.subscribe(p+t)})});c.on("message",function(tp,m){var v=m.toString(),p="cyd/"+id+"/";if(tp===p+"state")sv(v==="1");if(tp===p+"dompeur")od(v);if(tp===p+"dompeur/live"){var dl=document.getElementById("dlv");dl.textContent=v;dl.style.color=(v==="--:--")?"#666":"#4f4"}if(tp===p+"temp")document.getElementById("tmp").innerHTML=v+"&deg;C";if(tp===p+"basin1")sba(1,v);if(tp===p+"basin2")sba(2,v);if(tp===p+"basin3")sba(3,v)});c.on("error",function(){ss("Essai...","w");c.end(true);ui++;setTimeout(tc,1000)});c.on("close",function(){ss("Deconnecte","er");document.getElementById("vb").disabled=true})}tc()}
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
  digitalWrite(VACUUM_PIN, lightOn ? HIGH : LOW);
  if (currentScreen == SCREEN_MAIN) drawVacuumBtn();
  publishState();
  Serial.printf(">>> Web: Vacuum %s\n", lightOn ? "ON" : "OFF");
  String json = "{\"on\":" + String(lightOn ? "true" : "false") + "}";
  server.send(200, "application/json", json);
}


// ---- BLE Inkbird IBS-TH2 ----
class InkbirdScanCallback : public NimBLEAdvertisedDeviceCallbacks {
  void onResult(NimBLEAdvertisedDevice* device) {
    std::string devName = device->getName();
    std::string devAddr = device->getAddress().toString();
    // Log tous les appareils BLE trouves pour debug
    Serial.print("BLE found: ");
    Serial.print(devAddr.c_str());
    Serial.print(" name='");
    Serial.print(devName.c_str());
    Serial.print("' rssi=");
    Serial.println(device->getRSSI());
    // --- Capteur Bassins WROOM (nom "CBM", magic 0xCB) ---
    if (devName == "CBM" && device->haveManufacturerData()) {
      std::string mfData = device->getManufacturerData();
      // NimBLE: 2 bytes company ID (0xFFFF) + 6 bytes payload
      if (mfData.length() >= 8 && (uint8_t)mfData[2] == 0xCB) {
        uint16_t d2 = (uint8_t)mfData[3] | ((uint8_t)mfData[4] << 8);
        uint16_t d3 = (uint8_t)mfData[5] | ((uint8_t)mfData[6] << 8);
        rawBasin[1] = d2;
        rawBasin[2] = d3;
        // Appliquer calibration si disponible
        if (calLow[1] >= 0 && calHigh[1] >= 0 && calLow[1] != calHigh[1]) {
          basin2 = constrain(map(d2, calLow[1], calHigh[1], 0, 100), 0, 100);
        } else {
          basin2 = d2;  // valeur brute si pas calibre
        }
        if (calLow[2] >= 0 && calHigh[2] >= 0 && calLow[2] != calHigh[2]) {
          basin3 = constrain(map(d3, calLow[2], calHigh[2], 0, 100), 0, 100);
        } else {
          basin3 = d3;
        }
        Serial.printf(">>> CBM BLE: B2=%dcm(%d%%) B3=%dcm(%d%%)\n", d2, basin2, d3, basin3);
        // Publier sur MQTT
        // Display-only: basin data published by Hub
        if (false && mqtt.connected()) {
          // mqtt.publish(mqttTopicBasin2.c_str(), String(basin2).c_str(), true);
          // mqtt.publish(mqttTopicBasin3.c_str(), String(basin3).c_str(), true);
          String raw2Topic = "cyd/" + deviceId + "/basin2/raw";
          String raw3Topic = "cyd/" + deviceId + "/basin3/raw";
          mqtt.publish(raw2Topic.c_str(), String(rawBasin[1]).c_str(), true);
          mqtt.publish(raw3Topic.c_str(), String(rawBasin[2]).c_str(), true);
        }
        if (currentScreen == SCREEN_MAIN && !menuOpen) drawBasinValues();
      }
    }

    // --- WROOM Hub (nom "CBM-HUB", magic 0xCA) ---
    if (devName == "CBM-HUB" && device->haveManufacturerData()) {
      std::string mfData = device->getManufacturerData();
      // NimBLE: 2 bytes company ID (0xFFFF) + 9 bytes payload
      if (mfData.length() >= 11 && (uint8_t)mfData[2] == 0xCA) {
        uint16_t dmpSec = (uint8_t)mfData[3] | ((uint8_t)mfData[4] << 8);
        int b1 = (uint8_t)mfData[5];
        int b2 = (uint8_t)mfData[6];
        int b3 = (uint8_t)mfData[7];
        int16_t tempX10 = (uint8_t)mfData[8] | ((uint8_t)mfData[9] << 8);
        uint8_t flags = (uint8_t)mfData[10];
        bool alert = flags & 0x01;
        bool reset = flags & 0x02;
        // Update dompeur
        if (reset) {
          dompeurReset = true;
          dompeurTime = "--:--";
          lsLastEdge = 0;
        } else if (dmpSec > 0) {
          dompeurReset = false;
          lsLastEdge = millis() - (unsigned long)dmpSec * 1000;
        }
        // Update basins
        basin1 = b1; basin2 = b2; basin3 = b3;
        // Update temp
        temperature = tempX10 / 10.0f;
        Serial.println(">>> HUB BLE received");
        // Refresh display
        if (currentScreen == SCREEN_MAIN && !menuOpen) {
          drawDompeurCard();
          drawBasinCards();
        }
      }
    }

    // IBS-TH2 advertise comme "sps" ou "iBBQ" ou contient "Inkbird"
    bool isInkbird = (devName == "sps" || devName == "iBBQ" || devName.find("Inkbird") != std::string::npos || devName.find("IBS") != std::string::npos);
    // Aussi checker par manufacturer data meme sans nom
    if (isInkbird || (devName.empty() && device->haveManufacturerData())) {
      if (device->haveManufacturerData()) {
        std::string mfData = device->getManufacturerData();
        Serial.print("  MfData len=");
        Serial.print(mfData.length());
        Serial.print(" hex: ");
        for (size_t i = 0; i < mfData.length() && i < 16; i++) {
          char hx[4];
          snprintf(hx, sizeof(hx), "%02X ", (uint8_t)mfData[i]);
          Serial.print(hx);
        }
        Serial.println();
        if (mfData.length() >= 7) {
          int16_t rawTemp = (uint8_t)mfData[0] | ((uint8_t)mfData[1] << 8);
          float temp = rawTemp / 100.0f;
          uint16_t rawHum = (uint8_t)mfData[2] | ((uint8_t)mfData[3] << 8);
          float hum = rawHum / 100.0f;
          int bat = (mfData.length() >= 8) ? (uint8_t)mfData[7] : -1;
          Serial.print("  Parsed: temp=");
          Serial.print(temp);
          Serial.print(" hum=");
          Serial.print(hum);
          Serial.print(" bat=");
          Serial.println(bat);
          if (temp > -40.0 && temp < 80.0 && hum >= 0 && hum <= 100) {
            temperature = temp;
            humidity = hum;
            bleBattery = bat;
            Serial.print(">>> Inkbird OK: ");
            Serial.print(temp);
            Serial.print("C ");
            Serial.print(hum);
            Serial.println("%");
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
  pScan->setAdvertisedDeviceCallbacks(&inkbirdCallback, true);
  pScan->setActiveScan(true);
  pScan->setInterval(100);
  pScan->setWindow(99);
  bleInitDone = true;
  Serial.println("BLE NimBLE init OK - scan Inkbird IBS-TH2");
}

void bleScanInkbird() {
  if (!bleInitDone) return;
  Serial.println("BLE: starting scan 10s...");
  NimBLEScan* pScan = NimBLEDevice::getScan();
  pScan->clearResults();
  // Scan 10 secondes (bloquant) pour mieux capter Inkbird
  pScan->start(10, false);
  Serial.print("BLE: scan done, found ");
  Serial.print(pScan->getResults().getCount());
  Serial.println(" devices");
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
  mqttTopicDompeurLive = "cyd/" + deviceId + "/dompeur/live";
  mqttTopicTemp = "cyd/" + deviceId + "/temp";
  mqttTopicHumidity = "cyd/" + deviceId + "/humidity";
  mqttTopicBasin1 = "cyd/" + deviceId + "/basin1";
  mqttTopicBasin2 = "cyd/" + deviceId + "/basin2";
  mqttTopicBasin3 = "cyd/" + deviceId + "/basin3";
  mqttTopicBasin4 = "cyd/" + deviceId + "/basin4";
  // Additional topics for calibration
  String mqttTopicRaw1 = "cyd/" + deviceId + "/raw1";
  String mqttTopicRaw2 = "cyd/" + deviceId + "/raw2";
  String mqttTopicRaw3 = "cyd/" + deviceId + "/raw3";
  mqttTopicCal = "cyd/" + deviceId + "/cmd/cal";
  Serial.printf("Device ID: %s\n", deviceId.c_str());
  Serial.printf("MQTT topics: %s, %s\n", mqttTopicState.c_str(), mqttTopicCmd.c_str());

  // Touch SPI
  touchSPI.begin(T_CLK, T_DO, T_DIN, T_CS);
  pinMode(T_CS, OUTPUT);
  digitalWrite(T_CS, HIGH);
  pinMode(T_IRQ, INPUT);

  // Limit switch input with pull-up (active LOW)
  // REMOVED: dompeur ISR setup (Hub handles sensors)

  // REMOVED: ultrasonic GPIO setup (Hub handles sensors)

  // Simulateur pulses sur GPIO 1 (TX/P1)
  // REMOVED: simPulse setup

  // Display
  tft.init();
  tft.setRotation(1);
  tft.fillScreen(TFT_BLACK);
  pinMode(TFT_BL, OUTPUT);
  digitalWrite(TFT_BL, HIGH);

  // Vacuum GPIO
  pinMode(VACUUM_PIN, OUTPUT);
  digitalWrite(VACUUM_PIN, LOW);

  // MQTT setup
  mqtt.setServer(MQTT_BROKER, MQTT_PORT);
  mqtt.setCallback(mqttCallback);

  // BLE init deferred — will start after WiFi connected
  // bleInitInkbird() called later in loop when WiFi is up

  // Web server routes
  server.on("/", handleRoot);
  server.on("/remote", handleRemote);
  server.on("/remote-app", handleRemoteApp);
  server.on("/state", handleState);
  server.on("/toggle", handleToggle);

  // NVS
  String savedSSID = "";
  String savedPass = "";
  // Load 2-point calibration
  if (prefs.begin("calib", true)) {
    for (int i = 0; i < 3; i++) {
      String kl = "lo" + String(i);
      String kh = "hi" + String(i);
      calLow[i] = prefs.getInt(kl.c_str(), -1);
      calHigh[i] = prefs.getInt(kh.c_str(), -1);
    }
    prefs.end();
  }

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

  // BLE scan periodique Inkbird
  if (millis() - lastBleScan >= BLE_SCAN_INTERVAL) {
    lastBleScan = millis();
    Serial.println("--- BLE scan cycle ---");
    Serial.print("bleInitDone=");
    Serial.println(bleInitDone);
    if (!bleInitDone) {
      Serial.println("BLE: init NimBLE...");
      bleInitInkbird();
      Serial.println("BLE: init done");
    }
    bleScanInkbird();
    Serial.print("Temp apres scan: ");
    Serial.print(temperature);
    Serial.print("C Hum: ");
    Serial.println(humidity);
    // Display-only: temp/humidity received via MQTT from Hub
    // Rafraichir ecran
    if (currentScreen == SCREEN_MAIN && !menuOpen) drawTempCard();
  }

  // REMOVED: ultrasonic reading (Hub handles bassin 1 sensor via MQTT)

  // REMOVED: pulse simulator (Hub handles sensors)

  // REMOVED: local dompeur cycle processing (Hub handles and publishes via MQTT)

  // Dompeur reset is now handled by Hub via MQTT

  // Dompeur removed - basin 4 added
  // REMOVED: local dompeur MQTT live publishing (Hub publishes dompeur/live)

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
      case SCREEN_PIN:
        handlePinTouch(sx, sy);
        break;
      case SCREEN_CALIB:
        handleCalibTouch(sx, sy);
        break;
      default:
        break;
    }
  }

  wasTouched = touched;
  delay(30);
}
