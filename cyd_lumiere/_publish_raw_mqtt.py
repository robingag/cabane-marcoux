"""
Publier les valeurs raw (cm) sur MQTT pour la page GitHub calibration
Topics: cyd/{id}/basin1/raw, etc.
"""

path = r"C:\Users\ryb086\OneDrive - Groupe R.Y. Beaudoin\Bureau\CLAUDE_CODE\cyd_lumiere\src\main.cpp"

with open(path, "r", encoding="utf-8") as f:
    code = f.read()

replacements = [
    # Apres la publication du % bassin1, ajouter publication raw
    (
        '    if (p1 >= 0 && p1 != basin1) {\n'
        '      basin1 = p1;\n'
        '      if (currentScreen == SCREEN_MAIN && !menuOpen) drawBasinCards();\n'
        '      if (mqtt.connected()) {\n'
        '        mqtt.publish(mqttTopicBasin1.c_str(), String(basin1).c_str(), true);\n'
        '      }',
        '    if (p1 >= 0 && p1 != basin1) {\n'
        '      basin1 = p1;\n'
        '      if (currentScreen == SCREEN_MAIN && !menuOpen) drawBasinCards();\n'
        '      if (mqtt.connected()) {\n'
        '        mqtt.publish(mqttTopicBasin1.c_str(), String(basin1).c_str(), true);\n'
        '        // Publier raw pour la page calibration\n'
        '        String rawTopic = "cyd/" + deviceId + "/basin1/raw";\n'
        '        mqtt.publish(rawTopic.c_str(), String(rawBasin[0]).c_str(), true);\n'
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
