"""
Aligner les seuils de couleur des bassins ESP32 avec le MQTT (index.html).
MQTT: >=91% rouge, >=61% amber, <61% vert
ESP32 TFT drawBasinBar: etait >=50 rouge, >=25 jaune, <25 vert
ESP32 HTML embarque sba(): etait >=50, >=25
"""

path = r"C:\Users\ryb086\OneDrive - Groupe R.Y. Beaudoin\Bureau\CLAUDE_CODE\cyd_lumiere\src\main.cpp"

with open(path, "r", encoding="utf-8") as f:
    code = f.read()

replacements = [
    # 1. drawBasinBar - TFT display colors
    (
        '''    uint16_t bc = C_GREEN;
    if (level >= 50) bc = C_RED;
    else if (level >= 25) bc = C_YELLOW;''',
        '''    uint16_t bc = C_GREEN;
    if (level >= 91) bc = C_RED;
    else if (level >= 61) bc = C_YELLOW;'''
    ),
    # 2. HTML embarque sba() function
    (
        'f.className="bf "+(l>=50?"h":l>=25?"m":"l")',
        'f.className="bf "+(l>=91?"h":l>=61?"m":"l")'
    ),
]

count = 0
for old, new in replacements:
    if old in code:
        code = code.replace(old, new, 1)
        count += 1
        print(f"[OK] {old[:70]}...")
    else:
        print(f"[FAIL] Not found: {old[:70]}...")

with open(path, "w", encoding="utf-8") as f:
    f.write(code)

print(f"\nDone: {count}/{len(replacements)} replacements")
print("Seuils alignes: >=91% rouge, >=61% amber, <61% vert")
