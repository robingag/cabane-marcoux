"""
Ajoute la lecture d'un limit switch externe sur GPIO 27 pour mesurer
le temps entre chaque front (rising/falling) du dompeur.
"""
import re

path = r"C:\Users\ryb086\OneDrive - Groupe R.Y. Beaudoin\Bureau\CLAUDE_CODE\cyd_lumiere\src\main.cpp"

with open(path, 'r', encoding='utf-8') as f:
    code = f.read()

replacements = [
    # 1) Add limit switch pin definition and ISR variables after touch pin defines
    (
        '#define T_IRQ  36\n',
        '#define T_IRQ  36\n'
        '\n'
        '// Limit switch for dompeur timing (GPIO 27, P3 connector)\n'
        '#define LIMIT_SW_PIN 27\n'
        'volatile unsigned long lsLastEdge = 0;\n'
        'volatile unsigned long lsCycleMs = 0;\n'
        'volatile bool lsNewCycle = false;\n'
        '\n'
        'void IRAM_ATTR limitSwitchISR() {\n'
        '  unsigned long now = millis();\n'
        '  unsigned long delta = now - lsLastEdge;\n'
        '  if (delta > 200) {  // debounce 200ms\n'
        '    if (lsLastEdge > 0) {\n'
        '      lsCycleMs = delta;\n'
        '      lsNewCycle = true;\n'
        '    }\n'
        '    lsLastEdge = now;\n'
        '  }\n'
        '}\n'
    ),

    # 2) Add limit switch pin setup in setup() after touch IRQ pin
    (
        '  pinMode(T_IRQ, INPUT);\n',
        '  pinMode(T_IRQ, INPUT);\n'
        '\n'
        '  // Limit switch input with pull-up (active LOW)\n'
        '  pinMode(LIMIT_SW_PIN, INPUT_PULLUP);\n'
        '  attachInterrupt(digitalPinToInterrupt(LIMIT_SW_PIN), limitSwitchISR, CHANGE);\n'
    ),

    # 3) Add limit switch processing in loop() before touch reading
    (
        '  int sx, sy;\n'
        '  bool touched = readTouch(sx, sy);\n',
        '  // Process limit switch cycle\n'
        '  if (lsNewCycle) {\n'
        '    lsNewCycle = false;\n'
        '    unsigned long ms = lsCycleMs;\n'
        '    int totalSec = ms / 1000;\n'
        '    int mins = totalSec / 60;\n'
        '    int secs = totalSec % 60;\n'
        '    char buf[8];\n'
        '    snprintf(buf, sizeof(buf), "%02d:%02d", mins, secs);\n'
        '    updateDompeurTime(String(buf));\n'
        '    Serial.printf("Dompeur cycle: %lums = %s\\n", ms, buf);\n'
        '  }\n'
        '\n'
        '  int sx, sy;\n'
        '  bool touched = readTouch(sx, sy);\n'
    ),
]

count = 0
for old, new in replacements:
    if old in code:
        code = code.replace(old, new, 1)
        count += 1
        print(f"OK {count}: remplacement applique")
    else:
        print(f"ERREUR {count+1}: pattern non trouve!")
        print(f"  Cherche: {repr(old[:80])}")

with open(path, 'w', encoding='utf-8') as f:
    f.write(code)

print(f"\nTotal: {count}/3 remplacements appliques")
