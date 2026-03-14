"""
Ajouter simulateur de pulses sur GPIO 21 (P3) pour tester limit switch GPIO 27
Fronts aleatoires entre 2 et 3 minutes
"""

path = r"C:\Users\ryb086\OneDrive - Groupe R.Y. Beaudoin\Bureau\CLAUDE_CODE\cyd_lumiere\src\main.cpp"

with open(path, "r", encoding="utf-8") as f:
    code = f.read()

replacements = [
    # 1. Ajouter define SIM_PULSE_PIN apres US1_ECHO
    (
        '#define US1_ECHO 35\n',
        '#define US1_ECHO 35\n'
        '\n'
        '// Simulateur de pulses dompeur (P3 connecteur)\n'
        '#define SIM_PULSE_PIN 21\n'
    ),

    # 2. Ajouter variables globales apres lsNewCycle
    (
        'volatile bool lsNewCycle = false;\n',
        'volatile bool lsNewCycle = false;\n'
        '\n'
        '// Simulation pulses: true=actif, false=capteur reel\n'
        'bool simPulse = true;\n'
        'unsigned long simNextToggle = 0;\n'
        'bool simState = false;\n'
    ),

    # 3. Ajouter pinMode dans setup apres BLUE_LED_PIN HIGH
    (
        '  digitalWrite(BLUE_LED_PIN, HIGH);  // OFF au demarrage\n',
        '  digitalWrite(BLUE_LED_PIN, HIGH);  // OFF au demarrage\n'
        '\n'
        '  // Simulateur pulses sur GPIO 21\n'
        '  if (simPulse) {\n'
        '    pinMode(SIM_PULSE_PIN, OUTPUT);\n'
        '    digitalWrite(SIM_PULSE_PIN, LOW);\n'
        '    simNextToggle = millis() + random(120000, 180000);\n'
        '    Serial.println("SIM PULSE actif sur GPIO 21");\n'
        '  }\n'
    ),

    # 4. Ajouter logique simulation dans loop avant "Process limit switch cycle"
    (
        '  // Process limit switch cycle\n'
        '  if (lsNewCycle) {',
        '  // Simulateur de pulses aleatoires (2-3 min)\n'
        '  if (simPulse && millis() > simNextToggle) {\n'
        '    simState = !simState;\n'
        '    digitalWrite(SIM_PULSE_PIN, simState ? HIGH : LOW);\n'
        '    unsigned long interval = random(120000, 180000);\n'
        '    simNextToggle = millis() + interval;\n'
        '    Serial.printf("SIM: GPIO21=%d, prochain dans %lus\n", simState, interval / 1000);\n'
        '  }\n'
        '\n'
        '  // Process limit switch cycle\n'
        '  if (lsNewCycle) {'
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
