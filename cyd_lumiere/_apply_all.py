"""
Appliquer TOUTES les modifications firmware:
1. Basin 1 en 4-wire (GPIO 22 trig, GPIO 35 echo)
2. Simulateur pulses GPIO 21 (30s-60s)
3. Compteur temps reel dompeur sur TFT
"""

path = r"C:\Users\ryb086\OneDrive - Groupe R.Y. Beaudoin\Bureau\CLAUDE_CODE\cyd_lumiere\src\main.cpp"

with open(path, "r", encoding="utf-8") as f:
    code = f.read()

replacements = [
    # === BASIN 1: 4-WIRE ===
    # 1a. Pin definition
    (
        '#define US1_PIN  22\n',
        '// JSN-SR04T ultrasonic sensor\n'
        '// Bassin 1: 4-wire on GPIO 22 (Trig) + GPIO 35 (Echo) - P3 connector\n'
        '#define US1_TRIG 22\n'
        '#define US1_ECHO 35\n'
        '\n'
        '// Simulateur de pulses dompeur (P3 connecteur)\n'
        '#define SIM_PULSE_PIN 21\n'
    ),

    # 1b. Variables simulation apres lsNewCycle
    (
        'volatile bool lsNewCycle = false;\n',
        'volatile bool lsNewCycle = false;\n'
        '\n'
        '// Simulation pulses: true=actif, false=capteur reel\n'
        'bool simPulse = true;\n'
        'unsigned long simNextToggle = 0;\n'
        'bool simState = false;\n'
    ),

    # 1c. Replace readUltrasonic2Wire function with 4-wire version
    (
        'long readUltrasonic2Wire(int pin) {\n'
        '  pinMode(pin, OUTPUT);\n'
        '  digitalWrite(pin, LOW);\n'
        '  delayMicroseconds(2);\n'
        '  digitalWrite(pin, HIGH);\n'
        '  delayMicroseconds(10);\n'
        '  digitalWrite(pin, LOW);\n'
        '  pinMode(pin, INPUT);\n'
        '  long duration = pulseIn(pin, HIGH, 30000);\n'
        '  if (duration == 0) return -1;\n'
        '  return duration / 58;\n'
        '}',
        'long readUltrasonic4Wire(int trigPin, int echoPin) {\n'
        '  digitalWrite(trigPin, LOW);\n'
        '  delayMicroseconds(2);\n'
        '  digitalWrite(trigPin, HIGH);\n'
        '  delayMicroseconds(10);\n'
        '  digitalWrite(trigPin, LOW);\n'
        '  long duration = pulseIn(echoPin, HIGH, 30000);\n'
        '  if (duration == 0) return -1;\n'
        '  return duration / 58;\n'
        '}'
    ),

    # 1d. Setup: replace ultrasonic comment with proper pinMode
    (
        '  // Ultrasonic sensor: US1_PIN mode change dans readUltrasonic2Wire()',
        '  pinMode(US1_TRIG, OUTPUT);\n'
        '  pinMode(US1_ECHO, INPUT);'
    ),

    # 1e. Loop: replace 2wire call with 4wire
    (
        'readUltrasonic2Wire(US1_PIN)',
        'readUltrasonic4Wire(US1_TRIG, US1_ECHO)'
    ),

    # === SIMULATEUR PULSES ===
    # 2a. Setup: add sim pulse init after BLUE_LED HIGH
    (
        '  digitalWrite(BLUE_LED_PIN, HIGH);  // OFF au demarrage\n',
        '  digitalWrite(BLUE_LED_PIN, HIGH);  // OFF au demarrage\n'
        '\n'
        '  // Simulateur pulses sur GPIO 21\n'
        '  if (simPulse) {\n'
        '    pinMode(SIM_PULSE_PIN, OUTPUT);\n'
        '    digitalWrite(SIM_PULSE_PIN, LOW);\n'
        '    simNextToggle = millis() + random(30000, 60000);\n'
        '    Serial.println("SIM PULSE actif sur GPIO 21 (30-60s)");\n'
        '  }\n'
    ),

    # 2b. Loop: add sim pulse logic before "Process limit switch cycle"
    (
        '  // Process limit switch cycle\n'
        '  if (lsNewCycle) {',
        '  // Simulateur de pulses aleatoires (30s-60s)\n'
        '  if (simPulse && millis() > simNextToggle) {\n'
        '    simState = !simState;\n'
        '    digitalWrite(SIM_PULSE_PIN, simState ? HIGH : LOW);\n'
        '    unsigned long interval = random(30000, 60000);\n'
        '    simNextToggle = millis() + interval;\n'
        '    Serial.printf("SIM: GPIO21=%d, prochain dans %lus\n", simState, interval / 1000);\n'
        '  }\n'
        '\n'
        '  // Process limit switch cycle\n'
        '  if (lsNewCycle) {'
    ),

    # === COMPTEUR TEMPS REEL DOMPEUR ===
    # 3a. Agrandir carte et ajouter compteur
    (
        'void drawDompeurCard() {\n'
        '  int cx = 4, cy = 28, cw = SW - 8, ch = 56;\n'
        '  tft.fillRoundRect(cx, cy, cw, ch, 6, C_CARD);\n'
        '  tft.drawRoundRect(cx, cy, cw, ch, 6, C_BORDER);\n'
        '  tft.setTextFont(1); tft.setTextSize(1);\n'
        '  tft.setTextDatum(TL_DATUM);\n'
        '  tft.setTextColor(C_TXT_GRAY, C_CARD);\n'
        '  tft.drawString("DOMPEUR", cx + 10, cy + 6);\n'
        '  tft.setTextSize(4);\n'
        '  tft.setTextDatum(MC_DATUM);\n'
        '  tft.setTextColor(C_CYAN, C_CARD);\n'
        '  tft.drawString(dompeurTime.c_str(), cx + cw / 2, cy + 36);\n'
        '}',
        'void drawDompeurCard() {\n'
        '  int cx = 4, cy = 28, cw = SW - 8, ch = 72;\n'
        '  tft.fillRoundRect(cx, cy, cw, ch, 6, C_CARD);\n'
        '  tft.drawRoundRect(cx, cy, cw, ch, 6, C_BORDER);\n'
        '  tft.setTextFont(1); tft.setTextSize(1);\n'
        '  tft.setTextDatum(TL_DATUM);\n'
        '  tft.setTextColor(C_TXT_GRAY, C_CARD);\n'
        '  tft.drawString("DOMPEUR", cx + 10, cy + 6);\n'
        '  tft.setTextSize(3);\n'
        '  tft.setTextDatum(MC_DATUM);\n'
        '  tft.setTextColor(C_CYAN, C_CARD);\n'
        '  tft.drawString(dompeurTime.c_str(), cx + cw / 2, cy + 32);\n'
        '  // Compteur temps reel depuis dernier front\n'
        '  unsigned long elapsed = (lsLastEdge > 0) ? (millis() - lsLastEdge) / 1000 : 0;\n'
        '  int eMin = elapsed / 60;\n'
        '  int eSec = elapsed % 60;\n'
        '  char eBuf[8];\n'
        '  snprintf(eBuf, sizeof(eBuf), "%02d:%02d", eMin, eSec);\n'
        '  tft.setTextSize(2);\n'
        '  tft.setTextColor(C_GREEN, C_CARD);\n'
        '  tft.drawString(eBuf, cx + cw / 2, cy + 58);\n'
        '}'
    ),

    # 3b. Refresh dompeur card every second in loop
    (
        '  // LED bleue = etat du limit switch',
        '  // Rafraichir compteur dompeur chaque seconde\n'
        '  static unsigned long lastDompeurRefresh = 0;\n'
        '  if (currentScreen == SCREEN_MAIN && !menuOpen && millis() - lastDompeurRefresh > 1000) {\n'
        '    lastDompeurRefresh = millis();\n'
        '    drawDompeurCard();\n'
        '  }\n'
        '\n'
        '  // LED bleue = etat du limit switch'
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
