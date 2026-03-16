path = r"C:\Users\ryb086\OneDrive - Groupe R.Y. Beaudoin\Bureau\CLAUDE_CODE\cyd_lumiere\src\main.cpp"
with open(path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

for i, line in enumerate(lines):
    if 'Serial.printf("WiFi scan result: %d networks' in line:
        # This line + next line form the broken printf
        # Replace with single correct line
        lines[i] = '  Serial.printf("WiFi scan result: %d networks\n", n);\n'
        # Remove the dangling next line '", n);'
        if i+1 < len(lines) and '", n);' in lines[i+1]:
            lines[i+1] = ''
        break

with open(path, 'w', encoding='utf-8') as f:
    f.writelines(lines)

# Verify
with open(path, 'r', encoding='utf-8') as f:
    for j, line in enumerate(f, 1):
        if 'WiFi scan result' in line and 'printf' in line:
            print(f"Line {j}: {repr(line.rstrip())}")
