"""
Fix ecran calibration:
1. Ne pas redessiner tout l'ecran a chaque lecture - juste la valeur brute
2. Ajouter fonction updateCalibRaw() legere
"""

path = r"C:\Users\ryb086\OneDrive - Groupe R.Y. Beaudoin\Bureau\CLAUDE_CODE\cyd_lumiere\src\main.cpp"

with open(path, "r", encoding="utf-8") as f:
    code = f.read()

replacements = [
    # 1. Ajouter updateCalibRaw() juste avant drawCalibScreen()
    (
        'void drawCalibScreen() {\n'
        '  tft.fillScreen(C_BG);',
        'void updateCalibRaw() {\n'
        '  // Rafraichir seulement les valeurs brutes sans redessiner tout\n'
        '  const char* names[] = {"Bassin 1", "Bassin 2", "Bassin 3"};\n'
        '  for (int i = 0; i < 3; i++) {\n'
        '    int ry = 30 + i * 60;\n'
        '    // Effacer zone raw\n'
        '    tft.fillRect(SW / 2, ry - 4, SW / 2, 16, C_BG);\n'
        '    tft.setTextFont(1); tft.setTextSize(2);\n'
        '    tft.setTextDatum(MR_DATUM);\n'
        '    tft.setTextColor(C_CYAN, C_BG);\n'
        '    String rawStr = String(rawBasin[i]) + " cm";\n'
        '    tft.drawString(rawStr.c_str(), SW - 10, ry + 2);\n'
        '    // Mettre a jour cal info\n'
        '    tft.fillRect(10, ry + 12, SW - 20, 14, C_BG);\n'
        '    tft.setTextSize(1);\n'
        '    tft.setTextDatum(ML_DATUM);\n'
        '    tft.setTextColor(C_TXT_DIM, C_BG);\n'
        '    String info = "Bas: " + (calLow[i] >= 0 ? String(calLow[i]) : String("--")) +\n'
        '                  " cm | Haut: " + (calHigh[i] >= 0 ? String(calHigh[i]) : String("--")) + " cm";\n'
        '    tft.drawString(info.c_str(), 10, ry + 18);\n'
        '  }\n'
        '}\n'
        '\n'
        'void drawCalibScreen() {\n'
        '  tft.fillScreen(C_BG);'
    ),

    # 2. Dans loop(), utiliser updateCalibRaw() au lieu de drawCalibScreen()
    (
        '    // Rafraichir ecran calib en temps reel\n'
        '    if (currentScreen == SCREEN_CALIB) {\n'
        '      drawCalibScreen();\n'
        '    }',
        '    // Rafraichir valeurs brutes sur ecran calib\n'
        '    if (currentScreen == SCREEN_CALIB) {\n'
        '      updateCalibRaw();\n'
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
