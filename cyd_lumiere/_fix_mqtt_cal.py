"""
Fix MQTT calibration: l'ESP32 ne recoit pas les commandes cmd/cal du dashboard MQTT.
- Ajouter mqttTopicCal comme variable globale
- Ajouter subscribe a cmd/cal
- Ajouter handler dans mqttCallback pour cmd/cal
- Publier les donnees cal en retour apres calibration
"""

path = r"C:\Users\ryb086\OneDrive - Groupe R.Y. Beaudoin\Bureau\CLAUDE_CODE\cyd_lumiere\src\main.cpp"

with open(path, "r", encoding="utf-8") as f:
    code = f.read()

replacements = [
    # 1. Ajouter mqttTopicCal comme variable globale (apres basin3)
    (
        'String mqttTopicBasin3;  // cyd/{id}/basin3',
        'String mqttTopicBasin3;  // cyd/{id}/basin3\nString mqttTopicCal;     // cyd/{id}/cmd/cal'
    ),
    # 2. Ajouter handler cmd/cal dans mqttCallback (apres basin3 handler)
    (
        '''  else if (String(topic) == mqttTopicBasin3) {
    basin3 = msg.toInt();
    Serial.printf(">>> MQTT: Basin3 = %d%%\\n", basin3);
    if (currentScreen == SCREEN_MAIN && !menuOpen) drawBasinCards();
  }
}''',
        '''  else if (String(topic) == mqttTopicBasin3) {
    basin3 = msg.toInt();
    Serial.printf(">>> MQTT: Basin3 = %d%%\\n", basin3);
    if (currentScreen == SCREEN_MAIN && !menuOpen) drawBasinCards();
  }
  // Calibration command from MQTT dashboard
  else if (String(topic) == mqttTopicCal) {
    Serial.printf(">>> MQTT: cmd/cal = %s\\n", msg.c_str());
    // Parse JSON: {"basin":1,"point":"low"} or {"basin":1,"point":"high"}
    int bIdx = msg.indexOf("\\"basin\\":");
    int pIdx = msg.indexOf("\\"point\\":");
    if (bIdx >= 0 && pIdx >= 0) {
      int basin = msg.substring(bIdx + 8, msg.indexOf(',', bIdx)).toInt();
      String point = "";
      int pStart = msg.indexOf('"', pIdx + 8) + 1;
      int pEnd = msg.indexOf('"', pStart);
      if (pStart > 0 && pEnd > pStart) point = msg.substring(pStart, pEnd);

      if (basin >= 1 && basin <= 3) {
        int idx = basin - 1;
        if (point == "low") {
          calLow[idx] = rawBasin[idx];
          Serial.printf("CAL MQTT: Basin %d LOW = %d\\n", basin, rawBasin[idx]);
        } else if (point == "high") {
          calHigh[idx] = rawBasin[idx];
          Serial.printf("CAL MQTT: Basin %d HIGH = %d\\n", basin, rawBasin[idx]);
        }
        // Save to NVS
        Preferences calPrefs;
        if (calPrefs.begin("calib", false)) {
          String kl = "lo" + String(idx);
          String kh = "hi" + String(idx);
          calPrefs.putInt(kl.c_str(), calLow[idx]);
          calPrefs.putInt(kh.c_str(), calHigh[idx]);
          calPrefs.end();
        }
        // Publish cal data back to MQTT
        String calJson = "{\\"low\\":" + (calLow[idx] >= 0 ? String(calLow[idx]) : String("null")) +
                         ",\\"high\\":" + (calHigh[idx] >= 0 ? String(calHigh[idx]) : String("null")) + "}";
        String calTopic = "cyd/" + deviceId + "/basin" + String(basin) + "/cal";
        mqtt.publish(calTopic.c_str(), calJson.c_str(), true);
        Serial.printf("CAL MQTT: published %s = %s\\n", calTopic.c_str(), calJson.c_str());

        // Publish raw value
        String rawTopic = "cyd/" + deviceId + "/basin" + String(basin) + "/raw";
        mqtt.publish(rawTopic.c_str(), String(rawBasin[idx]).c_str(), true);

        // Redraw if on main screen
        if (currentScreen == SCREEN_MAIN && !menuOpen) drawBasinCards();
      }
    }
  }
}'''
    ),
    # 3. Initialiser mqttTopicCal dans setup (remplacer la variable locale)
    (
        '  String mqttTopicCal = "cyd/" + deviceId + "/cmd/cal";',
        '  mqttTopicCal = "cyd/" + deviceId + "/cmd/cal";'
    ),
    # 4. Ajouter subscribe a cmd/cal dans mqttConnect
    (
        '    mqtt.subscribe(mqttTopicBasin3.c_str());\n    publishState();',
        '    mqtt.subscribe(mqttTopicBasin3.c_str());\n    mqtt.subscribe(mqttTopicCal.c_str());\n    publishState();'
    ),
]

count = 0
for old, new in replacements:
    if old in code:
        code = code.replace(old, new, 1)
        count += 1
        print(f"[OK] {old[:70]}...")
    else:
        print(f"[FAIL] Not found: {old[:70]}...")

with open(path, "w", encoding="utf-8") as f:
    f.write(code)

print(f"\nDone: {count}/{len(replacements)} replacements")
