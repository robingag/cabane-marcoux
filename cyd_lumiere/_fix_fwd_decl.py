"""
Ajouter forward declaration pour updateCalibRaw()
"""

path = r"C:\Users\ryb086\OneDrive - Groupe R.Y. Beaudoin\Bureau\CLAUDE_CODE\cyd_lumiere\src\main.cpp"

with open(path, "r", encoding="utf-8") as f:
    code = f.read()

replacements = [
    (
        'void mqttCallback(char* topic, byte* payload, unsigned int length) {',
        '// Forward declarations\n'
        'void updateCalibRaw();\n'
        '\n'
        'void mqttCallback(char* topic, byte* payload, unsigned int length) {'
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
