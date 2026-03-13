"""
Vacuum slider avec PIN 777 + GPIO 4
- Touch slider -> ouvre clavier NIP
- PIN 777 -> toggle vacuum + GPIO 4 + feedback
- PIN 123 -> calibration (inchangé)
- Slider vert ON / rouge OFF
"""
import re

path = r"C:\Users\ryb086\OneDrive - Groupe R.Y. Beaudoin\Bureau\CLAUDE_CODE\cyd_lumiere\src\main.cpp"

with open(path, "r", encoding="utf-8") as f:
    code = f.read()

replacements = [
    # 1. Add VACUUM_PIN and pinReason after lightOn
    (
        'bool lightOn = false;',
        '''bool lightOn = false;
#define VACUUM_PIN 4
// PIN reason: 0=calibration, 1=vacuum
int pinReason = 0;
const char* VACUUM_PIN_CODE = "777";'''
    ),

    # 2. Modify drawPinScreen title to be dynamic
    (
        '  tft.drawString("NIP CALIBRATION", SW / 2, 12);',
        '  tft.drawString(pinReason == 1 ? "NIP VACUUM" : "NIP CALIBRATION", SW / 2, 12);'
    ),

    # 3. Modify handlePinTouch: after 3 digits, check for vacuum PIN too
    (
        '''          if (pinCode.length() == 3) {
            delay(200);
            if (pinCode == String(CAL_PIN)) {
              pinCode = "";
              currentScreen = SCREEN_CALIB;
              drawCalibScreen();
            } else {''',
        '''          if (pinCode.length() == 3) {
            delay(200);
            if (pinReason == 1 && pinCode == String(VACUUM_PIN_CODE)) {
              // Vacuum toggle confirmed
              pinCode = "";
              lightOn = !lightOn;
              digitalWrite(VACUUM_PIN, lightOn ? HIGH : LOW);
              publishState();
              Serial.printf(">>> PIN: Vacuum %s, GPIO4 %s\\n", lightOn ? "ON" : "OFF", lightOn ? "HIGH" : "LOW");
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
            } else {'''
    ),

    # 4. Modify vacuum slider touch: open PIN instead of direct toggle
    (
        '''  // Vacuum slider touch
  if (ty >= 214 && ty <= 236) {
    lightOn = !lightOn;
    drawVacuumBtn();
    publishState();
    Serial.printf(">>> Touch: Vacuum %s\\n", lightOn ? "ON" : "OFF");
    return;
  }''',
        '''  // Vacuum slider touch -> open PIN
  if (ty >= 214 && ty <= 236) {
    pinReason = 1;
    pinCode = "";
    currentScreen = SCREEN_PIN;
    drawPinScreen();
    return;
  }'''
    ),

    # 5. Modify PIN annuler to reset pinReason
    (
        '''  // Annuler
  if (ty >= 218) {
    pinCode = "";
    currentScreen = SCREEN_MAIN;
    drawMainScreen();
    return;
  }''',
        '''  // Annuler
  if (ty >= 218) {
    pinCode = "";
    pinReason = 0;
    currentScreen = SCREEN_MAIN;
    drawMainScreen();
    return;
  }'''
    ),

    # 6. Add GPIO 4 pinMode in setup after TFT_BL
    (
        '  digitalWrite(TFT_BL, HIGH);',
        '''  digitalWrite(TFT_BL, HIGH);

  // Vacuum GPIO
  pinMode(VACUUM_PIN, OUTPUT);
  digitalWrite(VACUUM_PIN, LOW);'''
    ),

    # 7. Add GPIO sync in MQTT callback for vacuum commands
    (
        '''    if (msg == "toggle") {
      lightOn = !lightOn;
      publishState();
      Serial.printf(">>> MQTT: Vacuum %s\\n", lightOn ? "ON" : "OFF");
    } else if (msg == "on") {
      lightOn = true;
      publishState();
    } else if (msg == "off") {
      lightOn = false;
      publishState();
    }''',
        '''    if (msg == "toggle") {
      lightOn = !lightOn;
      digitalWrite(VACUUM_PIN, lightOn ? HIGH : LOW);
      publishState();
      Serial.printf(">>> MQTT: Vacuum %s, GPIO4 %s\\n", lightOn ? "ON" : "OFF", lightOn ? "HIGH" : "LOW");
    } else if (msg == "on") {
      lightOn = true;
      digitalWrite(VACUUM_PIN, HIGH);
      publishState();
    } else if (msg == "off") {
      lightOn = false;
      digitalWrite(VACUUM_PIN, LOW);
      publishState();
    }'''
    ),

    # 8. Add GPIO sync in web toggle handler
    (
        '''  lightOn = !lightOn;
  if (currentScreen == SCREEN_MAIN) drawVacuumBtn();''',
        '''  lightOn = !lightOn;
  digitalWrite(VACUUM_PIN, lightOn ? HIGH : LOW);
  if (currentScreen == SCREEN_MAIN) drawVacuumBtn();'''
    ),

    # 9. Update drawVacuumBtn colors: green track when ON, red when OFF
    (
        '''  uint16_t brd = lightOn ? C_GREEN : C_BORDER;
  tft.fillRoundRect(sx, sy, sw, sh, 4, C_BG);
  tft.drawRoundRect(sx, sy, sw, sh, 4, brd);''',
        '''  uint16_t brd = lightOn ? C_GREEN : C_RED;
  uint16_t trackFill = lightOn ? tft.color565(0, 40, 0) : tft.color565(40, 0, 0);
  tft.fillRoundRect(sx, sy, sw, sh, 4, trackFill);
  tft.drawRoundRect(sx, sy, sw, sh, 4, brd);'''
    ),

    # 10. Update slider text: green "VACUUM ON" / red "VACUUM OFF"
    (
        '''  if (!lightOn) {
    tft.setTextDatum(ML_DATUM);
    tft.setTextColor(tft.color565(180, 50, 50), C_BG);
    tft.drawString("> VACUUM ON", sx + hdlW + 10, sy + sh / 2);
  } else {
    tft.setTextDatum(MR_DATUM);
    tft.setTextColor(C_GREEN, C_BG);
    tft.drawString("VACUUM OFF <", sx + sw - hdlW - 10, sy + sh / 2);
  }''',
        '''  if (!lightOn) {
    tft.setTextDatum(ML_DATUM);
    tft.setTextColor(C_RED, trackFill);
    tft.drawString("> VACUUM ON", sx + hdlW + 10, sy + sh / 2);
  } else {
    tft.setTextDatum(MR_DATUM);
    tft.setTextColor(C_GREEN, trackFill);
    tft.drawString("VACUUM OFF <", sx + sw - hdlW - 10, sy + sh / 2);
  }'''
    ),
]

count = 0
for old, new in replacements:
    if old in code:
        code = code.replace(old, new, 1)
        count += 1
        print(f"[OK] Replacement {count}")
    else:
        print(f"[FAIL] Not found: {old[:60]}...")

with open(path, "w", encoding="utf-8") as f:
    f.write(code)

print(f"\nDone: {count}/{len(replacements)} replacements applied")
