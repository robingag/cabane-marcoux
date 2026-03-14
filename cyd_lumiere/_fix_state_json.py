"""
Ajouter les valeurs raw et % des bassins + dompeur + temp dans /state
"""

path = r"C:\Users\ryb086\OneDrive - Groupe R.Y. Beaudoin\Bureau\CLAUDE_CODE\cyd_lumiere\src\main.cpp"

with open(path, "r", encoding="utf-8") as f:
    code = f.read()

replacements = [
    (
        'void handleState() {\n'
        '  String json = "{\\\"on\\\":" + String(lightOn ? "true" : "false") + "}";\n'
        '  server.send(200, "application/json", json);\n'
        '}',
        'void handleState() {\n'
        '  String json = "{";\n'
        '  json += "\\"on\\":" + String(lightOn ? "true" : "false");\n'
        '  json += ",\\"dompeur\\":\\"" + dompeurTime + "\\"";\n'
        '  json += ",\\"temp\\":" + String(temperature, 1);\n'
        '  json += ",\\"basin1\\":" + String(basin1);\n'
        '  json += ",\\"basin2\\":" + String(basin2);\n'
        '  json += ",\\"basin3\\":" + String(basin3);\n'
        '  json += ",\\"raw1\\":" + String(rawBasin[0]);\n'
        '  json += ",\\"raw2\\":" + String(rawBasin[1]);\n'
        '  json += ",\\"raw3\\":" + String(rawBasin[2]);\n'
        '  json += ",\\"calLow1\\":" + String(calLow[0]);\n'
        '  json += ",\\"calHigh1\\":" + String(calHigh[0]);\n'
        '  json += "}";\n'
        '  server.send(200, "application/json", json);\n'
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
