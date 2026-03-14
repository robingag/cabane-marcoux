"""
Fix bassin:
1. rawBasin toujours mis a jour (meme si erreur capteur)
2. % toujours correct: petite distance = haut niveau (100%), grande distance = bas niveau (0%)
   Peu importe l'ordre de calibration
"""

path = r"C:\Users\ryb086\OneDrive - Groupe R.Y. Beaudoin\Bureau\CLAUDE_CODE\cyd_lumiere\src\main.cpp"

with open(path, "r", encoding="utf-8") as f:
    code = f.read()

replacements = [
    (
        '// Convertir distance en pourcentage avec calibration 2 points\n'
        '// calLow = distance quand bassin vide (loin), calHigh = distance quand plein (proche)\n'
        'int distanceToPercent(long distCm, int idx) {\n'
        '  if (distCm < 0) return -1; // erreur lecture\n'
        '  rawBasin[idx] = (int)distCm; // toujours mettre a jour la valeur brute\n'
        '  if (calLow[idx] < 0 || calHigh[idx] < 0) {\n'
        '    // Pas calibre: afficher distance brute en cm comme pourcentage temporaire\n'
        '    return constrain((int)distCm, 0, 100);\n'
        '  }\n'
        '  // calLow = distance vide (grande), calHigh = distance plein (petite)\n'
        '  int pct = map(distCm, calLow[idx], calHigh[idx], 0, 100);\n'
        '  return constrain(pct, 0, 100);\n'
        '}',
        '// Convertir distance en pourcentage avec calibration 2 points\n'
        '// Petite distance = bassin plein (100%), Grande distance = bassin vide (0%)\n'
        'int distanceToPercent(long distCm, int idx) {\n'
        '  // Toujours mettre a jour rawBasin, meme si erreur\n'
        '  rawBasin[idx] = (int)distCm;\n'
        '  if (distCm < 0) return -1; // erreur lecture\n'
        '  if (calLow[idx] < 0 || calHigh[idx] < 0) {\n'
        '    // Pas calibre: afficher distance brute en cm comme pourcentage temporaire\n'
        '    return constrain((int)distCm, 0, 100);\n'
        '  }\n'
        '  // Determiner quelle cal est la grande distance (vide) et la petite (plein)\n'
        '  int distVide = max(calLow[idx], calHigh[idx]);  // grande distance = vide\n'
        '  int distPlein = min(calLow[idx], calHigh[idx]); // petite distance = plein\n'
        '  // Grande distance -> 0%, Petite distance -> 100%\n'
        '  int pct = map(distCm, distVide, distPlein, 0, 100);\n'
        '  return constrain(pct, 0, 100);\n'
        '}'
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
