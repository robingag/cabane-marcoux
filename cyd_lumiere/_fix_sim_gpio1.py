"""
Remettre la simulation dompeur sur GPIO physique: GPIO 1 (TX) sur connecteur P1.
Annule la version logicielle et remet digitalWrite sur un vrai pin.
"""

path = r"C:\Users\ryb086\OneDrive - Groupe R.Y. Beaudoin\Bureau\CLAUDE_CODE\cyd_lumiere\src\main.cpp"

with open(path, "r", encoding="utf-8") as f:
    code = f.read()

replacements = [
    # 1. Remettre le #define avec GPIO 1
    (
        '// SIM_PULSE: simulation purement logicielle (pas de GPIO)',
        '#define SIM_PULSE_PIN 1  // GPIO 1 = TX sur connecteur P1'
    ),
    # 2. Remettre simState
    (
        '// simState supprime - simulation logicielle directe',
        'bool simState = false;'
    ),
    # 3. Remettre le setup GPIO
    (
        '''  // Simulateur dompeur logiciel (pas de GPIO)
  if (simPulse) {
    simNextToggle = millis() + random(30000, 60000);
    Serial.println("SIM DOMPEUR logiciel actif (30-60s cycles)");
  }''',
        '''  // Simulateur pulses sur GPIO 1 (TX/P1)
  if (simPulse) {
    pinMode(SIM_PULSE_PIN, OUTPUT);
    digitalWrite(SIM_PULSE_PIN, LOW);
    simNextToggle = millis() + random(30000, 60000);
    Serial.println("SIM PULSE actif sur GPIO 1/TX (30-60s)");
  }'''
    ),
    # 4. Remettre le toggle GPIO dans loop
    (
        '''  // Simulateur dompeur logiciel (cycle aleatoire 30-60s)
  if (simPulse && millis() > simNextToggle) {
    unsigned long interval = random(30000, 60000);
    lsCycleMs = interval;
    lsNewCycle = true;
    simNextToggle = millis() + random(30000, 60000);
    Serial.printf("SIM DOMPEUR: cycle=%lus, prochain dans %lus\\n", interval / 1000, (simNextToggle - millis()) / 1000);
  }''',
        '''  // Simulateur de pulses aleatoires (30s-60s)
  if (simPulse && millis() > simNextToggle) {
    simState = !simState;
    digitalWrite(SIM_PULSE_PIN, simState ? HIGH : LOW);
    unsigned long interval = random(30000, 60000);
    simNextToggle = millis() + interval;
    Serial.printf("SIM: GPIO1=%d, prochain dans %lus\\n", simState, interval / 1000);
  }'''
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
print("\nSIM_PULSE_PIN = GPIO 1 (TX) sur connecteur P1")
