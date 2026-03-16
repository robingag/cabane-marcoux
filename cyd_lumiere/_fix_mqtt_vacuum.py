"""
Fix ESP32 CYD firmware:
1. MQTT subscriptions for sensor topics
2. MQTT callback handles incoming sensor data
3. Compact basin layout + vacuum button restored
4. Vacuum touch zone in handleMainTouch
"""

filepath = r"C:\Users\ryb086\OneDrive - Groupe R.Y. Beaudoin\Bureau\CLAUDE_CODE\cyd_lumiere\src\main.cpp"

with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

changes = 0

# --- Fix 1: Subscribe to sensor topics in mqttConnect() ---
old = """    mqtt.subscribe(mqttTopicCmd.c_str());
    publishState();"""
new = """    mqtt.subscribe(mqttTopicCmd.c_str());
    mqtt.subscribe(mqttTopicDompeur.c_str());
    mqtt.subscribe(mqttTopicTemp.c_str());
    mqtt.subscribe(mqttTopicBasin1.c_str());
    mqtt.subscribe(mqttTopicBasin2.c_str());
    mqtt.subscribe(mqttTopicBasin3.c_str());
    publishState();"""
if old in content:
    content = content.replace(old, new)
    changes += 1
    print("[OK] Fix 1: Souscriptions MQTT ajoutees (dompeur, temp, basin1-3)")
else:
    print("[SKIP] Fix 1: Pattern non trouve")

# --- Fix 2: Handle sensor topics in mqttCallback() ---
old = """    } else if (msg == "off") {
      lightOn = false;
      publishState();
    }
  }
}

void mqttConnect()"""
new = """    } else if (msg == "off") {
      lightOn = false;
      publishState();
    }
  }
  // Donnees capteurs entrantes
  else if (String(topic) == mqttTopicDompeur) {
    dompeurTime = msg;
    int colonIdx = msg.indexOf(':');
    if (colonIdx > 0) {
      int mins = msg.substring(0, colonIdx).toInt();
      int secs = msg.substring(colonIdx + 1).toInt();
      addDompeurPoint(mins * 60 + secs);
    }
    Serial.printf(">>> MQTT: Dompeur = %s\\n", msg.c_str());
    if (currentScreen == SCREEN_MAIN && !menuOpen) drawDompeurCard();
  }
  else if (String(topic) == mqttTopicTemp) {
    temperature = msg.toFloat();
    Serial.printf(">>> MQTT: Temp = %.1f\\n", temperature);
  }
  else if (String(topic) == mqttTopicBasin1) {
    basin1 = msg.toInt();
    Serial.printf(">>> MQTT: Basin1 = %d%%\\n", basin1);
    if (currentScreen == SCREEN_MAIN && !menuOpen) drawBasinCards();
  }
  else if (String(topic) == mqttTopicBasin2) {
    basin2 = msg.toInt();
    Serial.printf(">>> MQTT: Basin2 = %d%%\\n", basin2);
    if (currentScreen == SCREEN_MAIN && !menuOpen) drawBasinCards();
  }
  else if (String(topic) == mqttTopicBasin3) {
    basin3 = msg.toInt();
    Serial.printf(">>> MQTT: Basin3 = %d%%\\n", basin3);
    if (currentScreen == SCREEN_MAIN && !menuOpen) drawBasinCards();
  }
}

void mqttConnect()"""
if old in content:
    content = content.replace(old, new)
    changes += 1
    print("[OK] Fix 2: Callback MQTT traite les donnees capteurs")
else:
    print("[SKIP] Fix 2: Pattern non trouve")

# --- Fix 3: Compact basin cards to make room for vacuum ---
old = """void drawBasinCards() {
  int cy = 88, ch = 148;
  tft.fillRoundRect(4, cy, SW - 8, ch, 6, C_CARD);
  tft.drawRoundRect(4, cy, SW - 8, ch, 6, C_BORDER);
  // Basin bars (espacement 48px, remplit toute la carte)
  drawBasinBar(cy + 20, "Bassin 1", basin1);
  drawBasinBar(cy + 68, "Bassin 2", basin2);
  drawBasinBar(cy + 116, "Bassin 3", basin3);
}"""
new = """void drawBasinCards() {
  int cy = 88, ch = 124;
  tft.fillRoundRect(4, cy, SW - 8, ch, 6, C_CARD);
  tft.drawRoundRect(4, cy, SW - 8, ch, 6, C_BORDER);
  // Basin bars (espacement 38px, compact pour laisser place au vacuum)
  drawBasinBar(cy + 8, "Bassin 1", basin1);
  drawBasinBar(cy + 46, "Bassin 2", basin2);
  drawBasinBar(cy + 84, "Bassin 3", basin3);
}"""
if old in content:
    content = content.replace(old, new)
    changes += 1
    print("[OK] Fix 3: Bassins compacts (124px au lieu de 148px)")
else:
    print("[SKIP] Fix 3: Pattern non trouve")

# --- Fix 4: Update vacuum button Y position ---
old = "void drawVacuumBtn() {\n  int sx = 4, sy = 204, sw = SW - 8, sh = 22;"
new = "void drawVacuumBtn() {\n  int sx = 4, sy = 214, sw = SW - 8, sh = 22;"
if old in content:
    content = content.replace(old, new)
    changes += 1
    print("[OK] Fix 4: Position vacuum y=214 (sous les bassins)")
else:
    print("[SKIP] Fix 4: Pattern non trouve")

# --- Fix 5: Add vacuum button to drawMainScreen ---
old = """void drawMainScreen() {
  tft.fillScreen(C_BG);
  drawHeader();
  drawDompeurCard();
  drawBasinCards();
}"""
new = """void drawMainScreen() {
  tft.fillScreen(C_BG);
  drawHeader();
  drawDompeurCard();
  drawBasinCards();
  drawVacuumBtn();
}"""
if old in content:
    content = content.replace(old, new)
    changes += 1
    print("[OK] Fix 5: drawVacuumBtn() ajoute a drawMainScreen()")
else:
    print("[SKIP] Fix 5: Pattern non trouve")

# --- Fix 6: Add vacuum touch zone in handleMainTouch ---
old = """void handleMainTouch(int tx, int ty) {
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
new = """void handleMainTouch(int tx, int ty) {
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
  // Vacuum toggle (bottom bar, y=214 to 236)
  if (ty >= 214 && ty <= 236) {
    lightOn = !lightOn;
    drawVacuumBtn();
    publishState();
    Serial.printf(">>> Touch: Vacuum %s\\n", lightOn ? "ON" : "OFF");
    return;
  }
}"""
if old in content:
    content = content.replace(old, new)
    changes += 1
    print("[OK] Fix 6: Zone touch vacuum ajoutee (y 214-236)")
else:
    print("[SKIP] Fix 6: Pattern non trouve")

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)

print(f"\n=== {changes}/6 corrections appliquees ===")
