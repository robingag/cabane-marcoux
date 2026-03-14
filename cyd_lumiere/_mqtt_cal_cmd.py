"""
Ajouter gestion commande MQTT cmd/cal pour calibrer depuis la page web
1. Rendre mqttTopicCal global
2. Subscribe dans mqttConnect()
3. Handler dans mqttCallback()
"""

path = r"C:\Users\ryb086\OneDrive - Groupe R.Y. Beaudoin\Bureau\CLAUDE_CODE\cyd_lumiere\src\main.cpp"

with open(path, "r", encoding="utf-8") as f:
    code = f.read()

replacements = [
    # 1. Ajouter mqttTopicCal comme variable globale (apres mqttTopicBasin3)
    (
        'String mqttTopicBasin3;\n',
        'String mqttTopicBasin3;\n'
        'String mqttTopicCal;\n'
    ),

    # 2. Initialiser mqttTopicCal dans setup (remplacer le local par le global)
    (
        '  // Additional topics for calibration\n'
        '  String mqttTopicRaw1 = "cyd/" + deviceId + "/raw1";\n'
        '  String mqttTopicRaw2 = "cyd/" + deviceId + "/raw2";\n'
        '  String mqttTopicRaw3 = "cyd/" + deviceId + "/raw3";\n'
        '  String mqttTopicCal = "cyd/" + deviceId + "/cmd/cal";',
        '  // Additional topics for calibration\n'
        '  String mqttTopicRaw1 = "cyd/" + deviceId + "/raw1";\n'
        '  String mqttTopicRaw2 = "cyd/" + deviceId + "/raw2";\n'
        '  String mqttTopicRaw3 = "cyd/" + deviceId + "/raw3";\n'
        '  mqttTopicCal = "cyd/" + deviceId + "/cmd/cal";'
    ),

    # 3. Subscribe au topic cal dans mqttConnect()
    (
        '    mqtt.subscribe(mqttTopicBasin3.c_str());\n'
        '    publishState();',
        '    mqtt.subscribe(mqttTopicBasin3.c_str());\n'
        '    mqtt.subscribe(mqttTopicCal.c_str());\n'
        '    publishState();'
    ),

    # 4. Handler dans mqttCallback - apres le dernier else if basin3
    (
        '    Serial.printf(">>> MQTT: Basin3 = %d%%\\n", basin3);\n'
        '    if (currentScreen == SCREEN_MAIN && !menuOpen) drawBasinCards();\n'
        '  }\n'
        '}',
        '    Serial.printf(">>> MQTT: Basin3 = %d%%\\n", basin3);\n'
        '    if (currentScreen == SCREEN_MAIN && !menuOpen) drawBasinCards();\n'
        '  }\n'
        '  else if (String(topic) == mqttTopicCal) {\n'
        '    // Commande calibration depuis page web: {"basin":1,"point":"low"}\n'
        '    Serial.printf(">>> MQTT CAL CMD: %s\\n", msg.c_str());\n'
        '    int bIdx = -1;\n'
        '    String point = "";\n'
        '    // Parse simple JSON\n'
        '    int bPos = msg.indexOf("basin");\n'
        '    if (bPos >= 0) bIdx = msg.substring(bPos + 7, bPos + 8).toInt() - 1;\n'
        '    if (msg.indexOf("low") >= 0) point = "low";\n'
        '    else if (msg.indexOf("high") >= 0) point = "high";\n'
        '    if (bIdx >= 0 && bIdx < 3 && rawBasin[bIdx] > 0) {\n'
        '      if (point == "low") {\n'
        '        calLow[bIdx] = rawBasin[bIdx];\n'
        '        prefs.begin("calib", false);\n'
        '        prefs.putInt(("lo" + String(bIdx)).c_str(), calLow[bIdx]);\n'
        '        prefs.end();\n'
        '        Serial.printf(">>> MQTT Calib Basin %d LOW = %d (SAVED)\\n", bIdx + 1, calLow[bIdx]);\n'
        '      } else if (point == "high") {\n'
        '        calHigh[bIdx] = rawBasin[bIdx];\n'
        '        prefs.begin("calib", false);\n'
        '        prefs.putInt(("hi" + String(bIdx)).c_str(), calHigh[bIdx]);\n'
        '        prefs.end();\n'
        '        Serial.printf(">>> MQTT Calib Basin %d HIGH = %d (SAVED)\\n", bIdx + 1, calHigh[bIdx]);\n'
        '      }\n'
        '      // Publier cal mise a jour\n'
        '      if (mqtt.connected()) {\n'
        '        String calJson = "{\\"low\\":" + (calLow[bIdx] >= 0 ? String(calLow[bIdx]) : String("null")) + ",\\"high\\":" + (calHigh[bIdx] >= 0 ? String(calHigh[bIdx]) : String("null")) + "}";\n'
        '        String calTopic = "cyd/" + deviceId + "/basin" + String(bIdx + 1) + "/cal";\n'
        '        mqtt.publish(calTopic.c_str(), calJson.c_str(), true);\n'
        '      }\n'
        '      if (currentScreen == SCREEN_CALIB) drawCalibScreen();\n'
        '    }\n'
        '  }\n'
        '}'
    ),
]

count = 0
for old, new in replacements:
    if old in code:
        code = code.replace(old, new, 1)
        count += 1
        print(f"[OK] Replacement {count}")
    else:
        print(f"[FAIL] Not found: {old[:80]}...")

with open(path, "w", encoding="utf-8") as f:
    f.write(code)

print(f"\nDone: {count}/{len(replacements)} replacements applied")
