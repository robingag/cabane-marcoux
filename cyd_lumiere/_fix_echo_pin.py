"""
Changer Echo de GPIO 26 a GPIO 35 (P3 connector, input-only)
"""

path = r"C:\Users\ryb086\OneDrive - Groupe R.Y. Beaudoin\Bureau\CLAUDE_CODE\cyd_lumiere\src\main.cpp"

with open(path, "r", encoding="utf-8") as f:
    code = f.read()

replacements = [
    # 1. Pin definition
    (
        '// Bassin 1: 4-wire on GPIO 22 (Trig) + GPIO 26 (Echo) - CN1/P3 connector\n'
        '#define US1_TRIG 22\n'
        '#define US1_ECHO 26',
        '// Bassin 1: 4-wire on GPIO 22 (Trig) + GPIO 35 (Echo) - P3 connector\n'
        '#define US1_TRIG 22\n'
        '#define US1_ECHO 35'
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
