#include <Arduino.h>
#include <WiFi.h>
#include <Preferences.h>
#include <PubSubClient.h>
#include <NimBLEDevice.h>

// ========== CONFIGURATION ==========
String SHARED_DEVICE_ID = "";

// ========== GPIO ==========
#define DOMPEUR_PIN   5
#define US1_TRIG     13
#define US1_ECHO     14
#define VACUUM_PIN    4

// ========== MQTT ==========
WiFiClient mqttWifi;
PubSubClient mqtt(mqttWifi);
const char* MQTT_BROKER = "broker.hivemq.com";
const int MQTT_PORT = 1883;
unsigned long lastMqttRetry = 0;

String deviceId;
String mqttTopicState, mqttTopicCmd, mqttTopicDompeur, mqttTopicDompeurLive;
String mqttTopicTemp, mqttTopicHumidity;
String mqttTopicBasin1, mqttTopicBasin2, mqttTopicBasin3;
String mqttTopicCal;

Preferences prefs;

// ========== DOMPEUR ==========
volatile unsigned long lsLastEdge = 0;
volatile unsigned long lsCycleMs = 0;
volatile bool lsNewCycle = false;

String dompeurTime = "--:--";
bool dompeurReset = false;
#define DOMPEUR_ALERT_MS  (15UL * 60 * 1000)
#define DOMPEUR_RESET_MS  (30UL * 60 * 1000)

// Dompeur: software debounce with stable state detection
// Only count a transition when the pin stays stable for STABLE_MS
volatile unsigned long lastChange = 0;    // last raw edge timestamp
volatile bool lastStableState = true;     // last confirmed stable state (HIGH = pullup)
volatile bool pendingState = true;        // state we're waiting to confirm
#define STABLE_MS 500  // pin must be stable 500ms to confirm transition

// ISR just records raw edges
void IRAM_ATTR limitSwitchISR() {
  lastChange = millis();
  pendingState = digitalRead(DOMPEUR_PIN);
}


// ========== SENSOR DATA ==========
float temperature = 0.0;
float humidity = 0.0;
int bleBattery = -1;
int basin1 = 0, basin2 = 0, basin3 = 0;
int rawBasin[4] = {0, 0, 0, 0};
// Calibration 1-point offset (from dashboard)
float calRefRaw[4]    = {-1, -1, -1, -1};  // raw cm at calibration time
float calRefInches[4] = {-1, -1, -1, -1};   // actual inches at calibration time
float basinMax[4]     = {0, 0, 0, 0};        // max depth inches (for % calc)

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

// ========== ULTRASONIC ==========
unsigned long lastUltrasonicRead = 0;
const unsigned long US_INTERVAL = 500;

long readUltrasonic4Wire(int trigPin, int echoPin) {
  digitalWrite(trigPin, LOW);
  delayMicroseconds(2);
  digitalWrite(trigPin, HIGH);
  delayMicroseconds(20);
  digitalWrite(trigPin, LOW);
  long duration = pulseIn(echoPin, HIGH, 30000);
  if (duration == 0) return -1;
  return duration / 58;
}

float rawToInches(int idx, float currentRaw) {
  if (calRefRaw[idx] < 0 || calRefInches[idx] < 0) return -1;
  float deltaRaw = calRefRaw[idx] - currentRaw;
  float deltaInches = deltaRaw / 2.54;
  return calRefInches[idx] + deltaInches;
}

int distanceToPercent(long distCm, int idx) {
  if (distCm < 0) return -1;
  rawBasin[idx] = (int)distCm;
  float inches = rawToInches(idx, (float)distCm);
  if (inches >= 0 && basinMax[idx] > 0) {
    int pct = (int)(inches / basinMax[idx] * 100.0);
    return constrain(pct, 0, 100);
  }
  return 0;
}

// ========== BLE ==========
bool bleInitDone = false;
unsigned long lastBleScan = 0;
const unsigned long BLE_SCAN_INTERVAL = 20000;
bool vacuumOn = false;

// ========== BLE SCAN CALLBACK ==========
class HubScanCallback : public NimBLEAdvertisedDeviceCallbacks {
  void onResult(NimBLEAdvertisedDevice* device) {
    String name = device->getName().c_str();

    // CBM (capteur_bassins): bassin 2+3
    if (name == "CBM" && device->haveManufacturerData()) {
      std::string mfr = device->getManufacturerData();
      if (mfr.size() >= 7 && (uint8_t)mfr[2] == 0xCB) {
        uint16_t d2 = (uint8_t)mfr[3] | ((uint8_t)mfr[4] << 8);
        uint16_t d3 = (uint8_t)mfr[5] | ((uint8_t)mfr[6] << 8);
        rawBasin[1] = d2;
        rawBasin[2] = d3;
        float in2 = rawToInches(1, (float)d2);
        float in3 = rawToInches(2, (float)d3);
        if (in2 >= 0 && basinMax[1] > 0)
          basin2 = constrain((int)(in2 / basinMax[1] * 100.0), 0, 100);
        if (in3 >= 0 && basinMax[2] > 0)
          basin3 = constrain((int)(in3 / basinMax[2] * 100.0), 0, 100);
        Serial.printf(">>> BLE CBM: B2=%dcm(%d%%) B3=%dcm(%d%%)\n", d2, basin2, d3, basin3);
        if (mqtt.connected()) {
          mqtt.publish(mqttTopicBasin2.c_str(), String(basin2).c_str(), true);
          mqtt.publish(mqttTopicBasin3.c_str(), String(basin3).c_str(), true);
          String raw2 = "cyd/" + deviceId + "/basin2/raw";
          String raw3 = "cyd/" + deviceId + "/basin3/raw";
          mqtt.publish(raw2.c_str(), String(rawBasin[1]).c_str(), true);
          mqtt.publish(raw3.c_str(), String(rawBasin[2]).c_str(), true);
        }
      }
    }

    // Inkbird IBS-TH2: temperature + humidity
    if ((name == "sps" || name == "iBBQ" || name.startsWith("Inkbird") || name.startsWith("IBS"))
        && device->haveManufacturerData()) {
      std::string mfr = device->getManufacturerData();
      if (mfr.size() >= 9) {
        // Debug: print raw bytes
        Serial.printf(">>> Inkbird raw (%d bytes): ", (int)mfr.size());
        for (int i = 0; i < (int)mfr.size() && i < 12; i++)
          Serial.printf("%02X ", (uint8_t)mfr[i]);
        Serial.println();

        // NimBLE strips company ID — temp at [0-1], hum at [2-3]
        int16_t rawTemp = (uint8_t)mfr[0] | ((uint8_t)mfr[1] << 8);
        int16_t rawHum  = (uint8_t)mfr[2] | ((uint8_t)mfr[3] << 8);
        float t = rawTemp / 100.0;
        float h = rawHum / 100.0;
        Serial.printf(">>> Inkbird parsed: rawT=%d(%.1fC) rawH=%d(%.1f%%)\n", rawTemp, t, rawHum, h);
        if (t >= -40 && t <= 80 && h >= 0 && h <= 100) {
          temperature = t;
          humidity = h;
        }
        if (mfr.size() >= 8) {
          int bat = (uint8_t)mfr[7];  // battery at byte 7
          if (bat >= 0 && bat <= 100) bleBattery = bat;
        }
      }
    }
  }
};

// ========== BLE ADVERTISE (CBM-HUB) ==========
void updateBleAdvertising() {
  NimBLEAdvertising* pAdv = NimBLEDevice::getAdvertising();
  pAdv->stop();

  unsigned long elapsed = (lsLastEdge > 0) ? (millis() - lsLastEdge) : 0;
  uint16_t dmpSec = elapsed / 1000;
  uint8_t flags = 0;
  if (elapsed >= DOMPEUR_ALERT_MS && !dompeurReset) flags |= 0x01;
  if (dompeurReset) flags |= 0x02;

  int16_t tempX10 = (int16_t)(temperature * 10);
  uint8_t hum = (uint8_t)constrain((int)humidity, 0, 100);

  // Payload: magic(1) + dmpSec(2) + b1(1) + b2(1) + b3(1) + tempX10(2) + hum(1) + flags(1)
  uint8_t mfrData[12];
  mfrData[0] = 0xFF;
  mfrData[1] = 0xFF;
  mfrData[2] = 0xCA;
  mfrData[3] = dmpSec & 0xFF;
  mfrData[4] = (dmpSec >> 8) & 0xFF;
  mfrData[5] = (uint8_t)constrain(basin1, 0, 255);
  mfrData[6] = (uint8_t)constrain(basin2, 0, 255);
  mfrData[7] = (uint8_t)constrain(basin3, 0, 255);
  mfrData[8] = tempX10 & 0xFF;
  mfrData[9] = (tempX10 >> 8) & 0xFF;
  mfrData[10] = hum;
  mfrData[11] = flags;

  NimBLEAdvertisementData advData;
  advData.setName("CBM-HUB");
  advData.setManufacturerData(std::string((char*)mfrData, 12));
  pAdv->setAdvertisementData(advData);
  pAdv->start();
}

void bleInit() {
  NimBLEDevice::init("HUB");
  NimBLEDevice::setPower(ESP_PWR_LVL_P3);
  NimBLEScan* pScan = NimBLEDevice::getScan();
  pScan->setAdvertisedDeviceCallbacks(new HubScanCallback(), true);
  pScan->setActiveScan(true);
  pScan->setInterval(100);
  pScan->setWindow(99);
  bleInitDone = true;
  Serial.println("BLE NimBLE init OK");
}

void bleScan() {
  if (!bleInitDone) return;
  Serial.println("BLE: scanning 10s...");
  NimBLEScan* pScan = NimBLEDevice::getScan();
  pScan->start(10, false);
  Serial.printf("BLE: scan done, found %d devices\n", pScan->getResults().getCount());
  pScan->clearResults();
}

// ========== MQTT CALLBACK ==========
void mqttCallback(char* topic, byte* payload, unsigned int length) {
  String msg;
  for (unsigned int i = 0; i < length; i++) msg += (char)payload[i];
  String t = String(topic);
  Serial.printf("MQTT recv [%s]: %s\n", topic, msg.c_str());

  // Vacuum command from CYD
  if (t == mqttTopicCmd) {
    if (msg == "toggle") vacuumOn = !vacuumOn;
    else if (msg == "on" || msg == "1") vacuumOn = true;
    else if (msg == "off" || msg == "0") vacuumOn = false;
    digitalWrite(VACUUM_PIN, vacuumOn ? HIGH : LOW);
    mqtt.publish(mqttTopicState.c_str(), vacuumOn ? "1" : "0", true);
    Serial.printf("Vacuum: %s\n", vacuumOn ? "ON" : "OFF");
  }

  // Basin calibration data from dashboard (basin1/cal .. basin4/cal)
  for (int bn = 1; bn <= 4; bn++) {
    String calTopic = "cyd/" + deviceId + "/basin" + String(bn) + "/cal";
    if (t == calTopic) {
      int idx = bn - 1;
      // Parse {"refRaw":XX,"refInches":YY}
      int rr = msg.indexOf("\"refRaw\":");
      int ri = msg.indexOf("\"refInches\":");
      if (rr >= 0 && ri >= 0) {
        calRefRaw[idx] = msg.substring(rr + 9).toFloat();
        calRefInches[idx] = msg.substring(ri + 12).toFloat();
        prefs.begin("cal", false);
        prefs.putFloat(("rr" + String(idx)).c_str(), calRefRaw[idx]);
        prefs.putFloat(("ri" + String(idx)).c_str(), calRefInches[idx]);
        prefs.end();
        Serial.printf("Cal B%d: refRaw=%.1f refInches=%.1f\n", bn, calRefRaw[idx], calRefInches[idx]);
      }
    }
  }

  // Basin max depth from dashboard (settings/bmax)
  String bmaxTopic = "cyd/" + deviceId + "/settings/bmax";
  if (t == bmaxTopic) {
    // Parse {"1":XX,"2":YY,"3":ZZ,"4":WW}
    for (int bn = 1; bn <= 4; bn++) {
      String key = "\"" + String(bn) + "\":";
      int pos = msg.indexOf(key);
      if (pos >= 0) {
        basinMax[bn - 1] = msg.substring(pos + key.length()).toFloat();
      }
    }
    prefs.begin("cal", false);
    for (int i = 0; i < 4; i++)
      prefs.putFloat(("mx" + String(i)).c_str(), basinMax[i]);
    prefs.end();
    Serial.printf("BasinMax: %.0f %.0f %.0f %.0f\n", basinMax[0], basinMax[1], basinMax[2], basinMax[3]);
  }
}

void mqttReconnect() {
  if (WiFi.status() != WL_CONNECTED) return;
  if (mqtt.connected()) return;
  if (millis() - lastMqttRetry < 5000) return;
  lastMqttRetry = millis();
  String clientId = "hub-" + deviceId + "-" + String(random(1000));
  Serial.printf("MQTT: connecting as %s...\n", clientId.c_str());
  if (mqtt.connect(clientId.c_str())) {
    Serial.println("MQTT: connected!");
    mqtt.subscribe(mqttTopicCmd.c_str());
    for (int bn = 1; bn <= 4; bn++) {
      String ct = "cyd/" + deviceId + "/basin" + String(bn) + "/cal";
      mqtt.subscribe(ct.c_str());
    }
    String bmaxSub = "cyd/" + deviceId + "/settings/bmax";
    mqtt.subscribe(bmaxSub.c_str());
    mqtt.publish(mqttTopicState.c_str(), vacuumOn ? "1" : "0", true);
  } else {
    Serial.printf("MQTT: failed (rc=%d)\n", mqtt.state());
  }
}

void updateDompeurTime(unsigned long ms) {
  unsigned long sec = ms / 1000;
  char buf[8];
  snprintf(buf, sizeof(buf), "%02lu:%02lu", sec / 60, sec % 60);
  dompeurTime = String(buf);
  addDompeurPoint((int)sec);
  Serial.printf("Dompeur cycle: %s (%lu ms)\n", buf, ms);
  if (mqtt.connected())
    mqtt.publish(mqttTopicDompeur.c_str(), dompeurTime.c_str(), true);
}

void publishAll() {
  if (!mqtt.connected()) return;
  mqtt.publish(mqttTopicState.c_str(), vacuumOn ? "1" : "0", true);
  mqtt.publish(mqttTopicDompeur.c_str(), dompeurTime.c_str(), true);
  mqtt.publish(mqttTopicTemp.c_str(), String(temperature, 1).c_str(), true);
  mqtt.publish(mqttTopicHumidity.c_str(), String(humidity, 1).c_str(), true);
  mqtt.publish(mqttTopicBasin1.c_str(), String(basin1).c_str(), true);
  mqtt.publish(mqttTopicBasin2.c_str(), String(basin2).c_str(), true);
  mqtt.publish(mqttTopicBasin3.c_str(), String(basin3).c_str(), true);
}

void checkSerialCommands() {
  if (!Serial.available()) return;
  String line = Serial.readStringUntil('\n');
  line.trim();
  if (line.startsWith("SSID:")) {
    prefs.begin("wifi", false);
    prefs.putString("ssid", line.substring(5));
    prefs.end();
    Serial.printf("WiFi SSID saved: %s\n", line.substring(5).c_str());
  } else if (line.startsWith("PASS:")) {
    prefs.begin("wifi", false);
    prefs.putString("pass", line.substring(5));
    prefs.end();
    Serial.println("WiFi password saved. Type RESTART to apply");
  } else if (line.startsWith("ID:")) {
    prefs.begin("mqtt", false);
    prefs.putString("devid", line.substring(3));
    prefs.end();
    Serial.printf("Device ID saved: %s (restart to apply)\n", line.substring(3).c_str());
  } else if (line == "RESTART") {
    ESP.restart();
  } else if (line == "STATUS") {
    Serial.printf("WiFi: %s  IP: %s\nMQTT: %s\nDeviceId: %s\n",
      WiFi.status() == WL_CONNECTED ? "OK" : "DISCONNECTED",
      WiFi.localIP().toString().c_str(),
      mqtt.connected() ? "OK" : "DISCONNECTED",
      deviceId.c_str());
    Serial.printf("Dompeur: %s  B1:%d%%  B2:%d%%  B3:%d%%\n", dompeurTime.c_str(), basin1, basin2, basin3);
    Serial.printf("Temp: %.1fC  Hum: %.1f%%  Vacuum: %s\n", temperature, humidity, vacuumOn ? "ON" : "OFF");
  }
}

// ========== SETUP ==========
void setup() {
  Serial.begin(115200);
  delay(100);
  Serial.println("\n=== WROOM Hub - Cabane Marcoux ===");

  pinMode(DOMPEUR_PIN, INPUT_PULLUP);
  attachInterrupt(digitalPinToInterrupt(DOMPEUR_PIN), limitSwitchISR, CHANGE);
  pinMode(US1_TRIG, OUTPUT);
  pinMode(US1_ECHO, INPUT);
  pinMode(VACUUM_PIN, OUTPUT);
  digitalWrite(VACUUM_PIN, LOW);

  // Load calibration (1-point offset + max)
  prefs.begin("cal", true);
  for (int i = 0; i < 4; i++) {
    calRefRaw[i]    = prefs.getFloat(("rr" + String(i)).c_str(), -1);
    calRefInches[i] = prefs.getFloat(("ri" + String(i)).c_str(), -1);
    basinMax[i]     = prefs.getFloat(("mx" + String(i)).c_str(), 0);
  }
  prefs.end();

  // Device ID
  prefs.begin("mqtt", true);
  String savedId = prefs.getString("devid", "");
  prefs.end();
  if (savedId.length() > 0) deviceId = savedId;
  else if (SHARED_DEVICE_ID.length() > 0) deviceId = SHARED_DEVICE_ID;
  else {
    uint8_t mac[6]; WiFi.macAddress(mac);
    char idBuf[7];
    snprintf(idBuf, sizeof(idBuf), "%02x%02x%02x", mac[3], mac[4], mac[5]);
    deviceId = String(idBuf);
  }

  // MQTT topics (identical to CYD)
  mqttTopicState       = "cyd/" + deviceId + "/state";
  mqttTopicCmd         = "cyd/" + deviceId + "/cmd";
  mqttTopicDompeur     = "cyd/" + deviceId + "/dompeur";
  mqttTopicDompeurLive = "cyd/" + deviceId + "/dompeur/live";
  mqttTopicTemp        = "cyd/" + deviceId + "/temp";
  mqttTopicHumidity    = "cyd/" + deviceId + "/humidity";
  mqttTopicBasin1      = "cyd/" + deviceId + "/basin1";
  mqttTopicBasin2      = "cyd/" + deviceId + "/basin2";
  mqttTopicBasin3      = "cyd/" + deviceId + "/basin3";
  mqttTopicCal         = "cyd/" + deviceId + "/cmd/cal";
  Serial.printf("Device ID: %s\n", deviceId.c_str());

  // BLE init BEFORE WiFi (required — BLE controller must init first)
  bleInit();
  updateBleAdvertising();

  // WiFi
  WiFi.mode(WIFI_STA);
  prefs.begin("wifi", true);
  String ssid = prefs.getString("ssid", "Cabane_Marcoux");
  String pass = prefs.getString("pass", "Cabane2025");
  prefs.end();

  Serial.printf("WiFi: connecting to '%s'...\n", ssid.c_str());
  WiFi.begin(ssid.c_str(), pass.c_str());
  int tries = 0;
  while (WiFi.status() != WL_CONNECTED && tries < 20) { delay(500); Serial.print("."); tries++; }
  if (WiFi.status() == WL_CONNECTED)
    Serial.printf("\nWiFi connected! IP: %s\n", WiFi.localIP().toString().c_str());
  else
    Serial.println("\nWiFi failed - will retry in loop");

  // MQTT
  mqtt.setServer(MQTT_BROKER, MQTT_PORT);
  mqtt.setCallback(mqttCallback);
  mqtt.setBufferSize(512);

  Serial.println("=== WROOM Hub ready ===");
  Serial.println("Commands: SSID:xxx  PASS:xxx  ID:xxx  RESTART  STATUS");
  memset(dompeurHist, 0, sizeof(dompeurHist));
}

// ========== LOOP ==========
unsigned long lastWifiRetry = 0;
unsigned long lastDompeurMqtt = 0;
unsigned long lastBleAdv = 0;

void loop() {
  // WiFi reconnect
  if (WiFi.status() != WL_CONNECTED) {
    if (millis() - lastWifiRetry >= 30000) {
      lastWifiRetry = millis();
      prefs.begin("wifi", true);
      String ssid = prefs.getString("ssid", "Cabane_Marcoux");
      String pass = prefs.getString("pass", "Cabane2025");
      prefs.end();
      WiFi.begin(ssid.c_str(), pass.c_str());
    }
  } else {
    mqttReconnect();
    if (mqtt.connected()) mqtt.loop();
  }

  checkSerialCommands();

  // BLE scan every 20s
  if (millis() - lastBleScan >= BLE_SCAN_INTERVAL) {
    lastBleScan = millis();
    bleScan();
    if (mqtt.connected()) {
      mqtt.publish(mqttTopicTemp.c_str(), String(temperature, 1).c_str(), true);
      mqtt.publish(mqttTopicHumidity.c_str(), String(humidity, 1).c_str(), true);
    }
  }

  // Bassin 1 ultrasonic every 500ms
  if (millis() - lastUltrasonicRead >= US_INTERVAL) {
    lastUltrasonicRead = millis();
    long d1 = readUltrasonic4Wire(US1_TRIG, US1_ECHO);
    int p1 = distanceToPercent(d1, 0);
    if (p1 >= 0 && p1 != basin1) {
      basin1 = p1;
      Serial.printf("Bassin 1: %dcm = %d%%\n", (int)d1, basin1);
      if (mqtt.connected()) {
        mqtt.publish(mqttTopicBasin1.c_str(), String(basin1).c_str(), true);
        String rawTopic = "cyd/" + deviceId + "/basin1/raw";
        mqtt.publish(rawTopic.c_str(), String(rawBasin[0]).c_str(), true);
      }
    }
  }

  // Dompeur: check stable state transition (software debounce)
  if (lastChange > 0 && (millis() - lastChange) >= STABLE_MS) {
    bool currentPin = digitalRead(DOMPEUR_PIN);
    if (currentPin == pendingState && currentPin != lastStableState) {
      // State changed and stable for 500ms — real transition
      lastStableState = currentPin;
      unsigned long now = millis();
      if (lsLastEdge > 0) {
        unsigned long delta = now - lsLastEdge;
        if (delta >= 20000) {  // minimum 20s between real cycles
          lsCycleMs = delta;
          dompeurReset = false;
          updateDompeurTime(lsCycleMs);
        }
      }
      lsLastEdge = now;
      lastChange = 0;  // reset
    } else if (currentPin != pendingState) {
      // Pin bounced back — not stable, ignore
      lastChange = 0;
    }
  }

  // Dompeur: reset after 30 min
  if (!dompeurReset && lsLastEdge > 0 && (millis() - lsLastEdge) >= DOMPEUR_RESET_MS) {
    dompeurReset = true;
    dompeurTime = "--:--";
    graphCount = 0;
    memset(dompeurHist, 0, sizeof(dompeurHist));
    if (mqtt.connected()) {
      mqtt.publish(mqttTopicDompeur.c_str(), "--:--", true);
      mqtt.publish(mqttTopicDompeurLive.c_str(), "--:--", true);
    }
    Serial.println("Dompeur: RESET (30 min)");
  }

  // Dompeur: publish live counter every second (always retained)
  if (mqtt.connected() && millis() - lastDompeurMqtt >= 1000) {
    lastDompeurMqtt = millis();
    if (!dompeurReset && lsLastEdge > 0) {
      unsigned long sec = (millis() - lsLastEdge) / 1000;
      char liveBuf[8];
      snprintf(liveBuf, sizeof(liveBuf), "%02lu:%02lu", sec / 60, sec % 60);
      mqtt.publish(mqttTopicDompeurLive.c_str(), liveBuf, true);
    } else {
      mqtt.publish(mqttTopicDompeurLive.c_str(), "--:--", true);
    }
  }

  // BLE advertise update every 2s
  if (millis() - lastBleAdv >= 2000) {
    lastBleAdv = millis();
    updateBleAdvertising();
  }

  delay(10);
}
