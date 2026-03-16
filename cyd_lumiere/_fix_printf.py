path = r"C:\Users\ryb086\OneDrive - Groupe R.Y. Beaudoin\Bureau\CLAUDE_CODE\cyd_lumiere\src\main.cpp"
with open(path, 'r', encoding='utf-8') as f:
    code = f.read()

# The escaped newline got broken - fix it
code = code.replace('Serial.printf("WiFi scan result: %d networks\n', 'Serial.printf("WiFi scan result: %d networks\n')

with open(path, 'w', encoding='utf-8') as f:
    f.write(code)

print("Fixed printf newline")
