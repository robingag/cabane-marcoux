#include <Arduino.h>
#include <WiFi.h>
#include <Preferences.h>
#include <PubSubClient.h>
#include <NimBLEDevice.h>
#include <ArduinoOTA.h>
#include <time.h>

// ========== CONFIGURATION ==========
String SHARED_DEVICE_ID = "";

// ========== GPIO ==========
#define DOMPEUR_PIN   5
#define US1_TRIG     18
#define US1_ECHO     19
#define VACUUM_PIN    4
#define LED_PIN       2   // LED bleue embarquée WROOM

// ========== MQTT ==========
WiFiClient mqttWifi;
PubSubClient mqtt(mqttWifi);
const char* MQTT_BROKER = "broker.hivemq.com";
const int MQTT_PORT = 1883;
unsigned long lastMqttRetry = 0;

String deviceId;
String mqttTopicState, mqttTopicCmd;
String mqttTopicDompeur, mqttTopicDompeurLive;
String mqttTopicDompeurNewCycle, mqttTopicDompeurElapsed;
String mqttTopicGalToday, mqttTopicGalHist;
String mqttTopicTemp, mqttTopicHumidity;
String mqttTopicBasin1, mqttTopicBasin2, mqttTopicBasin3, mqttTopicBasin4;
String mqttTopicCal;

Preferences prefs;

// ========== DOMPEUR ==========
volatile unsigned long lsLastEdge = 0;
volatile unsigned long lsCycleMs  = 0;

String dompeurTime = "--:--";
bool dompeurReset  = false;
#define DOMPEUR_ALERT_MS  (15UL * 60 * 1000)
#define DOMPEUR_RESET_MS  (30UL * 60 * 1000)

// Debounce logiciel: la broche doit rester stable 500 ms pour confirmer une transition
volatile unsigned long lastChange    = 0;
volatile bool lastStableState        = true;
volatile bool pendingState           = true;
#define STABLE_MS 500

// ISR: enregistre uniquement le timestamp du dernier front brut
void IRAM_ATTR limitSwitchISR() {
  lastChange    = millis();
  pendingState  = digitalRead(DOMPEUR_PIN);
}

// ========== GALLONS ==========
// 3 gallons par cycle, compteur persisté dans NVS (survit aux redémarrages)
int    galCycleCount = 0;   // cycles aujourd'hui
int    galToday      = 0;   // gallons pompés aujourd'hui
String galDate       = "";  // "YYYY-MM-DD" du dernier comptage
String galHist       = "[]"; // tableau JSON des journées archivées

// Retourne la date locale (EST/EDT = UTC-5 + DST) en format "YYYY-MM-DD"
// Retourne "" si NTP pas encore synchronisé (tm_year < 100 = an 2000+)
String getDateStr() {
  time_t now = time(nullptr);
  struct tm* t = localtime(&now);
  if (t->tm_year < 100) return "";
  char buf[11];
  snprintf(buf, sizeof(buf), "%04d-%02d-%02d", t->tm_year + 1900, t->tm_mon + 1, t->tm_mday);
  return String(buf);
}

// Persiste les gallons dans NVS
void saveGallons() {
  prefs.begin("gal", false);
  prefs.putInt("today",  galToday);
  prefs.putInt("cycles", galCycleCount);
  prefs.putString("date", galDate);
  prefs.putString("hist", galHist);
  prefs.end();
}

// Publie le total gallons d'aujourd'hui (retain:true)
void publishGalToday() {
  if (!mqtt.connected() || galDate == "") return;
  char buf[80];
  snprintf(buf, sizeof(buf), "{\"date\":\"%s\",\"gal\":%d,\"cycles\":%d}",
    galDate.c_str(), galToday, galCycleCount);
  mqtt.publish(mqttTopicGalToday.c_str(), buf, true);
}

// Publie l'historique journalier (retain:true)
void publishGalHist() {
  if (!mqtt.connected()) return;
  mqtt.publish(mqttTopicGalHist.c_str(), galHist.c_str(), true);
}

// Archive le jour précédent et remet les compteurs à zéro pour la nouvelle journée
void checkDayRollover() {
  String today = getDateStr();
  if (today == "" || today == galDate) return;  // NTP pas prêt, ou même jour

  // Archiver la journée précédente si elle contient des données
  if (galDate != "" && galToday > 0) {
    String entry = "{\"date\":\"" + galDate + "\",\"gal\":" + galToday + ",\"cycles\":" + galCycleCount + "}";
    if (galHist == "[]") {
      galHist = "[" + entry + "]";
    } else {
      galHist = "[" + entry + "," + galHist.substring(1);  // insérer en tête
    }
    // Limiter à 30 entrées: compter les '{' et tronquer si nécessaire
    int count = 0;
    for (int i = 0; i < (int)galHist.length(); i++)
      if (galHist[i] == '{') count++;
    if (count > 30) {
      int found = 0;
      for (int i = (int)galHist.length() - 1; i >= 0; i--) {
        if (galHist[i] == '{') {
          found++;
          if (found == 30) { galHist = "[" + galHist.substring(i); break; }
        }
      }
    }
    publishGalHist();
    Serial.printf("Rollover: %s = %d gal (%d cycles) archivé\n", galDate.c_str(), galToday, galCycleCount);
  }

  // Réinitialiser pour la nouvelle journée
  galDate       = today;
  galToday      = 0;
  galCycleCount = 0;
  saveGallons();
  publishGalToday();
  Serial.printf("Nouvelle journée: %s\n", galDate.c_str());
}

// ========== DONNÉES CAPTEURS ==========
float temperature = 0.0;
float humidity    = 0.0;
int   bleBattery  = -1;
int   basin1 = 0, basin2 = 0, basin3 = 0, basin4 = 0;
int   rawBasin[4] = {0, 0, 0, 0};

// Calibration 1-point offset (envoyée par le dashboard)
float calRefRaw[4]    = {-1, -1, -1, -1};
float calRefInches[4] = {-1, -1, -1, -1};
float basinMax[4]     = { 0,  0,  0,  0};

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

// ========== ULTRASON ==========
unsigned long lastUltrasonicRead   = 0;
const unsigned long US_INTERVAL    = 500;

long readUltrasonic4Wire(int trigPin, int echoPin) {
  digitalWrite(trigPin, LOW);
  delayMicroseconds(2);
  digitalWrite(trigPin, HIGH);
  delayMicroseconds(20);
  digitalWrite(trigPin, LOW);
  portDISABLE_INTERRUPTS();
  long duration = pulseIn(echoPin, HIGH, 30000);
  portENABLE_INTERRUPTS();
  if (duration == 0) return -1;
  return duration / 58;
}

float rawToInches(int idx, float currentRaw) {
  if (calRefRaw[idx] < 0 || calRefInches[idx] < 0) return -1;
  float deltaRaw    = calRefRaw[idx] - currentRaw;
  float deltaInches = deltaRaw / 2.54;
  return calRefInches[idx] + deltaInches;
}

int distanceToPercent(long distCm, int idx) {
  if (distCm < 0) return -1;
  rawBasin[idx] = (int)distCm;
  float inches  = rawToInches(idx, (float)distCm);
  if (inches >= 0 && basinMax[idx] > 0) {
    int pct = (int)(inches / basinMax[idx] * 100.0);
    return constrain(pct, 0, 100);
  }
  return 0;
}

// ========== BLE ==========
bool bleInitDone = false;
unsigned long lastBleScan   = 0;
unsigned long lastLedBlink  = 0;
unsigned long lastTempMqtt  = 0;
const unsigned long BLE_SCAN_INTERVAL  = 2000;   // scan BLE toutes les 2s (1s bloquant)
const unsigned long TEMP_MQTT_INTERVAL = 30000;  // publier temp/hum toutes les 30s
bool vacuumOn = false;

// Callback scan BLE: CBM (bassins 2+3) et Inkbird (température/humidité)
class HubScanCallback : public NimBLEAdvertisedDeviceCallbacks {
  void onResult(NimBLEAdvertisedDevice* device) {
    String name = device->getName().c_str();
    // CBM (capteur_bassins): bassin 2 et 3 via BLE advertising
    // Payload: FF FF CB  d2_lo d2_hi  d3_lo d3_hi
    // NOTE: bassin 4 est un appareil WiFi séparé qui publie directement sur MQTT
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
          mqtt.publish(("cyd/" + deviceId + "/basin2/raw").c_str(), String(rawBasin[1]).c_str(), true);
          mqtt.publish(("cyd/" + deviceId + "/basin3/raw").c_str(), String(rawBasin[2]).c_str(), true);
        }
      }
    }

    // Inkbird IBS-TH2: température + humidité
    if ((name == "sps" || name == "iBBQ" || name.startsWith("Inkbird") || name.startsWith("IBS"))
        && device->haveManufacturerData()) {
      std::string mfr = device->getManufacturerData();
      if (mfr.size() >= 9) {
        Serial.printf(">>> Inkbird raw (%d bytes): ", (int)mfr.size());
        for (int i = 0; i < (int)mfr.size() && i < 12; i++)
          Serial.printf("%02X ", (uint8_t)mfr[i]);
        Serial.println();
        // NimBLE retire le company ID — temp à [0-1], hum à [2-3]
        int16_t rawTemp = (uint8_t)mfr[0] | ((uint8_t)mfr[1] << 8);
        int16_t rawHum  = (uint8_t)mfr[2] | ((uint8_t)mfr[3] << 8);
        float t = rawTemp / 100.0;
        float h = rawHum  / 100.0;
        Serial.printf(">>> Inkbird: %.1fC %.1f%%\n", t, h);
        if (t >= -40 && t <= 80 && h >= 0 && h <= 100) {
          temperature = t;
          humidity    = h;
        }
        if (mfr.size() >= 8) {
          int bat = (uint8_t)mfr[7];
          if (bat >= 0 && bat <= 100) bleBattery = bat;
        }
      }
    }
  }
};

// Mettre à jour l'advertising BLE (CBM-HUB) avec l'état courant
void updateBleAdvertising() {
  NimBLEAdvertising* pAdv = NimBLEDevice::getAdvertising();
  pAdv->stop();

  unsigned long elapsed = (lsLastEdge > 0) ? (millis() - lsLastEdge) : 0;
  uint16_t dmpSec = elapsed / 1000;
  uint8_t  flags  = 0;
  if (elapsed >= DOMPEUR_ALERT_MS && !dompeurReset) flags |= 0x01;
  if (dompeurReset) flags |= 0x02;

  int16_t tempX10 = (int16_t)(temperature * 10);
  uint8_t hum     = (uint8_t)constrain((int)humidity, 0, 100);

  // Payload: magic(1) + dmpSec(2) + b1(1) + b2(1) + b3(1) + tempX10(2) + hum(1) + flags(1)
  uint8_t mfrData[12];
  mfrData[0]  = 0xFF;
  mfrData[1]  = 0xFF;
  mfrData[2]  = 0xCA;
  mfrData[3]  = dmpSec & 0xFF;
  mfrData[4]  = (dmpSec >> 8) & 0xFF;
  mfrData[5]  = (uint8_t)constrain(basin1, 0, 255);
  mfrData[6]  = (uint8_t)constrain(basin2, 0, 255);
  mfrData[7]  = (uint8_t)constrain(basin3, 0, 255);
  mfrData[8]  = tempX10 & 0xFF;
  mfrData[9]  = (tempX10 >> 8) & 0xFF;
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

// Scan BLE 1 seconde — appelé toutes les 2s depuis le loop
// Le callback onResult() publie les données dès réception (< 500ms si CBM actif)
void bleScan() {
  if (!bleInitDone) return;
  NimBLEScan* pScan = NimBLEDevice::getScan();
  pScan->start(1, false);  // 1 seconde, non-continu
  pScan->clearResults();
}

// ========== CALLBACK MQTT ==========
void mqttCallback(char* topic, byte* payload, unsigned int length) {
  String msg;
  for (unsigned int i = 0; i < length; i++) msg += (char)payload[i];
  String t = String(topic);
  Serial.printf("MQTT recv [%s]: %s\n", topic, msg.c_str());

  // Commande vacuum depuis le dashboard
  if (t == mqttTopicCmd) {
    if      (msg == "toggle")             vacuumOn = !vacuumOn;
    else if (msg == "on"  || msg == "1")  vacuumOn = true;
    else if (msg == "off" || msg == "0")  vacuumOn = false;
    digitalWrite(VACUUM_PIN, vacuumOn ? HIGH : LOW);
    mqtt.publish(mqttTopicState.c_str(), vacuumOn ? "1" : "0", true);
    Serial.printf("Vacuum: %s\n", vacuumOn ? "ON" : "OFF");
  }

  // Calibration bassins depuis le dashboard (basin1/cal .. basin4/cal)
  for (int bn = 1; bn <= 4; bn++) {
    String calTopic = "cyd/" + deviceId + "/basin" + String(bn) + "/cal";
    if (t == calTopic) {
      int idx = bn - 1;
      int rr  = msg.indexOf("\"refRaw\":");
      int ri  = msg.indexOf("\"refInches\":");
      if (rr >= 0 && ri >= 0) {
        calRefRaw[idx]    = msg.substring(rr + 9).toFloat();
        calRefInches[idx] = msg.substring(ri + 12).toFloat();
        prefs.begin("cal", false);
        prefs.putFloat(("rr" + String(idx)).c_str(), calRefRaw[idx]);
        prefs.putFloat(("ri" + String(idx)).c_str(), calRefInches[idx]);
        prefs.end();
        Serial.printf("Cal B%d: refRaw=%.1f refInches=%.1f\n", bn, calRefRaw[idx], calRefInches[idx]);
      }
    }
  }

  // Profondeur max bassins depuis le dashboard (settings/bmax)
  if (t == "cyd/" + deviceId + "/settings/bmax") {
    for (int bn = 1; bn <= 4; bn++) {
      String key = "\"" + String(bn) + "\":";
      int pos = msg.indexOf(key);
      if (pos >= 0) basinMax[bn - 1] = msg.substring(pos + key.length()).toFloat();
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
  Serial.printf("MQTT: connexion (%s)...\n", clientId.c_str());
  if (mqtt.connect(clientId.c_str())) {
    Serial.println("MQTT: connecté!");
    mqtt.subscribe(mqttTopicCmd.c_str());
    for (int bn = 1; bn <= 4; bn++)
      mqtt.subscribe(("cyd/" + deviceId + "/basin" + String(bn) + "/cal").c_str());
    mqtt.subscribe(("cyd/" + deviceId + "/settings/bmax").c_str());
    // Republier l'état courant au (re)démarrage
    mqtt.publish(mqttTopicState.c_str(), vacuumOn ? "1" : "0", true);
    publishGalToday();
    publishGalHist();
  } else {
    Serial.printf("MQTT: échec (rc=%d)\n", mqtt.state());
  }
}

// Appelé à chaque nouveau cycle dompeur confirmé (transition stable + délai min 20s)
void updateDompeurTime(unsigned long ms) {
  unsigned long sec = ms / 1000;
  char buf[8];
  snprintf(buf, sizeof(buf), "%02lu:%02lu", sec / 60, sec % 60);
  dompeurTime = String(buf);
  addDompeurPoint((int)sec);
  Serial.printf("Dompeur cycle: %s (%lu ms)\n", buf, ms);

  // Vérifier le changement de journée avant de compter les gallons
  checkDayRollover();

  // 3 gallons par cycle, persister et publier
  galCycleCount++;
  galToday += 3;
  saveGallons();

  if (mqtt.connected()) {
    // Durée du cycle (retain:true) — compatibilité affichage dans #dmp
    mqtt.publish(mqttTopicDompeur.c_str(), dompeurTime.c_str(), true);

    // Événement newcycle (retain:false) — source de vérité pour le dashboard
    // Payload: {"ts":millis,"dur":secondes,"cycle":numéroCycleDuJour}
    char ncBuf[80];
    snprintf(ncBuf, sizeof(ncBuf), "{\"ts\":%lu,\"dur\":%lu,\"cycle\":%d}",
      millis(), sec, galCycleCount);
    mqtt.publish(mqttTopicDompeurNewCycle.c_str(), ncBuf, false);

    // Total gallons d'aujourd'hui (retain:true)
    publishGalToday();
  }
}

void checkSerialCommands() {
  if (!Serial.available()) return;
  String line = Serial.readStringUntil('\n');
  line.trim();
  if (line.startsWith("SSID:")) {
    prefs.begin("wifi", false); prefs.putString("ssid", line.substring(5)); prefs.end();
    Serial.printf("SSID sauvegardé: %s\n", line.substring(5).c_str());
  } else if (line.startsWith("PASS:")) {
    prefs.begin("wifi", false); prefs.putString("pass", line.substring(5)); prefs.end();
    Serial.println("Mot de passe sauvegardé. RESTART pour appliquer.");
  } else if (line.startsWith("ID:")) {
    prefs.begin("mqtt", false); prefs.putString("devid", line.substring(3)); prefs.end();
    Serial.printf("Device ID sauvegardé: %s (RESTART requis)\n", line.substring(3).c_str());
  } else if (line == "RESTART") {
    ESP.restart();
  } else if (line == "STATUS") {
    Serial.printf("WiFi: %s  IP: %s\nMQTT: %s  DevID: %s\n",
      WiFi.status() == WL_CONNECTED ? "OK" : "DECONNECTE",
      WiFi.localIP().toString().c_str(),
      mqtt.connected() ? "OK" : "DECONNECTE",
      deviceId.c_str());
    Serial.printf("Dompeur: %s  B1:%d%%  B2:%d%%  B3:%d%%  B4:%d%%\n", dompeurTime.c_str(), basin1, basin2, basin3, basin4);
    Serial.printf("Temp: %.1fC  Hum: %.1f%%  Vacuum: %s\n", temperature, humidity, vacuumOn ? "ON" : "OFF");
    Serial.printf("Gallons: %d gal (%d cycles) le %s\n", galToday, galCycleCount, galDate.c_str());
    Serial.printf("NTP date: %s\n", getDateStr().c_str());
  } else if (line == "GALRESET") {
    // Maintenance: réinitialiser les gallons du jour courant
    galToday = 0; galCycleCount = 0;
    saveGallons(); publishGalToday();
    Serial.println("Gallons réinitialisés.");
  }
}

// ========== SETUP ==========
void setup() {
  Serial.begin(115200);
  delay(100);
  Serial.println("\n=== WROOM Hub - Cabane Marcoux ===");

  // GPIO
  pinMode(DOMPEUR_PIN, INPUT_PULLUP);
  attachInterrupt(digitalPinToInterrupt(DOMPEUR_PIN), limitSwitchISR, CHANGE);
  pinMode(US1_TRIG, OUTPUT);
  pinMode(US1_ECHO, INPUT);
  pinMode(VACUUM_PIN, OUTPUT);
  digitalWrite(VACUUM_PIN, LOW);
  pinMode(LED_PIN, OUTPUT);
  digitalWrite(LED_PIN, LOW);

  // Charger calibration bassins (offset 1-point + profondeur max)
  prefs.begin("cal", true);
  for (int i = 0; i < 4; i++) {
    calRefRaw[i]    = prefs.getFloat(("rr" + String(i)).c_str(), -1);
    calRefInches[i] = prefs.getFloat(("ri" + String(i)).c_str(), -1);
    basinMax[i]     = prefs.getFloat(("mx" + String(i)).c_str(),  0);
  }
  prefs.end();

  // Restaurer les gallons depuis NVS (survit aux redémarrages)
  prefs.begin("gal", true);
  galToday      = prefs.getInt("today",    0);
  galCycleCount = prefs.getInt("cycles",   0);
  galDate       = prefs.getString("date",  "");
  galHist       = prefs.getString("hist",  "[]");
  prefs.end();
  Serial.printf("Gallons restaurés: %d gal (%d cycles) le %s\n", galToday, galCycleCount, galDate.c_str());

  // Device ID (priorité: NVS > code > MAC)
  prefs.begin("mqtt", true);
  String savedId = prefs.getString("devid", "");
  prefs.end();
  if      (savedId.length() > 0)          deviceId = savedId;
  else if (SHARED_DEVICE_ID.length() > 0) deviceId = SHARED_DEVICE_ID;
  else {
    uint8_t mac[6]; WiFi.macAddress(mac);
    char idBuf[7];
    snprintf(idBuf, sizeof(idBuf), "%02x%02x%02x", mac[3], mac[4], mac[5]);
    deviceId = String(idBuf);
  }

  // Initialiser les topics MQTT
  mqttTopicState           = "cyd/" + deviceId + "/state";
  mqttTopicCmd             = "cyd/" + deviceId + "/cmd";
  mqttTopicDompeur         = "cyd/" + deviceId + "/dompeur";
  mqttTopicDompeurLive     = "cyd/" + deviceId + "/dompeur/live";
  mqttTopicDompeurNewCycle = "cyd/" + deviceId + "/dompeur/newcycle";
  mqttTopicDompeurElapsed  = "cyd/" + deviceId + "/dompeur/elapsed";
  mqttTopicGalToday        = "cyd/" + deviceId + "/gallons/today";
  mqttTopicGalHist         = "cyd/" + deviceId + "/gallons/hist";
  mqttTopicTemp            = "cyd/" + deviceId + "/temp";
  mqttTopicHumidity        = "cyd/" + deviceId + "/humidity";
  mqttTopicBasin1          = "cyd/" + deviceId + "/basin1";
  mqttTopicBasin2          = "cyd/" + deviceId + "/basin2";
  mqttTopicBasin3          = "cyd/" + deviceId + "/basin3";
  mqttTopicBasin4          = "cyd/" + deviceId + "/basin4";
  mqttTopicCal             = "cyd/" + deviceId + "/cmd/cal";
  Serial.printf("Device ID: %s\n", deviceId.c_str());

  // BLE init AVANT WiFi (requis: le contrôleur BLE doit être initialisé en premier)
  bleInit();
  updateBleAdvertising();

  // WiFi
  WiFi.mode(WIFI_STA);
  prefs.begin("wifi", true);
  String ssid = prefs.getString("ssid", "Cabane_Marcoux");
  String pass = prefs.getString("pass", "Cabane2025");
  prefs.end();
  Serial.printf("WiFi: connexion à '%s'...\n", ssid.c_str());
  WiFi.begin(ssid.c_str(), pass.c_str());
  int tries = 0;
  while (WiFi.status() != WL_CONNECTED && tries < 20) { delay(500); Serial.print("."); tries++; }
  if (WiFi.status() == WL_CONNECTED)
    Serial.printf("\nWiFi connecté! IP: %s\n", WiFi.localIP().toString().c_str());
  else
    Serial.println("\nWiFi échoué - retry dans le loop");

  // NTP: timezone EST/EDT (UTC-5, DST +1h)
  configTime(-5 * 3600, 3600, "pool.ntp.org", "time.nist.gov");
  Serial.println("NTP: synchronisation en cours...");

  // ArduinoOTA: mise à jour firmware par WiFi (mDNS: hub-<deviceId>.local)
  ArduinoOTA.setHostname(("hub-" + deviceId).c_str());
  ArduinoOTA.setPassword("cabane2025");
  ArduinoOTA.onStart([]()  { Serial.println("OTA: début mise à jour..."); });
  ArduinoOTA.onEnd([]()    { Serial.println("\nOTA: terminé, redémarrage."); });
  ArduinoOTA.onProgress([](unsigned int progress, unsigned int total) {
    Serial.printf("OTA: %u%%\r", progress / (total / 100));
  });
  ArduinoOTA.onError([](ota_error_t error) {
    Serial.printf("OTA erreur[%u]\n", error);
  });
  ArduinoOTA.begin();
  Serial.printf("OTA: prêt — hostname: hub-%s.local\n", deviceId.c_str());

  // MQTT
  mqtt.setServer(MQTT_BROKER, MQTT_PORT);
  mqtt.setCallback(mqttCallback);
  mqtt.setBufferSize(512);

  memset(dompeurHist, 0, sizeof(dompeurHist));
  Serial.println("=== WROOM Hub prêt ===");
  Serial.println("Commandes série: SSID:  PASS:  ID:  RESTART  STATUS  GALRESET");
}

// ========== LOOP ==========
unsigned long lastWifiRetry   = 0;
unsigned long lastDompeurMqtt = 0;
unsigned long lastBleAdv      = 0;
unsigned long lastNtpCheck    = 0;

void loop() {
  // OTA: priorité haute, doit être appelé à chaque itération
  ArduinoOTA.handle();

  // WiFi reconnect (toutes les 30s si déconnecté)
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

  // Vérifier le rollover de journée toutes les 60s
  if (millis() - lastNtpCheck >= 60000) {
    lastNtpCheck = millis();
    checkDayRollover();
  }

  // Scan BLE toutes les 2s — bloque 1s, callback publie bassins 2/3/4 dès réception
  if (millis() - lastBleScan >= BLE_SCAN_INTERVAL) {
    lastBleScan = millis();
    bleScan();
  }

  // Temp / humidité publiée toutes les 30s (Inkbird met à jour lentement)
  if (mqtt.connected() && millis() - lastTempMqtt >= TEMP_MQTT_INTERVAL) {
    lastTempMqtt = millis();
    mqtt.publish(mqttTopicTemp.c_str(),     String(temperature, 1).c_str(), true);
    mqtt.publish(mqttTopicHumidity.c_str(), String(humidity,    1).c_str(), true);
  }

  // Heartbeat LED bleue: blink 50ms toutes les 2s
  if (millis() - lastLedBlink >= 2000) {
    lastLedBlink = millis();
    digitalWrite(LED_PIN, HIGH);
    delay(50);
    digitalWrite(LED_PIN, LOW);
  }

  // Bassin 1: mesure ultrason toutes les 500ms
  if (millis() - lastUltrasonicRead >= US_INTERVAL) {
    lastUltrasonicRead = millis();
    long d1 = readUltrasonic4Wire(US1_TRIG, US1_ECHO);
    Serial.printf(">>> Ultrason B1: raw=%ldcm\n", d1);
    if (d1 >= 0) {
      rawBasin[0] = (int)d1;
      if (mqtt.connected())
        mqtt.publish(("cyd/" + deviceId + "/basin1/raw").c_str(), String(rawBasin[0]).c_str(), true);
      int p1 = distanceToPercent(d1, 0);
      if (p1 >= 0 && p1 != basin1) {
        basin1 = p1;
        Serial.printf("Bassin 1: %dcm = %d%%\n", (int)d1, basin1);
        if (mqtt.connected())
          mqtt.publish(mqttTopicBasin1.c_str(), String(basin1).c_str(), true);
      }
    }
  }

  // Dompeur: détecter une transition stable (debounce logiciel 500ms)
  if (lastChange > 0 && (millis() - lastChange) >= STABLE_MS) {
    bool currentPin = digitalRead(DOMPEUR_PIN);
    if (currentPin == pendingState && currentPin != lastStableState) {
      // Transition confirmée (stable 500ms)
      lastStableState = currentPin;
      unsigned long now = millis();
      if (lsLastEdge > 0) {
        unsigned long delta = now - lsLastEdge;
        if (delta >= 20000) {  // minimum 20s entre deux cycles valides
          lsCycleMs    = delta;
          dompeurReset = false;
          updateDompeurTime(lsCycleMs);
        }
      }
      lsLastEdge = now;
      lastChange = 0;
    } else if (currentPin != pendingState) {
      lastChange = 0;  // rebond — ignorer
    }
  }

  // Dompeur: reset automatique après 30 min d'inactivité
  if (!dompeurReset && lsLastEdge > 0 && (millis() - lsLastEdge) >= DOMPEUR_RESET_MS) {
    dompeurReset = true;
    dompeurTime  = "--:--";
    lsLastEdge   = 0;   // ← remet elapsed à 0 pour ne plus publier 18h+
    graphCount   = 0;
    memset(dompeurHist, 0, sizeof(dompeurHist));
    if (mqtt.connected()) {
      mqtt.publish(mqttTopicDompeur.c_str(),        "--:--", true);
      mqtt.publish(mqttTopicDompeurLive.c_str(),    "--:--", true);
      mqtt.publish(mqttTopicDompeurElapsed.c_str(), "0",     true);
    }
    Serial.println("Dompeur: RESET (30 min d'inactivité)");
  }

  // Dompeur: publier elapsed (secondes) toutes les secondes
  if (mqtt.connected() && millis() - lastDompeurMqtt >= 1000) {
    lastDompeurMqtt = millis();
    unsigned long sec = (lsLastEdge > 0) ? (millis() - lsLastEdge) / 1000 : 0;
    char elapsedBuf[12];
    snprintf(elapsedBuf, sizeof(elapsedBuf), "%lu", sec);
    mqtt.publish(mqttTopicDompeurElapsed.c_str(), elapsedBuf, true);
    char liveBuf[8];
    snprintf(liveBuf, sizeof(liveBuf), "%02lu:%02lu", sec / 60, sec % 60);
    mqtt.publish(mqttTopicDompeurLive.c_str(), liveBuf, true);
  }

  // BLE advertising: mettre à jour l'état toutes les 2s
  if (millis() - lastBleAdv >= 2000) {
    lastBleAdv = millis();
    updateBleAdvertising();
  }

  delay(10);
}
