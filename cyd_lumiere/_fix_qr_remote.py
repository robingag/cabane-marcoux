import re

path = r"C:\Users\ryb086\OneDrive - Groupe R.Y. Beaudoin\Bureau\CLAUDE_CODE\cyd_lumiere\src\main.cpp"
with open(path, 'r', encoding='utf-8') as f:
    code = f.read()

# Fix QR Remote URL to point to cyd_lumiere/index.html
old = 'url = "https://robingag.github.io/cabane-marcoux/?id=" + deviceId;'
new = 'url = "https://robingag.github.io/cabane-marcoux/cyd_lumiere/index.html?id=" + deviceId;'
code = code.replace(old, new)

with open(path, 'w', encoding='utf-8') as f:
    f.write(code)

print("QR Remote URL fixed")
