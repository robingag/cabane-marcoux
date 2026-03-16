"""
Inverser le graphique TFT: court delai=haut, long delai=bas
- Inverser Y des points
- Inverser labels min/max
- Garder les couleurs: vert=temps augmente(bon), rouge=temps diminue(mauvais)
"""

path = r"C:\Users\ryb086\OneDrive - Groupe R.Y. Beaudoin\Bureau\CLAUDE_CODE\cyd_lumiere\src\main.cpp"

with open(path, "r", encoding="utf-8") as f:
    code = f.read()

replacements = [
    # 1. Inverser labels Y (min en haut, max en bas)
    (
        '  tft.drawString(String(maxV), cx - 2, cy2);\n'
        '  tft.drawString(String(minV), cx - 2, cy2 + ch);',
        '  tft.drawString(String(minV), cx - 2, cy2);\n'
        '  tft.drawString(String(maxV), cx - 2, cy2 + ch);'
    ),

    # 2. Inverser Y des points (enlever le "ch -" pour inverser)
    (
        '    int y1 = cy2 + ch - (long)(dompeurHist[i - 1] - minV) * ch / range;\n'
        '    int x2 = cx + (long)i * cw / (n - 1);\n'
        '    int y2 = cy2 + ch - (long)(dompeurHist[i] - minV) * ch / range;',
        '    int y1 = cy2 + (long)(dompeurHist[i - 1] - minV) * ch / range;\n'
        '    int x2 = cx + (long)i * cw / (n - 1);\n'
        '    int y2 = cy2 + (long)(dompeurHist[i] - minV) * ch / range;'
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
