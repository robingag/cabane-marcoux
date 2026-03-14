"""
Rediriger la page locale (/) vers la page GitHub Pages avec le device ID
"""

path = r"C:\Users\ryb086\OneDrive - Groupe R.Y. Beaudoin\Bureau\CLAUDE_CODE\cyd_lumiere\src\main.cpp"

with open(path, "r", encoding="utf-8") as f:
    code = f.read()

replacements = [
    (
        'void handleRoot() {\n'
        '  server.send(200, "text/html", WEBPAGE);\n'
        '}',
        'void handleRoot() {\n'
        '  // Rediriger vers la page GitHub Pages (meme interface que Android)\n'
        '  String url = "https://robingag.github.io/cabane-marcoux/?id=" + deviceId;\n'
        '  server.sendHeader("Location", url, true);\n'
        '  server.send(302, "text/plain", "");\n'
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
