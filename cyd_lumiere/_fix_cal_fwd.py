"""
Fix: remplacer drawCalibScreen par updateCalibRaw dans le handler MQTT cal
"""

path = r"C:\Users\ryb086\OneDrive - Groupe R.Y. Beaudoin\Bureau\CLAUDE_CODE\cyd_lumiere\src\main.cpp"

with open(path, "r", encoding="utf-8") as f:
    code = f.read()

replacements = [
    (
        '      if (currentScreen == SCREEN_CALIB) drawCalibScreen();\n'
        '    }\n'
        '  }\n'
        '}\n'
        '\n'
        'void mqttConnect()',
        '      if (currentScreen == SCREEN_CALIB) updateCalibRaw();\n'
        '    }\n'
        '  }\n'
        '}\n'
        '\n'
        'void mqttConnect()'
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
