"""
Corrige les GPIO pour correspondre au hardware reel du CYD:
- Retire GPIO 4 (LED rouge), 16 (LED verte), 17 (LED bleue), 26 (speaker)
- Garde GPIO 27 = limit switch (CN1)
- Bassin 1 = GPIO 22 en mode 2 fils (CN1/P3)
- Bassins 2-3 = MQTT seulement (pas de capteur physique)
- Vacuum = MQTT seulement (pas de GPIO)
"""

path = r"C:\Users\ryb086\OneDrive - Groupe R.Y. Beaudoin\Bureau\CLAUDE_CODE\cyd_lumiere\src\main.cpp"

with open(path, 'r', encoding='utf-8') as f:
    code = f.read()

replacements = [
    # 1) Remplacer les pin definitions ultrasoniques
    (
        '// JSN-SR04T ultrasonic sensors\n'
        '// Bassin 1: 4-wire (separate Trig/Echo)\n'
        '#define US1_TRIG 16\n'
        '#define US1_ECHO 17\n'
        '// Bassin 2: 2-wire (single pin)\n'
        '#define US2_PIN  22\n'
        '// Bassin 3: 2-wire (single pin)\n'
        '#define US3_PIN  26\n'
        '\n'
        '// Vacuum relay output\n'
        '#define VACUUM_PIN 4\n',

        '// JSN-SR04T ultrasonic sensor\n'
        '// Bassin 1: 2-wire on GPIO 22 (CN1/P3 connector)\n'
        '#define US1_PIN  22\n'
    ),

    # 2) Remplacer les fonctions de lecture ultrasoniques (retirer 4-wire, garder 2-wire)
    (
        '// Lecture 4 fils: trig et echo separes\n'
        'long readUltrasonic4Wire(int trigPin, int echoPin) {\n'
        '  digitalWrite(trigPin, LOW);\n'
        '  delayMicroseconds(2);\n'
        '  digitalWrite(trigPin, HIGH);\n'
        '  delayMicroseconds(10);\n'
        '  digitalWrite(trigPin, LOW);\n'
        '  long duration = pulseIn(echoPin, HIGH, 30000); // timeout 30ms (~5m)\n'
        '  if (duration == 0) return -1; // pas d\'echo\n'
        '  return duration / 58; // distance en cm\n'
        '}\n'
        '\n'
        '// Lecture 2 fils: meme pin pour trig et echo\n',

        '// Lecture 2 fils: meme pin pour trig et echo\n'
    ),

    # 3) Remplacer le setup des pins ultrasoniques + vacuum
    (
        '  // Ultrasonic sensors setup\n'
        '  pinMode(US1_TRIG, OUTPUT);\n'
        '  pinMode(US1_ECHO, INPUT);\n'
        '  // US2_PIN et US3_PIN: pinMode change dynamiquement dans readUltrasonic2Wire\n'
        '\n'
        '  // Vacuum relay output (OFF au demarrage)\n'
        '  pinMode(VACUUM_PIN, OUTPUT);\n'
        '  digitalWrite(VACUUM_PIN, LOW);\n',

        '  // Ultrasonic sensor: US1_PIN mode change dans readUltrasonic2Wire()\n'
    ),

    # 4) Remplacer la lecture periodique (seulement bassin 1)
    (
        '  // Lecture periodique des capteurs ultrasoniques\n'
        '  if (millis() - lastUltrasonicRead >= US_INTERVAL) {\n'
        '    lastUltrasonicRead = millis();\n'
        '    bool changed = false;\n'
        '\n'
        '    // Bassin 1 (4 fils)\n'
        '    long d1 = readUltrasonic4Wire(US1_TRIG, US1_ECHO);\n'
        '    int p1 = distanceToPercent(d1, 0);\n'
        '    if (p1 >= 0 && p1 != basin1) { basin1 = p1; changed = true; }\n'
        '\n'
        '    // Bassin 2 (2 fils)\n'
        '    long d2 = readUltrasonic2Wire(US2_PIN);\n'
        '    int p2 = distanceToPercent(d2, 1);\n'
        '    if (p2 >= 0 && p2 != basin2) { basin2 = p2; changed = true; }\n'
        '\n'
        '    // Bassin 3 (2 fils)\n'
        '    long d3 = readUltrasonic2Wire(US3_PIN);\n'
        '    int p3 = distanceToPercent(d3, 2);\n'
        '    if (p3 >= 0 && p3 != basin3) { basin3 = p3; changed = true; }\n'
        '\n'
        '    if (changed) {\n'
        '      // Mettre a jour affichage\n'
        '      if (currentScreen == SCREEN_MAIN && !menuOpen) drawBasinCards();\n'
        '      // Publier sur MQTT\n'
        '      if (mqtt.connected()) {\n'
        '        mqtt.publish(mqttTopicBasin1.c_str(), String(basin1).c_str(), true);\n'
        '        mqtt.publish(mqttTopicBasin2.c_str(), String(basin2).c_str(), true);\n'
        '        mqtt.publish(mqttTopicBasin3.c_str(), String(basin3).c_str(), true);\n'
        '      }\n'
        '      Serial.printf("Bassins: %dcm=%d%% | %dcm=%d%% | %dcm=%d%%\\n",\n'
        '                    (int)d1, basin1, (int)d2, basin2, (int)d3, basin3);\n'
        '    }\n'
        '  }\n',

        '  // Lecture periodique capteur ultrasonique (bassin 1 seulement)\n'
        '  if (millis() - lastUltrasonicRead >= US_INTERVAL) {\n'
        '    lastUltrasonicRead = millis();\n'
        '\n'
        '    long d1 = readUltrasonic2Wire(US1_PIN);\n'
        '    int p1 = distanceToPercent(d1, 0);\n'
        '    if (p1 >= 0 && p1 != basin1) {\n'
        '      basin1 = p1;\n'
        '      if (currentScreen == SCREEN_MAIN && !menuOpen) drawBasinCards();\n'
        '      if (mqtt.connected()) {\n'
        '        mqtt.publish(mqttTopicBasin1.c_str(), String(basin1).c_str(), true);\n'
        '      }\n'
        '      Serial.printf("Bassin 1: %dcm = %d%%\\n", (int)d1, basin1);\n'
        '    }\n'
        '  }\n'
    ),

    # 5) Retirer digitalWrite(VACUUM_PIN) du MQTT callback toggle
    (
        '      lightOn = !lightOn;\n'
        '      digitalWrite(VACUUM_PIN, lightOn ? HIGH : LOW);\n'
        '      publishState();\n'
        '      Serial.printf(">>> MQTT: Vacuum %s\\n", lightOn ? "ON" : "OFF");',

        '      lightOn = !lightOn;\n'
        '      publishState();\n'
        '      Serial.printf(">>> MQTT: Vacuum %s\\n", lightOn ? "ON" : "OFF");'
    ),

    # 6) Retirer digitalWrite(VACUUM_PIN) du MQTT callback on
    (
        '      lightOn = true;\n'
        '      digitalWrite(VACUUM_PIN, HIGH);\n'
        '      publishState();',

        '      lightOn = true;\n'
        '      publishState();'
    ),

    # 7) Retirer digitalWrite(VACUUM_PIN) du MQTT callback off
    (
        '      lightOn = false;\n'
        '      digitalWrite(VACUUM_PIN, LOW);\n'
        '      publishState();',

        '      lightOn = false;\n'
        '      publishState();'
    ),

    # 8) Retirer digitalWrite(VACUUM_PIN) du web toggle
    (
        '  lightOn = !lightOn;\n'
        '  digitalWrite(VACUUM_PIN, lightOn ? HIGH : LOW);\n'
        '  if (currentScreen == SCREEN_MAIN) drawVacuumBtn();',

        '  lightOn = !lightOn;\n'
        '  if (currentScreen == SCREEN_MAIN) drawVacuumBtn();'
    ),

    # 9) Retirer digitalWrite(VACUUM_PIN) du touch vacuum
    (
        '    lightOn = !lightOn;\n'
        '    digitalWrite(VACUUM_PIN, lightOn ? HIGH : LOW);\n'
        '    drawVacuumBtn();',

        '    lightOn = !lightOn;\n'
        '    drawVacuumBtn();'
    ),
]

count = 0
for old, new in replacements:
    if old in code:
        code = code.replace(old, new, 1)
        count += 1
        print(f"OK {count}: remplacement applique")
    else:
        count += 1
        print(f"ERREUR {count}: pattern non trouve!")
        print(f"  Cherche: {repr(old[:60])}")

with open(path, 'w', encoding='utf-8') as f:
    f.write(code)

print(f"\nTotal: {count}/9 remplacements")
