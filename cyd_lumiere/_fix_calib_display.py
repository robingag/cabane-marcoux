"""
Fix affichage calibration:
- Agrandir le texte raw (taille 2)
- Afficher aussi quand raw=0
- Ajouter message si capteur ne repond pas
"""

path = r"C:\Users\ryb086\OneDrive - Groupe R.Y. Beaudoin\Bureau\CLAUDE_CODE\cyd_lumiere\src\main.cpp"

with open(path, "r", encoding="utf-8") as f:
    code = f.read()

replacements = [
    # Remplacer la section affichage raw + info calibration
    (
        '    // Basin name + raw value\n'
        '    tft.setTextFont(1); tft.setTextSize(1);\n'
        '    tft.setTextDatum(ML_DATUM);\n'
        '    tft.setTextColor(C_LABEL, C_BG);\n'
        '    tft.drawString(names[i], 10, ry + 4);\n'
        '    tft.setTextDatum(MR_DATUM);\n'
        '    tft.setTextColor(C_AMBER, C_BG);\n'
        '    String rawStr = "Brut: " + String(rawBasin[i]);\n'
        '    tft.drawString(rawStr.c_str(), SW - 10, ry + 4);\n'
        '\n'
        '    // Calibration info\n'
        '    tft.setTextDatum(ML_DATUM);\n'
        '    tft.setTextColor(C_TXT_DIM, C_BG);\n'
        '    String info = "Bas: " + (calLow[i] >= 0 ? String(calLow[i]) : String("--")) +\n'
        '                  " | Haut: " + (calHigh[i] >= 0 ? String(calHigh[i]) : String("--"));\n'
        '    tft.drawString(info.c_str(), 10, ry + 18);',
        '    // Basin name\n'
        '    tft.setTextFont(1); tft.setTextSize(1);\n'
        '    tft.setTextDatum(ML_DATUM);\n'
        '    tft.setTextColor(C_LABEL, C_BG);\n'
        '    tft.drawString(names[i], 10, ry + 2);\n'
        '    // Raw value - gros et visible\n'
        '    tft.setTextSize(2);\n'
        '    tft.setTextDatum(MR_DATUM);\n'
        '    tft.setTextColor(C_CYAN, C_BG);\n'
        '    String rawStr = String(rawBasin[i]) + " cm";\n'
        '    tft.drawString(rawStr.c_str(), SW - 10, ry + 2);\n'
        '    // Calibration info\n'
        '    tft.setTextSize(1);\n'
        '    tft.setTextDatum(ML_DATUM);\n'
        '    tft.setTextColor(C_TXT_DIM, C_BG);\n'
        '    String info = "Bas: " + (calLow[i] >= 0 ? String(calLow[i]) : String("--")) +\n'
        '                  " cm | Haut: " + (calHigh[i] >= 0 ? String(calHigh[i]) : String("--")) + " cm";\n'
        '    tft.drawString(info.c_str(), 10, ry + 18);'
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
