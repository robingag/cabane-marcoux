"""
Fix calibration bassin 1:
1. rawBasin toujours mis a jour (meme non calibre)
2. Ecran calib se rafraichit en temps reel
3. distanceToPercent retourne la distance brute quand pas calibre
"""

path = r"C:\Users\ryb086\OneDrive - Groupe R.Y. Beaudoin\Bureau\CLAUDE_CODE\cyd_lumiere\src\main.cpp"

with open(path, "r", encoding="utf-8") as f:
    code = f.read()

replacements = [
    # 1. Fix distanceToPercent: quand pas calibre, retourner -1 pour signaler
    #    mais toujours mettre a jour rawBasin
    (
        '// calLow = distance quand bassin vide (loin), calHigh = distance quand plein (proche)\n'
        'int distanceToPercent(long distCm, int idx) {\n'
        '  if (distCm < 0) return -1; // erreur lecture\n'
        '  if (calLow[idx] < 0 || calHigh[idx] < 0) {\n'
        '    // Pas calibre: retourner distance brute comme raw\n'
        '    rawBasin[idx] = (int)distCm;\n'
        '    return 0;\n'
        '  }\n'
        '  rawBasin[idx] = (int)distCm;\n'
        '  // calLow = distance vide (grande), calHigh = distance plein (petite)\n'
        '  // Inverser: plus la distance est petite, plus le niveau est haut\n'
        '  int pct = map(distCm, calLow[idx], calHigh[idx], 0, 100);\n'
        '  return constrain(pct, 0, 100);\n'
        '}',
        '// calLow = distance quand bassin vide (loin), calHigh = distance quand plein (proche)\n'
        'int distanceToPercent(long distCm, int idx) {\n'
        '  if (distCm < 0) return -1; // erreur lecture\n'
        '  rawBasin[idx] = (int)distCm; // toujours mettre a jour la valeur brute\n'
        '  if (calLow[idx] < 0 || calHigh[idx] < 0) {\n'
        '    // Pas calibre: afficher distance brute en cm comme pourcentage temporaire\n'
        '    return constrain((int)distCm, 0, 100);\n'
        '  }\n'
        '  // calLow = distance vide (grande), calHigh = distance plein (petite)\n'
        '  // Inverser: plus la distance est petite, plus le niveau est haut\n'
        '  int pct = map(distCm, calLow[idx], calHigh[idx], 0, 100);\n'
        '  return constrain(pct, 0, 100);\n'
        '}'
    ),

    # 2. Rafraichir ecran calib en temps reel pendant lecture capteur
    (
        '    long d1 = readUltrasonic4Wire(US1_TRIG, US1_ECHO);\n'
        '    int p1 = distanceToPercent(d1, 0);\n'
        '    if (p1 >= 0 && p1 != basin1) {\n'
        '      basin1 = p1;\n'
        '      if (currentScreen == SCREEN_MAIN && !menuOpen) drawBasinCards();\n'
        '      if (mqtt.connected()) {\n'
        '        mqtt.publish(mqttTopicBasin1.c_str(), String(basin1).c_str(), true);\n'
        '      }\n'
        '      Serial.printf("Bassin 1: %dcm = %d%%\\n", (int)d1, basin1);\n'
        '    }',
        '    long d1 = readUltrasonic4Wire(US1_TRIG, US1_ECHO);\n'
        '    int p1 = distanceToPercent(d1, 0);\n'
        '    if (d1 >= 0) Serial.printf("Bassin 1: %dcm = %d%%\\n", (int)d1, p1);\n'
        '    // Rafraichir ecran calib en temps reel\n'
        '    if (currentScreen == SCREEN_CALIB) {\n'
        '      drawCalibScreen();\n'
        '    }\n'
        '    if (p1 >= 0 && p1 != basin1) {\n'
        '      basin1 = p1;\n'
        '      if (currentScreen == SCREEN_MAIN && !menuOpen) drawBasinCards();\n'
        '      if (mqtt.connected()) {\n'
        '        mqtt.publish(mqttTopicBasin1.c_str(), String(basin1).c_str(), true);\n'
        '      }\n'
        '    }'
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
