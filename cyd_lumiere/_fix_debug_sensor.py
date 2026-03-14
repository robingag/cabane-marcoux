"""
Ajouter debug serie pour diagnostic capteur bassin 1
Afficher la lecture brute meme si -1 (erreur)
"""

path = r"C:\Users\ryb086\OneDrive - Groupe R.Y. Beaudoin\Bureau\CLAUDE_CODE\cyd_lumiere\src\main.cpp"

with open(path, "r", encoding="utf-8") as f:
    code = f.read()

replacements = [
    (
        '    long d1 = readUltrasonic4Wire(US1_TRIG, US1_ECHO);\n'
        '    int p1 = distanceToPercent(d1, 0);\n'
        '    if (d1 >= 0) Serial.printf("Bassin 1: %dcm = %d%%\\n", (int)d1, p1);',
        '    long d1 = readUltrasonic4Wire(US1_TRIG, US1_ECHO);\n'
        '    Serial.printf("Bassin 1 raw: %d cm (trig=%d echo=%d)\\n", (int)d1, US1_TRIG, US1_ECHO);\n'
        '    int p1 = distanceToPercent(d1, 0);\n'
        '    if (d1 >= 0) Serial.printf("Bassin 1: %dcm = %d%% (rawBasin=%d)\\n", (int)d1, p1, rawBasin[0]);'
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
