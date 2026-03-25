/*
 * USB 2 — ESP32 CP2102 (COM8)
 * Lit 2x JSN-SR04T (Bassin 2 + Bassin 3)
 * Transmet via BLE advertisement (nom "CBM")
 * B2: Trig=18, Echo=19
 * B3: Trig=22, Echo=23
 */

#include <Arduino.h>
#include <NimBLEDevice.h>

#define B2_TRIG 18
#define B2_ECHO 19
#define B3_TRIG 22
#define B3_ECHO 23
#define LED_PIN 2

#define MAGIC_BYTE 0xCB
#define MEASURE_INTERVAL 2000

NimBLEAdvertising* pAdvertising = nullptr;
unsigned long lastMeasure = 0;
uint16_t distB2 = 0;
uint16_t distB3 = 0;

long readUltrasonic(int trigPin, int echoPin) {
  digitalWrite(trigPin, LOW);
  delayMicroseconds(5);
  digitalWrite(trigPin, HIGH);
  delayMicroseconds(50);
  digitalWrite(trigPin, LOW);
  long duration = pulseIn(echoPin, HIGH, 50000);
  if (duration == 0) return -1;
  return duration / 58;
}

void updateAdvertising() {
  if (!pAdvertising) return;
  pAdvertising->stop();

  NimBLEAdvertisementData advData;
  advData.setName("CBM");

  // Format: [companyID_lo, companyID_hi, magic, b2_lo, b2_hi, b3_lo, b3_hi]
  // Hub reads: mfr[2]==0xCB, mfr[3-4]=B2, mfr[5-6]=B3
  std::string mfString;
  mfString += (char)0xFF;
  mfString += (char)0xFF;
  mfString += (char)MAGIC_BYTE;
  mfString += (char)(distB2 & 0xFF);
  mfString += (char)((distB2 >> 8) & 0xFF);
  mfString += (char)(distB3 & 0xFF);
  mfString += (char)((distB3 >> 8) & 0xFF);
  advData.setManufacturerData(mfString);

  pAdvertising->setAdvertisementData(advData);
  pAdvertising->start();
}

void setup() {
  Serial.begin(115200);
  delay(500);
  Serial.println("\n=== USB 2 — Bassin 2+3 BLE ===");
  Serial.printf("B2: Trig=%d Echo=%d\n", B2_TRIG, B2_ECHO);
  Serial.printf("B3: Trig=%d Echo=%d\n", B3_TRIG, B3_ECHO);

  pinMode(B2_TRIG, OUTPUT);
  digitalWrite(B2_TRIG, LOW);
  pinMode(B2_ECHO, INPUT);
  pinMode(B3_TRIG, OUTPUT);
  digitalWrite(B3_TRIG, LOW);
  pinMode(B3_ECHO, INPUT);
  pinMode(LED_PIN, OUTPUT);

  NimBLEDevice::init("CBM");
  NimBLEDevice::setPower(ESP_PWR_LVL_P9);

  pAdvertising = NimBLEDevice::getAdvertising();
  pAdvertising->setMinInterval(160);
  pAdvertising->setMaxInterval(320);

  updateAdvertising();
  Serial.println("BLE advertising started as 'CBM'");
}

void loop() {
  if (millis() - lastMeasure >= MEASURE_INTERVAL) {
    lastMeasure = millis();

    long d2 = readUltrasonic(B2_TRIG, B2_ECHO);
    if (d2 > 0 && d2 < 500) distB2 = (uint16_t)d2;

    long d3 = readUltrasonic(B3_TRIG, B3_ECHO);
    if (d3 > 0 && d3 < 500) distB3 = (uint16_t)d3;

    updateAdvertising();
    digitalWrite(LED_PIN, !digitalRead(LED_PIN));
    Serial.printf("B2: %dcm  B3: %dcm (BLE: %d/%d)\n", (int)d2, (int)d3, distB2, distB3);
  }
}
