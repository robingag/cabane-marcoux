f = r'C:\Users\ryb086\OneDrive - Groupe R.Y. Beaudoin\Bureau\CLAUDE_CODE\cyd_lumiere\src\main.cpp'
with open(f, 'r', encoding='utf-8') as fh:
    c = fh.read()

# 1. Replace calibOff vars with 2-point calibration + PIN vars
old_vars = """int basin1 = 0;  // 0-100%
int basin2 = 0;
int basin3 = 0;
int calibOff1 = 0, calibOff2 = 0, calibOff3 = 0; // calibration offsets"""

new_vars = """int basin1 = 0;  // 0-100%
int basin2 = 0;
int basin3 = 0;
int rawBasin[3] = {0, 0, 0};  // raw sensor values
int calLow[3]  = {-1, -1, -1}; // calibration low points (-1 = not set)
int calHigh[3] = {-1, -1, -1}; // calibration high points

// PIN entry
String pinCode = "";
const char* CAL_PIN = "123";"""

c = c.replace(old_vars, new_vars)
print("1. Vars:", "OK" if "rawBasin" in c else "NOT FOUND")

# 2. Add SCREEN_PIN to enum
old_enum = "enum Screen { SCREEN_MAIN, SCREEN_WIFI_LIST, SCREEN_WIFI_PASS, SCREEN_WIFI_CONNECTING, SCREEN_WIFI_FAIL, SCREEN_QR_LOCAL, SCREEN_QR_REMOTE, SCREEN_INFO, SCREEN_CALIB };"
new_enum = "enum Screen { SCREEN_MAIN, SCREEN_WIFI_LIST, SCREEN_WIFI_PASS, SCREEN_WIFI_CONNECTING, SCREEN_WIFI_FAIL, SCREEN_QR_LOCAL, SCREEN_QR_REMOTE, SCREEN_INFO, SCREEN_PIN, SCREEN_CALIB };"
c = c.replace(old_enum, new_enum)
print("2. Enum:", "OK" if "SCREEN_PIN" in c else "NOT FOUND")

# 3. Add MQTT topics for raw basins + cmd/cal (after basin3 topic)
old_topics = """  mqttTopicBasin3 = "cyd/" + deviceId + "/basin3";"""
new_topics = """  mqttTopicBasin3 = "cyd/" + deviceId + "/basin3";
  // Additional topics for calibration
  String mqttTopicRaw1 = "cyd/" + deviceId + "/raw1";
  String mqttTopicRaw2 = "cyd/" + deviceId + "/raw2";
  String mqttTopicRaw3 = "cyd/" + deviceId + "/raw3";
  String mqttTopicCal = "cyd/" + deviceId + "/cmd/cal";"""
c = c.replace(old_topics, new_topics)
print("3. Topics:", "OK" if "mqttTopicRaw1" in c else "NOT FOUND")

# 4. Remove calibOff from drawBasinCards, use raw calibration
old_basin_draw = """  drawBasinBar(cy + 12, "Bassin 1", constrain(basin1 + calibOff1, 0, 100));
  drawBasinBar(cy + 48, "Bassin 2", constrain(basin2 + calibOff2, 0, 100));
  drawBasinBar(cy + 84, "Bassin 3", constrain(basin3 + calibOff3, 0, 100));"""

new_basin_draw = """  drawBasinBar(cy + 12, "Bassin 1", basin1);
  drawBasinBar(cy + 48, "Bassin 2", basin2);
  drawBasinBar(cy + 84, "Bassin 3", basin3);"""

c = c.replace(old_basin_draw, new_basin_draw)
print("4. BasinDraw:", "OK" if 'drawBasinBar(cy + 12, "Bassin 1", basin1)' in c else "NOT FOUND")

# 5. Replace entire calibration section (drawCalibScreen + handleCalibTouch)
#    with PIN screen + new 2-point calibration
old_calib = """// ---- Calibration Screen ----
void drawCalibScreen() {
  tft.fillScreen(C_BG);
  tft.fillRect(0, 0, SW, 28, C_HEADER);
  tft.setTextFont(1); tft.setTextSize(2);
  tft.setTextDatum(MC_DATUM);
  tft.setTextColor(C_TXT, C_HEADER);
  tft.drawString("CALIBRATION", SW / 2, 14);

  const char* names[] = {"Bassin 1", "Bassin 2", "Bassin 3"};
  int offsets[] = {calibOff1, calibOff2, calibOff3};

  for (int i = 0; i < 3; i++) {
    int ry = 42 + i * 56;
    // Label
    tft.setTextFont(1); tft.setTextSize(2);
    tft.setTextDatum(ML_DATUM);
    tft.setTextColor(C_LABEL, C_BG);
    tft.drawString(names[i], 12, ry + 10);
    // Minus button
    tft.fillRoundRect(160, ry, 40, 30, 6, C_BORDER);
    tft.setTextDatum(MC_DATUM);
    tft.setTextColor(C_RED, C_BORDER);
    tft.drawString("-", 180, ry + 15);
    // Value
    tft.setTextColor(C_CYAN, C_BG);
    char buf[8];
    sprintf(buf, "%+d", offsets[i]);
    tft.drawString(buf, 224, ry + 15);
    // Plus button
    tft.fillRoundRect(260, ry, 40, 30, 6, C_BORDER);
    tft.setTextColor(C_GREEN, C_BORDER);
    tft.drawString("+", 280, ry + 15);
  }

  // Retour button
  tft.fillRoundRect(SW / 2 - 60, 215, 120, 22, 6, C_HEADER);
  tft.setTextFont(1); tft.setTextSize(1);
  tft.setTextDatum(MC_DATUM);
  tft.setTextColor(C_TXT, C_HEADER);
  tft.drawString("RETOUR", SW / 2, 226);
}

void handleCalibTouch(int tx, int ty) {
  // Retour button
  if (ty >= 215 && tx >= SW / 2 - 60 && tx <= SW / 2 + 60) {
    // Save offsets to Preferences
    prefs.begin("calib", false);
    prefs.putInt("off1", calibOff1);
    prefs.putInt("off2", calibOff2);
    prefs.putInt("off3", calibOff3);
    prefs.end();
    currentScreen = SCREEN_MAIN;
    drawMainScreen();
    return;
  }
  // +/- buttons for each basin
  for (int i = 0; i < 3; i++) {
    int ry = 42 + i * 56;
    if (ty >= ry && ty <= ry + 30) {
      int* off = (i == 0) ? &calibOff1 : (i == 1) ? &calibOff2 : &calibOff3;
      if (tx >= 160 && tx <= 200) { *off -= 5; if (*off < -50) *off = -50; }
      if (tx >= 260 && tx <= 300) { *off += 5; if (*off > 50) *off = 50; }
      drawCalibScreen();
      return;
    }
  }
}"""

new_calib = r"""// ---- PIN Screen ----
void drawPinScreen() {
  tft.fillScreen(C_BG);
  tft.fillRect(0, 0, SW, 24, C_HEADER);
  tft.setTextFont(1); tft.setTextSize(1);
  tft.setTextDatum(MC_DATUM);
  tft.setTextColor(C_CYAN, C_HEADER);
  tft.drawString("NIP CALIBRATION", SW / 2, 12);

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
            if (pinCode == String(CAL_PIN)) {
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
}"""

c = c.replace(old_calib, new_calib)
print("5. CalibRewrite:", "OK" if "drawPinScreen" in c and "BAS NIVEAU" in c else "NOT FOUND")

# 6. Change gear touch to go to PIN screen instead of SCREEN_CALIB
old_gear_touch = """  // Gear icon on basin card (top-right, ~SW-28 to SW-8, y 88-108)
  if (tx >= SW - 32 && tx <= SW - 4 && ty >= 86 && ty <= 110) {
    currentScreen = SCREEN_CALIB;
    drawCalibScreen();
    return;
  }"""

new_gear_touch = """  // Gear icon on basin card -> PIN screen
  if (tx >= SW - 32 && tx <= SW - 4 && ty >= 86 && ty <= 110) {
    pinCode = "";
    currentScreen = SCREEN_PIN;
    drawPinScreen();
    return;
  }"""

c = c.replace(old_gear_touch, new_gear_touch)
print("6. GearTouch:", "OK" if "SCREEN_PIN" in new_gear_touch and new_gear_touch in c else "NOT FOUND")

# 7. Add SCREEN_PIN to loop() touch switch
old_switch = """      case SCREEN_CALIB:
        handleCalibTouch(sx, sy);
        break;"""

new_switch = """      case SCREEN_PIN:
        handlePinTouch(sx, sy);
        break;
      case SCREEN_CALIB:
        handleCalibTouch(sx, sy);
        break;"""

c = c.replace(old_switch, new_switch)
print("7. LoopSwitch:", "OK" if "handlePinTouch" in c else "NOT FOUND")

# 8. Replace Preferences loading (offsets -> 2-point cal)
old_prefs_load = """  // Load calibration offsets
  if (prefs.begin("calib", true)) {
    calibOff1 = prefs.getInt("off1", 0);
    calibOff2 = prefs.getInt("off2", 0);
    calibOff3 = prefs.getInt("off3", 0);
    prefs.end();
  }"""

new_prefs_load = """  // Load 2-point calibration
  if (prefs.begin("calib", true)) {
    for (int i = 0; i < 3; i++) {
      String kl = "lo" + String(i);
      String kh = "hi" + String(i);
      calLow[i] = prefs.getInt(kl.c_str(), -1);
      calHigh[i] = prefs.getInt(kh.c_str(), -1);
    }
    prefs.end();
  }"""

c = c.replace(old_prefs_load, new_prefs_load)
print("8. PrefsLoad:", "OK" if 'calLow[i] = prefs.getInt' in c else "NOT FOUND")

with open(f, 'w', encoding='utf-8') as fh:
    fh.write(c)

import os
print(f"\nDone! Size: {os.path.getsize(f)} bytes")
