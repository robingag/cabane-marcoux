"""
Fix LED bleue: deplacer dans loop() + blink test au boot
- Retirer digitalWrite de l'ISR
- Ajouter lecture pin dans loop()
- Ajouter 2x blink au demarrage
"""

path = r"C:\Users\ryb086\OneDrive - Groupe R.Y. Beaudoin\Bureau\CLAUDE_CODE\cyd_lumiere\src\main.cpp"

with open(path, "r", encoding="utf-8") as f:
    code = f.read()

replacements = [
    # 1. Retirer digitalWrite de l'ISR
    (
        '''void IRAM_ATTR limitSwitchISR() {
  unsigned long now = millis();
  unsigned long delta = now - lsLastEdge;
  // Blue LED: ON quand switch actif (LOW), OFF quand relache (HIGH)
  digitalWrite(BLUE_LED_PIN, digitalRead(LIMIT_SW_PIN) ? HIGH : LOW);
  if (delta > 200) {  // debounce 200ms''',
        '''void IRAM_ATTR limitSwitchISR() {
  unsigned long now = millis();
  unsigned long delta = now - lsLastEdge;
  if (delta > 200) {  // debounce 200ms'''
    ),

    # 2. Ajouter blink test apres init LED
    (
        '''  // Blue LED (active LOW: LOW=ON, HIGH=OFF)
  pinMode(BLUE_LED_PIN, OUTPUT);
  digitalWrite(BLUE_LED_PIN, HIGH);  // OFF au demarrage''',
        '''  // Blue LED (active LOW: LOW=ON, HIGH=OFF)
  pinMode(BLUE_LED_PIN, OUTPUT);
  digitalWrite(BLUE_LED_PIN, HIGH);  // OFF au demarrage
  // Test blink: 2x bleu rapide pour confirmer que la LED fonctionne
  for (int i = 0; i < 2; i++) {
    digitalWrite(BLUE_LED_PIN, LOW);   // ON
    delay(150);
    digitalWrite(BLUE_LED_PIN, HIGH);  // OFF
    delay(150);
  }'''
    ),

    # 3. Ajouter lecture LED dans loop() apres le bloc lsNewCycle
    (
        '''    Serial.printf("Dompeur cycle: %lums = %s\\n", ms, buf);
  }''',
        '''    Serial.printf("Dompeur cycle: %lums = %s\\n", ms, buf);
  }

  // LED bleue = etat du limit switch (LOW=switch ferme=LED ON, HIGH=ouvert=LED OFF)
  digitalWrite(BLUE_LED_PIN, digitalRead(LIMIT_SW_PIN) ? HIGH : LOW);'''
    ),
]

count = 0
for old, new in replacements:
    if old in code:
        code = code.replace(old, new, 1)
        count += 1
        print(f"[OK] Replacement {count}")
    else:
        print(f"[FAIL] Not found: {old[:70]}...")

with open(path, "w", encoding="utf-8") as f:
    f.write(code)

print(f"\nDone: {count}/{len(replacements)} replacements applied")
