"""
Inverse les couleurs de la courbe de tendance:
- Vert quand la valeur monte (temps augmente)
- Rouge quand la valeur descend (temps diminue)
- Fleche verte vers le haut, rouge vers le bas
"""

path = r"C:\Users\ryb086\OneDrive - Groupe R.Y. Beaudoin\Bureau\CLAUDE_CODE\cyd_lumiere\src\main.cpp"

with open(path, 'r', encoding='utf-8') as f:
    code = f.read()

replacements = [
    # 1) Ligne du graphique TFT: inverser vert/rouge
    (
        '    // Color: green if going down, red if going up\n'
        '    uint16_t lc = (dompeurHist[i] <= dompeurHist[i - 1]) ? C_GREEN : C_RED;',
        '    // Color: green if going up, red if going down\n'
        '    uint16_t lc = (dompeurHist[i] >= dompeurHist[i - 1]) ? C_GREEN : C_RED;'
    ),
    # 2) Fleche de tendance TFT: inverser direction/couleur
    (
        '  // Trend arrow (last vs first)\n'
        '  bool up = dompeurHist[n - 1] > dompeurHist[0];\n'
        '  uint16_t arrowC = up ? C_RED : C_GREEN;\n'
        '  int ax = gx + gw - 16, ay = gy + 3;\n'
        '  if (up) { // arrow up = bad (time increasing)\n'
        '    tft.fillTriangle(ax, ay + 2, ax - 4, ay + 8, ax + 4, ay + 8, arrowC);\n'
        '  } else { // arrow down = good\n'
        '    tft.fillTriangle(ax, ay + 8, ax - 4, ay + 2, ax + 4, ay + 2, arrowC);\n'
        '  }',
        '  // Trend arrow (last vs first)\n'
        '  bool up = dompeurHist[n - 1] > dompeurHist[0];\n'
        '  uint16_t arrowC = up ? C_GREEN : C_RED;\n'
        '  int ax = gx + gw - 16, ay = gy + 3;\n'
        '  if (up) { // arrow up = good (time increasing)\n'
        '    tft.fillTriangle(ax, ay + 2, ax - 4, ay + 8, ax + 4, ay + 8, arrowC);\n'
        '  } else { // arrow down = bad (time decreasing)\n'
        '    tft.fillTriangle(ax, ay + 8, ax - 4, ay + 2, ax + 4, ay + 2, arrowC);\n'
        '  }'
    ),
    # 3) Page web remote: ligne du graphique - inverser vert/rouge
    (
        'ctx.strokeStyle=hist[i]<=hist[i-1]?"#4f4":"#f44"',
        'ctx.strokeStyle=hist[i]>=hist[i-1]?"#4f4":"#f44"'
    ),
    # 4) Page web remote: fleche de tendance - inverser
    (
        'if(hist[n-1]>hist[0]){a.textContent="\\u25B2";a.className="ar u"}else{a.textContent="\\u25BC";a.className="ar d"}',
        'if(hist[n-1]>hist[0]){a.textContent="\\u25B2";a.className="ar d"}else{a.textContent="\\u25BC";a.className="ar u"}'
    ),
]

count = 0
for old, new in replacements:
    if old in code:
        code = code.replace(old, new, 1)
        count += 1
        print(f"OK {count}: remplacement applique")
    else:
        count += 1
        print(f"ERREUR {count}: pattern non trouve!")
        print(f"  Cherche: {repr(old[:80])}")

with open(path, 'w', encoding='utf-8') as f:
    f.write(code)

print(f"\nTotal: {count}/4 remplacements")
