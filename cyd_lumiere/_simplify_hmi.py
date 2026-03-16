f = r'C:\Users\ryb086\OneDrive - Groupe R.Y. Beaudoin\Bureau\CLAUDE_CODE\cyd_lumiere\src\main.cpp'
with open(f, 'r', encoding='utf-8') as fh:
    c = fh.read()

# 1. drawDompeurCard — BIGGER, full width, textSize 4
old_domp = """void drawDompeurCard() {
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
}"""

new_domp = """void drawDompeurCard() {
  int cx = 4, cy = 40, cw = SW - 8, ch = 56;
  tft.fillRect(cx, cy, cw, 2, C_AMBER);
  tft.fillRoundRect(cx, cy + 2, cw, ch - 2, 4, C_CARD);
  tft.drawRoundRect(cx, cy + 2, cw, ch - 2, 4, C_BORDER);
  tft.setTextFont(1); tft.setTextSize(1);
  tft.setTextDatum(TL_DATUM);
  tft.setTextColor(C_TXT_GRAY, C_CARD);
  tft.drawString("TEMPS DOMPEUR", cx + 10, cy + 6);
  tft.setTextSize(4);
  tft.setTextDatum(MC_DATUM);
  tft.setTextColor(C_AMBER, C_CARD);
  tft.drawString(dompeurTime.c_str(), cx + cw / 2, cy + 36);
}"""

c = c.replace(old_domp, new_domp)
print("1. DompeurCard:", "OK" if new_domp in c else "NOT FOUND")

# 2. drawBasinBar — BIGGER bars (barH 12->20)
old_bar = """void drawBasinBar(int y, const char* name, int level) {
  int nameX = 10, barX = 62, barW = 210, barH = 12;
  // Name
  tft.setTextFont(1); tft.setTextSize(1);
  tft.setTextDatum(ML_DATUM);
  tft.setTextColor(C_LABEL, C_CARD);
  tft.drawString(name, nameX, y + 7);
  // Bar wrapper
  tft.fillRect(barX, y + 1, barW, barH, C_BG);
  tft.drawRect(barX, y + 1, barW, barH, C_BORDER);
  // Fill
  int fillW = (barW - 2) * level / 100;
  if (fillW > 0) {
    uint16_t bc = C_GREEN;
    if (level >= 50) bc = C_RED;
    else if (level >= 25) bc = C_AMBER;
    tft.fillRect(barX + 1, y + 2, fillW, barH - 2, bc);
  }
  // Percentage
  tft.setTextDatum(MR_DATUM);
  tft.setTextColor(C_TXT_DIM, C_CARD);
  String pct = String(level) + "%";
  tft.drawString(pct.c_str(), SW - 10, y + 7);
}"""

new_bar = """void drawBasinBar(int y, const char* name, int level) {
  int nameX = 10, barX = 68, barW = 200, barH = 20;
  // Name
  tft.setTextFont(1); tft.setTextSize(1);
  tft.setTextDatum(ML_DATUM);
  tft.setTextColor(C_LABEL, C_CARD);
  tft.drawString(name, nameX, y + 12);
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
  tft.drawString(pct.c_str(), SW - 10, y + 12);
}"""

c = c.replace(old_bar, new_bar)
print("2. BasinBar:", "OK" if new_bar in c else "NOT FOUND")

# 3. drawBasinCards — BIGGER, new positions
old_cards = """void drawBasinCards() {
  int cy = 132, ch = 64;
  tft.fillRoundRect(4, cy, SW - 8, ch, 4, C_CARD);
  tft.drawRoundRect(4, cy, SW - 8, ch, 4, C_BORDER);
  // Header like HTML "Etat de remplissage"
  tft.setTextFont(1); tft.setTextSize(1);
  tft.setTextDatum(TL_DATUM);
  tft.setTextColor(C_TXT_GRAY, C_CARD);
  tft.drawString("ETAT DE REMPLISSAGE", 10, cy + 3);
  // Compact basin bars
  drawBasinBar(cy + 13, "BASSIN 1", basin1);
  drawBasinBar(cy + 29, "BASSIN 2", basin2);
  drawBasinBar(cy + 45, "BASSIN 3", basin3);
}"""

new_cards = """void drawBasinCards() {
  int cy = 112, ch = 100;
  tft.fillRoundRect(4, cy, SW - 8, ch, 4, C_CARD);
  tft.drawRoundRect(4, cy, SW - 8, ch, 4, C_BORDER);
  // Header
  tft.setTextFont(1); tft.setTextSize(1);
  tft.setTextDatum(TL_DATUM);
  tft.setTextColor(C_TXT_GRAY, C_CARD);
  tft.drawString("ETAT DE REMPLISSAGE", 10, cy + 4);
  // Big basin bars
  drawBasinBar(cy + 16, "BASSIN 1", basin1);
  drawBasinBar(cy + 44, "BASSIN 2", basin2);
  drawBasinBar(cy + 72, "BASSIN 3", basin3);
}"""

c = c.replace(old_cards, new_cards)
print("3. BasinCards:", "OK" if new_cards in c else "NOT FOUND")

# 4. drawStatusBar — BIGGER + add temperature
old_sb = """void drawStatusBar() {
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
}"""

new_sb = """void drawStatusBar() {
  int sy = 216, sh = 20;
  tft.fillRoundRect(4, sy, SW - 8, sh, 3, C_SB_BG);
  tft.drawRoundRect(4, sy, SW - 8, sh, 3, C_BORDER);
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
}"""

c = c.replace(old_sb, new_sb)
print("4. StatusBar:", "OK" if new_sb in c else "NOT FOUND")

# 5. drawMainScreen — SIMPLIFY (remove temp, graph, vacuum)
old_main = """void drawMainScreen() {
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
}"""

new_main = """void drawMainScreen() {
  tft.fillScreen(C_BG);
  drawHeader();
  drawSectionDiv(28, "DOMPEUR");
  drawDompeurCard();
  drawSectionDiv(100, "NIVEAU DES BASSINS");
  drawBasinCards();
  drawStatusBar();
}"""

c = c.replace(old_main, new_main)
print("5. MainScreen:", "OK" if new_main in c else "NOT FOUND")

# 6. handleMainTouch — REMOVE vacuum touch
old_touch = """void handleMainTouch(int tx, int ty) {
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
    Serial.printf(">>> Touch: Vacuum %s\\n", lightOn ? "ON" : "OFF");
  }
}"""

new_touch = """void handleMainTouch(int tx, int ty) {
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

c = c.replace(old_touch, new_touch)
print("6. Touch:", "OK" if new_touch in c else "NOT FOUND")

# 7. updateDompeurTime — remove drawTrendGraph
old_upd = """  if (currentScreen == SCREEN_MAIN && !menuOpen) {
    drawDompeurCard();
    drawTrendGraph();
  }"""

new_upd = """  if (currentScreen == SCREEN_MAIN && !menuOpen) {
    drawDompeurCard();
  }"""

c = c.replace(old_upd, new_upd)
print("7. UpdateDompeur:", "OK" if new_upd in c else "NOT FOUND")

# 8. mqttCallback — remove drawVacuumBtn, add drawStatusBar for temp
old_vac1 = '      if (currentScreen == SCREEN_MAIN && !menuOpen) drawVacuumBtn();\n      publishState();\n      Serial.printf(">>> MQTT: Vacuum %s\\n", lightOn ? "ON" : "OFF");'
new_vac1 = '      publishState();\n      Serial.printf(">>> MQTT: Vacuum %s\\n", lightOn ? "ON" : "OFF");'
c = c.replace(old_vac1, new_vac1)
print("8a. MQTT vacuum1:", "OK" if new_vac1 in c else "NOT FOUND")

# Remove other drawVacuumBtn calls in mqttCallback
old_vac2 = '      if (currentScreen == SCREEN_MAIN && !menuOpen) drawVacuumBtn();\n      publishState();\n    } else if (msg == "off") {\n      lightOn = false;\n      if (currentScreen == SCREEN_MAIN && !menuOpen) drawVacuumBtn();'
new_vac2 = '      publishState();\n    } else if (msg == "off") {\n      lightOn = false;'
c = c.replace(old_vac2, new_vac2)
print("8b. MQTT vacuum2:", "OK" if new_vac2 in c else "NOT FOUND")

# 9. Menu dropdown — add Vacuum as 5th item
old_menu_items = "#define MENU_ITEMS   4"
new_menu_items = "#define MENU_ITEMS   5"
c = c.replace(old_menu_items, new_menu_items)
print("9a. Menu items:", "OK" if new_menu_items in c else "NOT FOUND")

old_menu_labels = 'const char* menuLabels[MENU_ITEMS] = { "WiFi", "QR Local", "QR Remote", "Infos" };'
new_menu_labels = 'const char* menuLabels[MENU_ITEMS] = { "WiFi", "QR Local", "QR Remote", "Infos", "Vacuum" };'
c = c.replace(old_menu_labels, new_menu_labels)
print("9b. Menu labels:", "OK" if new_menu_labels in c else "NOT FOUND")

old_menu_case3 = """      case 3: // Infos
        menuOpen = false;
        currentScreen = SCREEN_INFO;
        drawInfoScreen();
        break;
    }"""

new_menu_case3 = """      case 3: // Infos
        menuOpen = false;
        currentScreen = SCREEN_INFO;
        drawInfoScreen();
        break;
      case 4: // Vacuum toggle
        lightOn = !lightOn;
        publishState();
        Serial.printf(">>> Menu: Vacuum %s\\n", lightOn ? "ON" : "OFF");
        closeDropdownMenu();
        break;
    }"""

c = c.replace(old_menu_case3, new_menu_case3)
print("9c. Menu vacuum:", "OK" if new_menu_case3 in c else "NOT FOUND")

with open(f, 'w', encoding='utf-8') as fh:
    fh.write(c)

import os
print(f"\nDone! Size: {os.path.getsize(f)} bytes")
