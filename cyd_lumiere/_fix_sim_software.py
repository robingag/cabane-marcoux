"""
Rendre la simulation de pulses dompeur purement logicielle.
Plus besoin de GPIO - on set directement lsCycleMs et lsNewCycle.
Elimine SIM_PULSE_PIN completement (evite tout conflit GPIO).
"""

path = r"C:\Users\ryb086\OneDrive - Groupe R.Y. Beaudoin\Bureau\CLAUDE_CODE\cyd_lumiere\src\main.cpp"

with open(path, "r", encoding="utf-8") as f:
    code = f.read()

replacements = [
    # 1. Supprimer le #define SIM_PULSE_PIN
    (
        '#define SIM_PULSE_PIN 17',
        '// SIM_PULSE: simulation purement logicielle (pas de GPIO)'
    ),
    # 2. Supprimer simState (plus besoin)
    (
        'bool simState = false;',
        '// simState supprime - simulation logicielle directe'
    ),
    # 3. Remplacer le setup du sim pin par un simple message
    (
        '''  // Simulateur pulses sur GPIO 17 (PAS 21 = TFT backlight!)
  if (simPulse) {
    pinMode(SIM_PULSE_PIN, OUTPUT);
    digitalWrite(SIM_PULSE_PIN, LOW);
    simNextToggle = millis() + random(30000, 60000);
    Serial.println("SIM PULSE actif sur GPIO 17 (30-60s)");
  }''',
        '''  // Simulateur dompeur logiciel (pas de GPIO)
  if (simPulse) {
    simNextToggle = millis() + random(30000, 60000);
    Serial.println("SIM DOMPEUR logiciel actif (30-60s cycles)");
  }'''
    ),
    # 4. Remplacer le toggle GPIO par une simulation logicielle directe
    (
        '''  // Simulateur de pulses aleatoires (30s-60s)
  if (simPulse && millis() > simNextToggle) {
    simState = !simState;
    digitalWrite(SIM_PULSE_PIN, simState ? HIGH : LOW);
    unsigned long interval = random(30000, 60000);
    simNextToggle = millis() + interval;
    Serial.printf("SIM: GPIO17=%d, prochain dans %lus\\n", simState, interval / 1000);
  }''',
        '''  // Simulateur dompeur logiciel (cycle aleatoire 30-60s)
  if (simPulse && millis() > simNextToggle) {
    unsigned long interval = random(30000, 60000);
    lsCycleMs = interval;
    lsNewCycle = true;
    simNextToggle = millis() + random(30000, 60000);
    Serial.printf("SIM DOMPEUR: cycle=%lus, prochain dans %lus\\n", interval / 1000, (simNextToggle - millis()) / 1000);
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
print("\nChangements:")
print("- SIM_PULSE_PIN supprime (plus de GPIO)")
print("- Simulation logicielle: set lsCycleMs + lsNewCycle directement")
print("- Plus aucun conflit GPIO possible")
