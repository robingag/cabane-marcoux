"""
Inverser les couleurs de la courbe de tendance:
- Monte = ROUGE (temps augmente = mauvais)
- Descend = VERT (temps diminue = bon)
"""

path = r"C:\Users\ryb086\OneDrive - Groupe R.Y. Beaudoin\Bureau\CLAUDE_CODE\cyd_lumiere\src\main.cpp"

with open(path, "r", encoding="utf-8") as f:
    code = f.read()

replacements = [
    # 1. Inverser couleur segments: monte=rouge, descend=vert
    (
        '    // Color: green if going up, red if going down\n'
        '    uint16_t lc = (dompeurHist[i] >= dompeurHist[i - 1]) ? C_GREEN : C_RED;',
        '    // Color: red if going up (bad), green if going down (good)\n'
        '    uint16_t lc = (dompeurHist[i] >= dompeurHist[i - 1]) ? C_RED : C_GREEN;'
    ),

    # 2. Inverser couleur fleche tendance: hausse=rouge, baisse=vert
    (
        '  uint16_t arrowC = up ? C_GREEN : C_RED;\n'
        '  int ax = gx + gw - 16, ay = gy + 3;\n'
        '  if (up) { // arrow up = good (time increasing)\n'
        '    tft.fillTriangle(ax, ay + 2, ax - 4, ay + 8, ax + 4, ay + 8, arrowC);\n'
        '  } else { // arrow down = bad (time decreasing)\n'
        '    tft.fillTriangle(ax, ay + 8, ax - 4, ay + 2, ax + 4, ay + 2, arrowC);',
        '  uint16_t arrowC = up ? C_RED : C_GREEN;\n'
        '  int ax = gx + gw - 16, ay = gy + 3;\n'
        '  if (up) { // arrow up = bad (time increasing)\n'
        '    tft.fillTriangle(ax, ay + 2, ax - 4, ay + 8, ax + 4, ay + 8, arrowC);\n'
        '  } else { // arrow down = good (time decreasing)\n'
        '    tft.fillTriangle(ax, ay + 8, ax - 4, ay + 2, ax + 4, ay + 2, arrowC);'
    ),
]

count = 0
for old, new in replacements:
    if old in code:
        code = code.replace(old, new, 1)
        count += 1
        print(f"[OK] Replacement {count}")
    else:
        print(f"[FAIL] Not found: {old[:70]}...")

with open(path, "w", encoding="utf-8") as f:
    f.write(code)

print(f"\nDone: {count}/{len(replacements)} replacements applied")
