"""
Remettre map bassin a l'original: 0->100
calLow = vide (grande distance) -> 0%
calHigh = plein (petite distance) -> 100%
"""

path = r"C:\Users\ryb086\OneDrive - Groupe R.Y. Beaudoin\Bureau\CLAUDE_CODE\cyd_lumiere\src\main.cpp"

with open(path, "r", encoding="utf-8") as f:
    code = f.read()

replacements = [
    (
        '  // calLow = distance vide (grande), calHigh = distance plein (petite)\n'
        '  // Plus la distance est grande (vide), plus le % est bas\n'
        '  int pct = map(distCm, calLow[idx], calHigh[idx], 100, 0);',
        '  // calLow = distance vide (grande), calHigh = distance plein (petite)\n'
        '  int pct = map(distCm, calLow[idx], calHigh[idx], 0, 100);'
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
