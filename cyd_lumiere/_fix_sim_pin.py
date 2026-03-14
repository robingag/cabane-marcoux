"""
Changer SIM_PULSE_PIN de GPIO 21 (conflit TFT_BL!) a GPIO 17
GPIO 21 = backlight ecran TFT, donc quand simState=LOW, ecran s'eteint!
GPIO 17 est libre sur le connecteur P3
"""

path = r"C:\Users\ryb086\OneDrive - Groupe R.Y. Beaudoin\Bureau\CLAUDE_CODE\cyd_lumiere\src\main.cpp"

with open(path, "r", encoding="utf-8") as f:
    code = f.read()

replacements = [
    ('#define SIM_PULSE_PIN 21', '#define SIM_PULSE_PIN 17'),
    ('// Simulateur pulses sur GPIO 21', '// Simulateur pulses sur GPIO 17 (PAS 21 = TFT backlight!)'),
    ('Serial.println("SIM PULSE actif sur GPIO 21 (30-60s)");', 'Serial.println("SIM PULSE actif sur GPIO 17 (30-60s)");'),
    ('Serial.printf("SIM: GPIO21=%d', 'Serial.printf("SIM: GPIO17=%d'),
]

count = 0
for old, new in replacements:
    if old in code:
        code = code.replace(old, new, 1)
        count += 1
        print(f"[OK] {old[:60]}...")
    else:
        print(f"[FAIL] Not found: {old[:60]}...")

with open(path, "w", encoding="utf-8") as f:
    f.write(code)

print(f"\nDone: {count}/{len(replacements)} replacements")
