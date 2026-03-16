path = r"C:\Users\ryb086\OneDrive - Groupe R.Y. Beaudoin\Bureau\CLAUDE_CODE\cyd_lumiere\src\main.cpp"
with open(path, 'r', encoding='utf-8') as f:
    code = f.read()

# The sim pulse and ISR are on different pins — sim can't trigger the ISR
# Fix: when simPulse is true, process the cycle directly in the sim code
# instead of relying on the ISR

old_sim = '''  // Simulateur de pulses aleatoires (30s-60s)
  if (simPulse && millis() > simNextToggle) {
    simState = !simState;
    digitalWrite(SIM_PULSE_PIN, simState ? HIGH : LOW);
    unsigned long interval = random(30000, 60000);
    simNextToggle = millis() + interval;
    Serial.printf("SIM: GPIO1=%d, prochain dans %lus\n", simState, interval / 1000);
  }'''

new_sim = '''  // Simulateur de pulses aleatoires (30s-60s)
  static unsigned long simLastEdge = 0;
  if (simPulse && millis() > simNextToggle) {
    simState = !simState;
    digitalWrite(SIM_PULSE_PIN, simState ? HIGH : LOW);
    unsigned long now = millis();
    if (simLastEdge > 0) {
      unsigned long ms = now - simLastEdge;
      int totalSec = ms / 1000;
      int mins = totalSec / 60;
      int secs = totalSec % 60;
      char buf[8];
      snprintf(buf, sizeof(buf), "%02d:%02d", mins, secs);
      updateDompeurTime(String(buf));
      Serial.printf("SIM Dompeur: %lums = %s\n", ms, buf);
    }
    simLastEdge = now;
    unsigned long interval = random(30000, 60000);
    simNextToggle = millis() + interval;
    Serial.printf("SIM: GPIO1=%d, prochain dans %lus\n", simState, interval / 1000);
  }'''

code = code.replace(old_sim, new_sim)

with open(path, 'w', encoding='utf-8') as f:
    f.write(code)

print("Fixed: sim pulse now directly updates dompeur time")
