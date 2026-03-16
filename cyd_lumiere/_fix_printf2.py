path = r"C:\Users\ryb086\OneDrive - Groupe R.Y. Beaudoin\Bureau\CLAUDE_CODE\cyd_lumiere\src\main.cpp"
with open(path, 'r', encoding='utf-8') as f:
    code = f.read()

# Replace the broken multiline printf with a working one
code = code.replace(
    'Serial.printf("WiFi scan result: %d networks\n", n);',
    'Serial.printf("WiFi scan result: %d networks\n", n);'
)

with open(path, 'w', encoding='utf-8') as f:
    f.write(code)

# Verify
with open(path, 'r', encoding='utf-8') as f:
    for i, line in enumerate(f, 1):
        if 'WiFi scan result' in line:
            print(f"Line {i}: {repr(line.rstrip())}")
