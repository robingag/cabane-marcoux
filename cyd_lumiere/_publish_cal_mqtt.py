"""
Publier les points de calibration sur MQTT apres chaque sauvegarde
Topics: cyd/{id}/basin1/cal, etc. avec JSON {"low":XX,"high":XX}
"""

path = r"C:\Users\ryb086\OneDrive - Groupe R.Y. Beaudoin\Bureau\CLAUDE_CODE\cyd_lumiere\src\main.cpp"

with open(path, "r", encoding="utf-8") as f:
    code = f.read()

replacements = [
    # Apres sauvegarde BAS NIVEAU, publier cal sur MQTT
    (
        '          Serial.printf(">>> Calib Basin %d LOW = %d (SAVED)\\n", i + 1, calLow[i]);\n'
        '        } else {\n'
        '          Serial.printf(">>> Calib Basin %d LOW SKIPPED (raw=%d)\\n", i + 1, rawBasin[i]);\n'
        '        }\n'
        '        drawCalibScreen();\n'
        '        return;\n'
        '      }\n'
        '      if (tx >= 168 && tx <= 308) {\n'
        '        // Haut Niveau - capture raw value\n'
        '        if (rawBasin[i] > 0) {\n'
        '          calHigh[i] = rawBasin[i];\n'
        '          // Sauvegarder immediatement dans NVS\n'
        '          prefs.begin("calib", false);\n'
        '          prefs.putInt(("hi" + String(i)).c_str(), calHigh[i]);\n'
        '          prefs.end();\n'
        '          Serial.printf(">>> Calib Basin %d HIGH = %d (SAVED)\\n", i + 1, calHigh[i]);\n'
        '        } else {\n'
        '          Serial.printf(">>> Calib Basin %d HIGH SKIPPED (raw=%d)\\n", i + 1, rawBasin[i]);\n'
        '        }',
        '          Serial.printf(">>> Calib Basin %d LOW = %d (SAVED)\\n", i + 1, calLow[i]);\n'
        '          // Publier calibration sur MQTT\n'
        '          if (mqtt.connected()) {\n'
        '            String calJson = "{\\"low\\":" + String(calLow[i]) + ",\\"high\\":" + (calHigh[i] >= 0 ? String(calHigh[i]) : String("null")) + "}";\n'
        '            String calTopic = "cyd/" + deviceId + "/basin" + String(i + 1) + "/cal";\n'
        '            mqtt.publish(calTopic.c_str(), calJson.c_str(), true);\n'
        '          }\n'
        '        } else {\n'
        '          Serial.printf(">>> Calib Basin %d LOW SKIPPED (raw=%d)\\n", i + 1, rawBasin[i]);\n'
        '        }\n'
        '        drawCalibScreen();\n'
        '        return;\n'
        '      }\n'
        '      if (tx >= 168 && tx <= 308) {\n'
        '        // Haut Niveau - capture raw value\n'
        '        if (rawBasin[i] > 0) {\n'
        '          calHigh[i] = rawBasin[i];\n'
        '          // Sauvegarder immediatement dans NVS\n'
        '          prefs.begin("calib", false);\n'
        '          prefs.putInt(("hi" + String(i)).c_str(), calHigh[i]);\n'
        '          prefs.end();\n'
        '          Serial.printf(">>> Calib Basin %d HIGH = %d (SAVED)\\n", i + 1, calHigh[i]);\n'
        '          // Publier calibration sur MQTT\n'
        '          if (mqtt.connected()) {\n'
        '            String calJson = "{\\"low\\":" + (calLow[i] >= 0 ? String(calLow[i]) : String("null")) + ",\\"high\\":" + String(calHigh[i]) + "}";\n'
        '            String calTopic = "cyd/" + deviceId + "/basin" + String(i + 1) + "/cal";\n'
        '            mqtt.publish(calTopic.c_str(), calJson.c_str(), true);\n'
        '          }\n'
        '        } else {\n'
        '          Serial.printf(">>> Calib Basin %d HIGH SKIPPED (raw=%d)\\n", i + 1, rawBasin[i]);\n'
        '        }'
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
