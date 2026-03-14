"""
LED bleue arriere ON quand limit switch GPIO 27 est actif (LOW)
LED RGB CYD: GPIO 4=R, 16=G, 17=B (active LOW)
"""

path = r"C:\Users\ryb086\OneDrive - Groupe R.Y. Beaudoin\Bureau\CLAUDE_CODE\cyd_lumiere\src\main.cpp"

with open(path, "r", encoding="utf-8") as f:
    code = f.read()

replacements = [
    # 1. Add BLUE_LED_PIN definition after LIMIT_SW_PIN
    (
        '#define LIMIT_SW_PIN 27',
        '#define LIMIT_SW_PIN 27\n#define BLUE_LED_PIN 17  // RGB LED blue (active LOW)'
    ),

    # 2. Init blue LED pin in setup after limit switch
    (
        '  attachInterrupt(digitalPinToInterrupt(LIMIT_SW_PIN), limitSwitchISR, CHANGE);',
        '''  attachInterrupt(digitalPinToInterrupt(LIMIT_SW_PIN), limitSwitchISR, CHANGE);

  // Blue LED (active LOW: LOW=ON, HIGH=OFF)
  pinMode(BLUE_LED_PIN, OUTPUT);
  digitalWrite(BLUE_LED_PIN, HIGH);  // OFF au demarrage'''
    ),

    # 3. In ISR, toggle blue LED based on pin state
    (
        '''void IRAM_ATTR limitSwitchISR() {
  unsigned long now = millis();
  unsigned long delta = now - lsLastEdge;
  if (delta > 200) {  // debounce 200ms
    if (lsLastEdge > 0) {
      lsCycleMs = delta;
      lsNewCycle = true;
    }
    lsLastEdge = now;
  }
}''',
        '''void IRAM_ATTR limitSwitchISR() {
  unsigned long now = millis();
  unsigned long delta = now - lsLastEdge;
  // Blue LED: ON quand switch actif (LOW), OFF quand relache (HIGH)
  digitalWrite(BLUE_LED_PIN, digitalRead(LIMIT_SW_PIN) ? HIGH : LOW);
  if (delta > 200) {  // debounce 200ms
    if (lsLastEdge > 0) {
      lsCycleMs = delta;
      lsNewCycle = true;
    }
    lsLastEdge = now;
  }
}'''
    ),
]

count = 0
for old, new in replacements:
    if old in code:
        code = code.replace(old, new, 1)
        count += 1
        print(f"[OK] Replacement {count}")
    else:
        print(f"[FAIL] Not found: {old[:60]}...")

with open(path, "w", encoding="utf-8") as f:
    f.write(code)

print(f"\nDone: {count}/{len(replacements)} replacements applied")
