/*
 * Capteur Bassins — ESP32 WROOM
 * Lit 2x JSN-SR04T (bassin 2 + bassin 3)
 * Transmet les distances via BLE advertisement (manufacturer data)
 * Le CYD scanne et parse les données
 *
 * Protocole manufacturer data:
 *   Byte 0:    0xCB (magic — Cabane Bassins)
 *   Byte 1-2:  Bassin 2 distance cm (uint16_t LE)
 *   Byte 3-4:  Bassin 3 distance cm (uint16_t LE)
 *   Byte 5:    Status (0xFF = OK)
 */

#include <Arduino.h>
#include <NimBLEDevice.h>

// JSN-SR04T Bassin 2 (4-wire)
#define B2_TRIG 25
#define B2_ECHO 26

// JSN-SR04T Bassin 3 (4-wire)
#define B3_TRIG 27
#define B3_ECHO 33

// LED interne pour debug
#define LED_PIN 2

// Intervalle de mesure
#define MEASURE_INTERVAL 2000  // 2 secondes

// Magic byte pour identification
#define MAGIC_BYTE 0xCB

NimBLEAdvertising* pAdvertising = nullptr;
unsigned long lastMeasure = 0;
uint16_t distB2 = 0;  // distance bassin 2 en cm
uint16_t distB3 = 0;  // distance bassin 3 en cm

// Lecture ultrasonique JSN-SR04T (4-wire)
long readDistanceCm(int trigPin, int echoPin) {
  digitalWrite(trigPin, LOW);
  delayMicroseconds(5);
  digitalWrite(trigPin, HIGH);
  delayMicroseconds(20);
  digitalWrite(trigPin, LOW);

  long duration = pulseIn(echoPin, HIGH, 30000);  // timeout 30ms
  if (duration == 0) return -1;  // pas d'echo
  return duration / 58;  // conversion en cm
}

// Met a jour les donnees BLE advertisement
void updateAdvertising() {
  if (!pAdvertising) return;

  pAdvertising->stop();

  NimBLEAdvertisementData advData;
  advData.setName("CBM");  // Cabane Marcoux — identifiant pour le CYD

  // Manufacturer data: magic + 2x uint16_t LE + status
  uint8_t mfData[6];
  mfData[0] = MAGIC_BYTE;
  mfData[1] = distB2 & 0xFF;         // bassin 2 low byte
  mfData[2] = (distB2 >> 8) & 0xFF;  // bassin 2 high byte
  mfData[3] = distB3 & 0xFF;         // bassin 3 low byte
  mfData[4] = (distB3 >> 8) & 0xFF;  // bassin 3 high byte
  mfData[5] = 0xFF;                  // status OK

  // NimBLE manufacturer data: premier 2 bytes = company ID, reste = data
  // On utilise 0xFFFF (non-assigné) + nos 6 bytes
  std::string mfString;
  mfString += (char)0xFF;  // company ID low
  mfString += (char)0xFF;  // company ID high
  for (int i = 0; i < 6; i++) {
    mfString += (char)mfData[i];
  }
  advData.setManufacturerData(mfString);

  pAdvertising->setAdvertisementData(advData);
  pAdvertising->start();
}

void setup() {
  Serial.begin(115200);
  delay(500);
  Serial.println("\n=== Capteur Bassins v1.0 ===");
  Serial.println("Bassins 2+3 via BLE");

  // GPIO setup
  pinMode(B2_TRIG, OUTPUT);
  pinMode(B2_ECHO, INPUT);
  pinMode(B3_TRIG, OUTPUT);
  pinMode(B3_ECHO, INPUT);
  pinMode(LED_PIN, OUTPUT);
  digitalWrite(LED_PIN, LOW);

  // Init BLE
  NimBLEDevice::init("CBM");
  NimBLEDevice::setPower(ESP_PWR_LVL_P9);  // puissance max

  pAdvertising = NimBLEDevice::getAdvertising();
  pAdvertising->setMinInterval(160);   // 100ms (160 * 0.625ms)
  pAdvertising->setMaxInterval(320);   // 200ms (320 * 0.625ms)

  // Premier advertisement avec valeurs 0
  updateAdvertising();

  Serial.println("BLE advertising started as 'CBM'");
  Serial.printf("Bassin 2: TRIG=%d ECHO=%d\n", B2_TRIG, B2_ECHO);
  Serial.printf("Bassin 3: TRIG=%d ECHO=%d\n", B3_TRIG, B3_ECHO);
}

void loop() {
  if (millis() - lastMeasure >= MEASURE_INTERVAL) {
    lastMeasure = millis();

    // Lire bassin 2
    long d2 = readDistanceCm(B2_TRIG, B2_ECHO);
    if (d2 > 0 && d2 < 500) {
      distB2 = (uint16_t)d2;
    }

    // Lire bassin 3
    long d3 = readDistanceCm(B3_TRIG, B3_ECHO);
    if (d3 > 0 && d3 < 500) {
      distB3 = (uint16_t)d3;
    }

    // Update BLE advertisement
    updateAdvertising();

    // LED toggle pour montrer que ca tourne
    digitalWrite(LED_PIN, !digitalRead(LED_PIN));

    Serial.printf("B2=%dcm B3=%dcm\n", distB2, distB3);
  }
}
