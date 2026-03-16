"""
Fix calibration:
1. Sauvegarder immediatement a chaque appui BAS/HAUT (pas attendre FERMER)
2. Ajouter debug serial pour confirmer la sauvegarde
3. Ignorer si rawBasin est -1 ou 0
"""

path = r"C:\Users\ryb086\OneDrive - Groupe R.Y. Beaudoin\Bureau\CLAUDE_CODE\cyd_lumiere\src\main.cpp"

with open(path, "r", encoding="utf-8") as f:
    code = f.read()

replacements = [
    # Fix Bas Niveau touch - save immediately + debug
    (
        '      if (tx >= 10 && tx <= 150) {\n'
        '        // Bas Niveau - capture raw value\n'
        '        calLow[i] = rawBasin[i];\n'
        '        Serial.printf(">>> Calib Basin %d LOW = %d\\n", i + 1, rawBasin[i]);\n'
        '        // Publish MQTT calibration command\n'
        '        if (mqtt.connected()) {\n'
        '          String cmd = "{\\\"basin\\\":" + String(i + 1) + ",\\\"point\\\":\\\"low\\\"}";\n'
        '          String topic = "cyd/" + deviceId + "/cmd/cal";\n'
        '          mqtt.publish(topic.c_str(), cmd.c_str());\n'
        '        }\n'
        '        drawCalibScreen();\n'
        '        return;\n'
        '      }',
        '      if (tx >= 10 && tx <= 150) {\n'
        '        // Bas Niveau - capture raw value\n'
        '        if (rawBasin[i] > 0) {\n'
        '          calLow[i] = rawBasin[i];\n'
        '          // Sauvegarder immediatement dans NVS\n'
        '          prefs.begin("calib", false);\n'
        '          prefs.putInt(("lo" + String(i)).c_str(), calLow[i]);\n'
        '          prefs.end();\n'
        '          Serial.printf(">>> Calib Basin %d LOW = %d (SAVED)\\n", i + 1, calLow[i]);\n'
        '        } else {\n'
        '          Serial.printf(">>> Calib Basin %d LOW SKIPPED (raw=%d)\\n", i + 1, rawBasin[i]);\n'
        '        }\n'
        '        drawCalibScreen();\n'
        '        return;\n'
        '      }'
    ),

    # Fix Haut Niveau touch - save immediately + debug
    (
        '      if (tx >= 168 && tx <= 308) {\n'
        '        // Haut Niveau - capture raw value\n'
        '        calHigh[i] = rawBasin[i];\n'
        '        Serial.printf(">>> Calib Basin %d HIGH = %d\\n", i + 1, rawBasin[i]);\n'
        '        if (mqtt.connected()) {\n'
        '          String cmd = "{\\\"basin\\\":" + String(i + 1) + ",\\\"point\\\":\\\"high\\\"}";\n'
        '          String topic = "cyd/" + deviceId + "/cmd/cal";\n'
        '          mqtt.publish(topic.c_str(), cmd.c_str());\n'
        '        }\n'
        '        drawCalibScreen();\n'
        '        return;\n'
        '      }',
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
        '        }\n'
        '        drawCalibScreen();\n'
        '        return;\n'
        '      }'
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
