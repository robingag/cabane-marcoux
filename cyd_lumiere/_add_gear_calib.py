f = r'C:\Users\ryb086\OneDrive - Groupe R.Y. Beaudoin\Bureau\CLAUDE_CODE\cyd_lumiere\src\main.cpp'
with open(f, 'r', encoding='utf-8') as fh:
    c = fh.read()

# 1. Fix leftover case 4 vacuum in dropdown (wasn't removed properly)
old_case4 = """      case 3: // Infos
        menuOpen = false;
        currentScreen = SCREEN_INFO;
        drawInfoScreen();
        break;
      case 4: // Vacuum toggle
        lightOn = !lightOn;
        publishState();
        Serial.printf(">>> Menu: Vacuum %s""" + '\\' + """n", lightOn ? "ON" : "OFF");
        closeDropdownMenu();
        break;
    }"""

new_case4 = """      case 3: // Infos
        menuOpen = false;
        currentScreen = SCREEN_INFO;
        drawInfoScreen();
        break;
    }"""

c = c.replace(old_case4, new_case4)
print("1. Remove case4:", "OK" if old_case4 not in c else "NOT FOUND")

# 2. Add SCREEN_CALIB to enum
old_enum = "enum Screen { SCREEN_MAIN, SCREEN_WIFI_LIST, SCREEN_WIFI_PASS, SCREEN_WIFI_CONNECTING, SCREEN_WIFI_FAIL, SCREEN_QR_LOCAL, SCREEN_QR_REMOTE, SCREEN_INFO };"
new_enum = "enum Screen { SCREEN_MAIN, SCREEN_WIFI_LIST, SCREEN_WIFI_PASS, SCREEN_WIFI_CONNECTING, SCREEN_WIFI_FAIL, SCREEN_QR_LOCAL, SCREEN_QR_REMOTE, SCREEN_INFO, SCREEN_CALIB };"
c = c.replace(old_enum, new_enum)
print("2. Enum:", "OK" if "SCREEN_CALIB" in c else "NOT FOUND")

# 3. Add calibration offset variables after basin vars
old_basin_vars = """int basin1 = 0;  // 0-100%
int basin2 = 0;
int basin3 = 0;"""

new_basin_vars = """int basin1 = 0;  // 0-100%
int basin2 = 0;
int basin3 = 0;
int calibOff1 = 0, calibOff2 = 0, calibOff3 = 0; // calibration offsets"""

c = c.replace(old_basin_vars, new_basin_vars)
print("3. Calib vars:", "OK" if "calibOff1" in c else "NOT FOUND")

# 4. Add gear icon draw + touch zone in drawBasinCards
old_basin_cards = """void drawBasinCards() {
  int cy = 88, ch = 120;
  tft.fillRoundRect(4, cy, SW - 8, ch, 6, C_CARD);
  tft.drawRoundRect(4, cy, SW - 8, ch, 6, C_BORDER);
  // Basin bars (evenly spaced)
  drawBasinBar(cy + 12, "Bassin 1", basin1);
  drawBasinBar(cy + 48, "Bassin 2", basin2);
  drawBasinBar(cy + 84, "Bassin 3", basin3);
}"""

new_basin_cards = """void drawGearIcon(int x, int y) {
  // 16x16 gear icon
  tft.fillCircle(x + 8, y + 8, 6, C_TXT_GRAY);
  tft.fillCircle(x + 8, y + 8, 3, C_CARD);
  // Teeth (4 cardinal + 4 diagonal)
  for (int a = 0; a < 4; a++) {
    int dx[] = {0, 8, 0, -8};
    int dy[] = {-8, 0, 8, 0};
    tft.fillRect(x + 8 + dx[a] - 1, y + 8 + dy[a] - 1, 3, 3, C_TXT_GRAY);
  }
}

void drawBasinCards() {
  int cy = 88, ch = 120;
  tft.fillRoundRect(4, cy, SW - 8, ch, 6, C_CARD);
  tft.drawRoundRect(4, cy, SW - 8, ch, 6, C_BORDER);
  // Gear icon (top-right of card)
  drawGearIcon(SW - 28, cy + 4);
  // Basin bars (evenly spaced)
  drawBasinBar(cy + 12, "Bassin 1", constrain(basin1 + calibOff1, 0, 100));
  drawBasinBar(cy + 48, "Bassin 2", constrain(basin2 + calibOff2, 0, 100));
  drawBasinBar(cy + 84, "Bassin 3", constrain(basin3 + calibOff3, 0, 100));
}"""

c = c.replace(old_basin_cards, new_basin_cards)
print("4. Basin+Gear:", "OK" if "drawGearIcon" in c else "NOT FOUND")

# 5. Add calibration screen draw + touch BEFORE drawMainScreen
old_main_screen = """void drawMainScreen() {
  tft.fillScreen(C_BG);
  drawHeader();
  drawDompeurCard();
  drawBasinCards();
  drawStatusBar();
}"""

new_main_screen = """// ---- Calibration Screen ----
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
}

void drawMainScreen() {
  tft.fillScreen(C_BG);
  drawHeader();
  drawDompeurCard();
  drawBasinCards();
  drawStatusBar();
}"""

c = c.replace(old_main_screen, new_main_screen)
print("5. CalibScreen:", "OK" if "drawCalibScreen" in c else "NOT FOUND")

# 6. Add gear touch zone in handleMainTouch
old_main_touch = """void handleMainTouch(int tx, int ty) {
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
}"""

new_main_touch = """void handleMainTouch(int tx, int ty) {
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
  // Gear icon on basin card (top-right, ~SW-28 to SW-8, y 88-108)
  if (tx >= SW - 32 && tx <= SW - 4 && ty >= 86 && ty <= 110) {
    currentScreen = SCREEN_CALIB;
    drawCalibScreen();
    return;
  }
}"""

c = c.replace(old_main_touch, new_main_touch)
print("6. GearTouch:", "OK" if "SCREEN_CALIB" in new_main_touch and new_main_touch in c else "NOT FOUND")

# 7. Add SCREEN_CALIB case in loop() touch switch
old_switch = """      case SCREEN_INFO:
        handleInfoTouch(sx, sy);
        break;
      default:
        break;"""

new_switch = """      case SCREEN_INFO:
        handleInfoTouch(sx, sy);
        break;
      case SCREEN_CALIB:
        handleCalibTouch(sx, sy);
        break;
      default:
        break;"""

c = c.replace(old_switch, new_switch)
print("7. LoopSwitch:", "OK" if "handleCalibTouch" in c else "NOT FOUND")

# 8. Load calibration offsets in setup() after wifi prefs
old_setup_prefs = """  if (prefs.begin("wifi", false)) {
    savedSSID = prefs.getString("ssid", "");
    savedPass = prefs.getString("pass", "");
    prefs.end();"""

new_setup_prefs = """  // Load calibration offsets
  if (prefs.begin("calib", true)) {
    calibOff1 = prefs.getInt("off1", 0);
    calibOff2 = prefs.getInt("off2", 0);
    calibOff3 = prefs.getInt("off3", 0);
    prefs.end();
  }

  if (prefs.begin("wifi", false)) {
    savedSSID = prefs.getString("ssid", "");
    savedPass = prefs.getString("pass", "");
    prefs.end();"""

c = c.replace(old_setup_prefs, new_setup_prefs)
print("8. LoadCalib:", "OK" if 'prefs.getInt("off1"' in c else "NOT FOUND")

with open(f, 'w', encoding='utf-8') as fh:
    fh.write(c)

import os
print(f"\nDone! Size: {os.path.getsize(f)} bytes")
