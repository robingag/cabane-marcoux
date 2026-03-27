#include <Arduino.h>
#include <WiFi.h>
#include <WebServer.h>
#include <Preferences.h>
#include <PubSubClient.h>
#include <NimBLEDevice.h>

WebServer server(80);

// ========== CONFIGURATION ==========
String SHARED_DEVICE_ID = "";

// ========== GPIO ==========
#define DOMPEUR_PIN   5
#define US1_TRIG     18
#define US1_ECHO     19
#define US2_TRIG     27
#define US2_ECHO     33
#define VACUUM_PIN    4
#define LED_PIN       2   // onboard blue LED

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
String mqttTopicBmax;

Preferences prefs;

// ========== DOMPEUR ==========
volatile unsigned long lsLastEdge = 0;
volatile unsigned long lsCycleMs = 0;
volatile bool lsNewCycle = false;

String dompeurTime = "--:--";
bool dompeurReset = false;
#define DOMPEUR_ALERT_MS  (15UL * 60 * 1000)
#define DOMPEUR_RESET_MS  (30UL * 60 * 1000)

// Dompeur: stable-state filter (replaces fixed debounce)
// A transition is only accepted when the pin stays stable for STABLE_TIME_MS
// If the pin bounces back before the timer completes, the timer resets
volatile unsigned long stableStart = 0;     // when the pending state started
volatile bool lastStableState = true;       // last confirmed stable state (HIGH = pullup)
volatile bool pendingState = true;          // state we're waiting to confirm
volatile bool stableTimerActive = false;    // is the timer running?
#define STABLE_TIME_MS 80  // pin must stay stable 80ms consecutive to validate

// ISR records every edge and resets the stable timer
void IRAM_ATTR limitSwitchISR() {
  bool pin = digitalRead(DOMPEUR_PIN);
  if (pin != pendingState) {
    // New edge detected — reset timer with new state
    pendingState = pin;
    stableStart = millis();
    stableTimerActive = true;
  }
}


// ========== SENSOR DATA ==========
float temperature = 0.0;
float humidity = 0.0;
int bleBattery = -1;
int basin1 = 0, basin2 = 0, basin3 = 0;
int rawBasin[3] = {0, 0, 0};

// Calibration 1-point offset (matches dashboard)
// refRaw = raw cm at calibration, refInches = known depth in inches
// currentInches = refInches + (refRaw - currentRaw) / 2.54
// percent = currentInches / maxInches * 100
float calRefRaw[3]    = {-1, -1, -1};
float calRefInches[3] = {-1, -1, -1};
float basinMax[3]     = {0, 0, 0};  // max depth in inches per basin

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
  delayMicroseconds(5);
  digitalWrite(trigPin, HIGH);
  delayMicroseconds(50);
  digitalWrite(trigPin, LOW);
  long duration = pulseIn(echoPin, HIGH, 50000);
  if (duration == 0) return -1;
  return duration / 58;
}

float rawToInches(int idx, long rawCm) {
  if (calRefRaw[idx] < 0 || calRefInches[idx] < 0) return -1;
  float deltaRaw = calRefRaw[idx] - (float)rawCm;
  float deltaInches = deltaRaw / 2.54;
  return calRefInches[idx] + deltaInches;
}

int distanceToPercent(long distCm, int idx) {
  if (distCm < 0) return -1;
  rawBasin[idx] = (int)distCm;
  if (calRefRaw[idx] < 0 || basinMax[idx] <= 0) return 0;
  float inches = rawToInches(idx, distCm);
  if (inches < 0) return 0;
  int pct = (int)((inches / basinMax[idx]) * 100.0);
  return constrain(pct, 0, 100);
}

// ========== BLE ==========
bool bleInitDone = false;
bool bleScanning = false;
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
      Serial.printf(">>> CBM raw (%d bytes): ", (int)mfr.size());
      for (int i = 0; i < (int)mfr.size() && i < 12; i++)
        Serial.printf("%02X ", (uint8_t)mfr[i]);
      Serial.println();
      if (mfr.size() >= 7 && (uint8_t)mfr[2] == 0xCB) {
        uint16_t d2 = (uint8_t)mfr[3] | ((uint8_t)mfr[4] << 8);
        uint16_t d3 = (uint8_t)mfr[5] | ((uint8_t)mfr[6] << 8);
        rawBasin[1] = d2;
        rawBasin[2] = d3;
        // 1-point offset calibration for BLE basins
        if (calRefRaw[1] >= 0 && basinMax[1] > 0) {
          float in2 = rawToInches(1, d2);
          basin2 = constrain((int)((in2 / basinMax[1]) * 100.0), 0, 100);
        }
        if (calRefRaw[2] >= 0 && basinMax[2] > 0) {
          float in3 = rawToInches(2, d3);
          basin3 = constrain((int)((in3 / basinMax[2]) * 100.0), 0, 100);
        }
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
  bleScanning = true;
  Serial.println("BLE: scanning 10s...");
  NimBLEScan* pScan = NimBLEDevice::getScan();
  pScan->start(10, false);
  Serial.printf("BLE: scan done, found %d devices\n", pScan->getResults().getCount());
  pScan->clearResults();
  bleScanning = false;
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

  // Calibration 1-point offset: {"refRaw":70,"refInches":10}
  // Matches per-basin topic: cyd/{id}/basin{n}/cal
  for (int n = 1; n <= 3; n++) {
    String calTopic = "cyd/" + deviceId + "/basin" + String(n) + "/cal";
    if (t == calTopic) {
      int idx = n - 1;
      int rr = msg.indexOf("\"refRaw\":");
      int ri = msg.indexOf("\"refInches\":");
      if (rr >= 0 && ri >= 0) {
        calRefRaw[idx] = msg.substring(rr + 9).toFloat();
        calRefInches[idx] = msg.substring(ri + 12).toFloat();
        // Save to NVS
        prefs.begin("cal", false);
        prefs.putFloat(("rr" + String(idx)).c_str(), calRefRaw[idx]);
        prefs.putFloat(("ri" + String(idx)).c_str(), calRefInches[idx]);
        prefs.end();
        Serial.printf("CAL basin%d: refRaw=%.1f refInches=%.1f (saved NVS)\n", n, calRefRaw[idx], calRefInches[idx]);
      }
    }
  }

  // Basin max depth: {"1":24,"2":30,"3":18}
  if (t == mqttTopicBmax) {
    for (int n = 1; n <= 3; n++) {
      String key = "\"" + String(n) + "\":";
      int pos = msg.indexOf(key);
      if (pos >= 0) {
        basinMax[n - 1] = msg.substring(pos + key.length()).toFloat();
      }
    }
    prefs.begin("cal", false);
    for (int i = 0; i < 3; i++)
      prefs.putFloat(("mx" + String(i)).c_str(), basinMax[i]);
    prefs.end();
    Serial.printf("BMAX: B1=%.1f B2=%.1f B3=%.1f (saved NVS)\n", basinMax[0], basinMax[1], basinMax[2]);
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
    mqtt.subscribe(mqttTopicBmax.c_str());
    // Subscribe to per-basin calibration topics
    for (int n = 1; n <= 3; n++) {
      String calTopic = "cyd/" + deviceId + "/basin" + String(n) + "/cal";
      mqtt.subscribe(calTopic.c_str());
    }
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
  // Retained: broker stores latest for new subscribers / F5
  mqtt.publish(mqttTopicState.c_str(), vacuumOn ? "1" : "0", true);
  mqtt.publish(mqttTopicDompeur.c_str(), dompeurTime.c_str(), true);
  mqtt.publish(mqttTopicTemp.c_str(), String(temperature, 1).c_str(), true);
  mqtt.publish(mqttTopicHumidity.c_str(), String(humidity, 1).c_str(), true);
  mqtt.publish(mqttTopicBasin1.c_str(), String(basin1).c_str(), true);
  mqtt.publish(mqttTopicBasin2.c_str(), String(basin2).c_str(), true);
  mqtt.publish(mqttTopicBasin3.c_str(), String(basin3).c_str(), true);
  String r1 = "cyd/" + deviceId + "/basin1/raw";
  String r2 = "cyd/" + deviceId + "/basin2/raw";
  String r3 = "cyd/" + deviceId + "/basin3/raw";
  mqtt.publish(r1.c_str(), String(rawBasin[0]).c_str(), true);
  mqtt.publish(r2.c_str(), String(rawBasin[1]).c_str(), true);
  mqtt.publish(r3.c_str(), String(rawBasin[2]).c_str(), true);
  // Live topic: always delivered (no retain), dashboard subscribes to this
  String live = "cyd/" + deviceId + "/live";
  char buf[128];
  snprintf(buf, sizeof(buf), "%d|%d|%d|%d|%d|%d|%.1f|%.1f",
    basin1, basin2, basin3, rawBasin[0], rawBasin[1], rawBasin[2],
    temperature, humidity);
  mqtt.publish(live.c_str(), buf, false);
}

// ========== WEB SERVER ==========
const char DASHBOARD[] PROGMEM = R"rawliteral(<!DOCTYPE html>
<html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="apple-mobile-web-app-capable" content="yes"><meta name="theme-color" content="#080a0e">
<title>Cabane Marcoux</title><style>
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:'Segoe UI',system-ui,sans-serif;background:#080a0e;color:#c8d4e0;text-align:center;min-height:100vh}
.hdr{padding:12px;background:#0d1117;border-bottom:1px solid #1a2030}
h1{font-size:18px;color:#f0b429}
.st{font-size:10px;margin-top:4px}
.st.ok{color:#4ade80}.st.er{color:#f87171}
.row{display:flex;justify-content:center;gap:10px;padding:10px;flex-wrap:wrap}
.tank{background:#111820;border-radius:12px;padding:10px;width:80px;text-align:center}
.nl{font-size:10px;color:#64748b;margin-bottom:4px}
.tb{position:relative;width:50px;height:120px;margin:0 auto;background:#1a2030;border-radius:8px;overflow:hidden;border:1px solid #2a3040}
.tf{position:absolute;bottom:0;width:100%;transition:height 0.3s;border-radius:0 0 7px 7px}
.tf.l{background:linear-gradient(to top,#2563eb,#3b82f6)}.tf.m{background:linear-gradient(to top,#f59e0b,#fbbf24)}.tf.h{background:linear-gradient(to top,#dc2626,#ef4444)}
.bp{font-size:14px;font-weight:bold;margin-top:6px}
.raw{font-size:9px;color:#64748b}
.info{display:flex;justify-content:center;gap:20px;padding:8px;background:#0d1117;margin:8px;border-radius:8px}
.big{font-size:28px;font-weight:bold;color:#f0b429}
.lbl{font-size:10px;color:#64748b}
.dmp{background:#0d1117;margin:8px;padding:10px;border-radius:8px}
.dmp .v{font-size:20px;color:#4ade80;font-weight:bold}
</style></head><body>
<div class="hdr"><h1>Cabane Marcoux</h1><div class="st" id="st">Connexion...</div></div>
<div class="row">
<div class="tank"><div class="nl" id="n1">Bassin 1</div><div class="tb"><div class="tf l" id="f1" style="height:0%"></div></div><div class="bp" id="p1">--</div><div class="raw" id="w1">--</div></div>
<div class="tank"><div class="nl" id="n2">Bassin 2</div><div class="tb"><div class="tf l" id="f2" style="height:0%"></div></div><div class="bp" id="p2">--</div><div class="raw" id="w2">--</div></div>
<div class="tank"><div class="nl" id="n3">Bassin 3</div><div class="tb"><div class="tf l" id="f3" style="height:0%"></div></div><div class="bp" id="p3">--</div><div class="raw" id="w3">--</div></div>
</div>
<div class="info">
<div><div class="big" id="tmp">--</div><div class="lbl">Temperature</div></div>
<div><div class="big" id="hum" style="font-size:18px">--</div><div class="lbl">Humidite</div></div>
</div>
<div class="dmp"><div class="lbl">Dompeur</div><div class="v" id="dmp">--:--</div></div>
<script>
function up(i,pct,raw){
  var f=document.getElementById("f"+i);
  f.style.height=pct+"%";
  f.className="tf "+(pct>=91?"h":pct>=61?"m":"l");
  document.getElementById("p"+i).textContent=pct+"%";
  document.getElementById("w"+i).textContent=raw+"cm";
}
function poll(){
  fetch("/api").then(function(r){return r.json()}).then(function(d){
    up(1,d.b1,d.r1);up(2,d.b2,d.r2);up(3,d.b3,d.r3);
    document.getElementById("tmp").textContent=d.t+"\u00B0C";
    document.getElementById("hum").textContent=d.h+"%";
    document.getElementById("dmp").textContent=d.dmp;
    document.getElementById("st").textContent="Live";
    document.getElementById("st").className="st ok";
  }).catch(function(){
    document.getElementById("st").textContent="Hors ligne";
    document.getElementById("st").className="st er";
  });
}
setInterval(poll,500);poll();
</script></body></html>)rawliteral";

void handleRoot() {
  server.send_P(200, "text/html", DASHBOARD);
}

void handleApi() {
  char json[256];
  snprintf(json, sizeof(json),
    "{\"b1\":%d,\"b2\":%d,\"b3\":%d,\"r1\":%d,\"r2\":%d,\"r3\":%d,"
    "\"t\":%.1f,\"h\":%.1f,\"vac\":%d,\"dmp\":\"%s\"}",
    basin1, basin2, basin3, rawBasin[0], rawBasin[1], rawBasin[2],
    temperature, humidity, vacuumOn ? 1 : 0, dompeurTime.c_str());
  server.sendHeader("Access-Control-Allow-Origin", "*");
  server.send(200, "application/json", json);
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

  pinMode(LED_PIN, OUTPUT);
  pinMode(DOMPEUR_PIN, INPUT_PULLUP);
  attachInterrupt(digitalPinToInterrupt(DOMPEUR_PIN), limitSwitchISR, CHANGE);
  pinMode(US1_TRIG, OUTPUT);
  digitalWrite(US1_TRIG, LOW);
  pinMode(US1_ECHO, INPUT);
  pinMode(US2_TRIG, OUTPUT);
  digitalWrite(US2_TRIG, LOW);
  pinMode(US2_ECHO, INPUT);
  pinMode(VACUUM_PIN, OUTPUT);
  digitalWrite(VACUUM_PIN, LOW);

  // Load calibration (1-point offset + max depth)
  prefs.begin("cal", true);
  for (int i = 0; i < 3; i++) {
    calRefRaw[i]    = prefs.getFloat(("rr" + String(i)).c_str(), -1);
    calRefInches[i] = prefs.getFloat(("ri" + String(i)).c_str(), -1);
    basinMax[i]     = prefs.getFloat(("mx" + String(i)).c_str(), 0);
  }
  prefs.end();
  Serial.printf("CAL loaded: B1(ref=%.0f/%.1fpo max=%.1f) B2(ref=%.0f/%.1fpo max=%.1f) B3(ref=%.0f/%.1fpo max=%.1f)\n",
    calRefRaw[0], calRefInches[0], basinMax[0],
    calRefRaw[1], calRefInches[1], basinMax[1],
    calRefRaw[2], calRefInches[2], basinMax[2]);

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
  mqttTopicBmax        = "cyd/" + deviceId + "/settings/bmax";
  Serial.printf("Device ID: %s\n", deviceId.c_str());

  // BLE init BEFORE WiFi
  bleInit();

  // WiFi
  WiFi.mode(WIFI_STA);
  prefs.begin("wifi", true);
  String ssid = prefs.getString("ssid", "HELIX-0277_EXT");
  String pass = prefs.getString("pass", "robingag");
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

  // Web server
  server.on("/", handleRoot);
  server.on("/api", handleApi);
  server.begin();
  Serial.println("Web server started on port 80");

  Serial.println("=== WROOM Hub ready ===");
  Serial.println("Commands: SSID:xxx  PASS:xxx  ID:xxx  RESTART  STATUS");
  memset(dompeurHist, 0, sizeof(dompeurHist));
}

// ========== LOOP ==========
unsigned long lastWifiRetry = 0;
unsigned long lastDompeurMqtt = 0;
unsigned long lastBleAdv = 0;
unsigned long lastPublishAll = 0;
unsigned long lastLedToggle = 0;
bool ledState = false;

void loop() {
  // WiFi reconnect
  if (WiFi.status() != WL_CONNECTED) {
    if (millis() - lastWifiRetry >= 30000) {
      lastWifiRetry = millis();
      prefs.begin("wifi", true);
      String ssid = prefs.getString("ssid", "HELIX-0277_EXT");
      String pass = prefs.getString("pass", "robingag");
      prefs.end();
      WiFi.begin(ssid.c_str(), pass.c_str());
    }
  } else {
    mqttReconnect();
    if (mqtt.connected()) mqtt.loop();
  }

  checkSerialCommands();
  server.handleClient();

  // BLE scan every 20s
  if (millis() - lastBleScan >= BLE_SCAN_INTERVAL) {
    lastBleScan = millis();
    bleScan();
  }

  // Bassin 1 ultrasonic every 500ms
  if (millis() - lastUltrasonicRead >= US_INTERVAL) {
    lastUltrasonicRead = millis();
    long d1 = readUltrasonic4Wire(US1_TRIG, US1_ECHO);
    long d2 = readUltrasonic4Wire(US2_TRIG, US2_ECHO);
    Serial.printf("US1: %dcm  US2: %dcm\n", (int)d1, (int)d2);
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
    int p2 = distanceToPercent(d2, 1);
    if (p2 >= 0 && p2 != basin2) {
      basin2 = p2;
      Serial.printf("Bassin 2: %dcm = %d%%\n", (int)d2, basin2);
      if (mqtt.connected()) {
        mqtt.publish(mqttTopicBasin2.c_str(), String(basin2).c_str(), true);
        String rawTopic = "cyd/" + deviceId + "/basin2/raw";
        mqtt.publish(rawTopic.c_str(), String(rawBasin[1]).c_str(), true);
      }
    }
  }

  // Dompeur: stable-state filter — validate transition after 80ms stable
  if (stableTimerActive && (millis() - stableStart) >= STABLE_TIME_MS) {
    bool currentPin = digitalRead(DOMPEUR_PIN);
    if (currentPin == pendingState && currentPin != lastStableState) {
      // State stayed stable for 80ms — confirmed real transition
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
      stableTimerActive = false;
    } else if (currentPin != pendingState) {
      // Pin bounced back before timer completed — reset, ignore
      stableTimerActive = false;
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

  // Publish all values every 2s (live updates with retain)
  if (millis() - lastPublishAll >= 2000) {
    lastPublishAll = millis();
    publishAll();
  }

  // BLE advertise update every 2s
  if (millis() - lastBleAdv >= 2000) {
    lastBleAdv = millis();
    updateBleAdvertising();
  }

  // Blue LED status indicator
  // Slow (1s) = WiFi+MQTT OK | Fast (200ms) = connecting | Solid = no WiFi
  unsigned long ledInterval;
  if (WiFi.status() == WL_CONNECTED && mqtt.connected())
    ledInterval = 1000;
  else if (WiFi.status() == WL_CONNECTED)
    ledInterval = 500;
  else
    ledInterval = 200;

  if (millis() - lastLedToggle >= ledInterval) {
    lastLedToggle = millis();
    ledState = !ledState;
    digitalWrite(LED_PIN, ledState);
  }

  delay(10);
}
