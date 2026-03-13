"""
Ajoute la lecture des 3 capteurs JSN-SR04T:
- Bassin 1: 4 fils (Trig=GPIO16, Echo=GPIO17)
- Bassin 2: 2 fils (GPIO22)
- Bassin 3: 2 fils (GPIO26)
+ conversion distance -> pourcentage via calibration 2 points
+ lecture periodique dans loop()
"""

path = r"C:\Users\ryb086\OneDrive - Groupe R.Y. Beaudoin\Bureau\CLAUDE_CODE\cyd_lumiere\src\main.cpp"

with open(path, 'r', encoding='utf-8') as f:
    code = f.read()

replacements = [
    # 1) Ajouter les pin definitions apres LIMIT_SW_PIN
    (
        '#define LIMIT_SW_PIN 27\n',
        '#define LIMIT_SW_PIN 27\n'
        '\n'
        '// JSN-SR04T ultrasonic sensors\n'
        '// Bassin 1: 4-wire (separate Trig/Echo)\n'
        '#define US1_TRIG 16\n'
        '#define US1_ECHO 17\n'
        '// Bassin 2: 2-wire (single pin)\n'
        '#define US2_PIN  22\n'
        '// Bassin 3: 2-wire (single pin)\n'
        '#define US3_PIN  26\n'
        '\n'
        'unsigned long lastUltrasonicRead = 0;\n'
        'const unsigned long US_INTERVAL = 500; // lecture chaque 500ms\n'
        '\n'
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
        '// Lecture 2 fils: meme pin pour trig et echo\n'
        'long readUltrasonic2Wire(int pin) {\n'
        '  // Envoyer pulse trigger\n'
        '  pinMode(pin, OUTPUT);\n'
        '  digitalWrite(pin, LOW);\n'
        '  delayMicroseconds(2);\n'
        '  digitalWrite(pin, HIGH);\n'
        '  delayMicroseconds(10);\n'
        '  digitalWrite(pin, LOW);\n'
        '  // Passer en input pour lire l\'echo\n'
        '  pinMode(pin, INPUT);\n'
        '  long duration = pulseIn(pin, HIGH, 30000); // timeout 30ms\n'
        '  if (duration == 0) return -1;\n'
        '  return duration / 58; // distance en cm\n'
        '}\n'
        '\n'
        '// Convertir distance en pourcentage avec calibration 2 points\n'
        '// calLow = distance quand bassin vide (loin), calHigh = distance quand plein (proche)\n'
        'int distanceToPercent(long distCm, int idx) {\n'
        '  if (distCm < 0) return -1; // erreur lecture\n'
        '  if (calLow[idx] < 0 || calHigh[idx] < 0) {\n'
        '    // Pas calibre: retourner distance brute comme raw\n'
        '    rawBasin[idx] = (int)distCm;\n'
        '    return 0;\n'
        '  }\n'
        '  rawBasin[idx] = (int)distCm;\n'
        '  // calLow = distance vide (grande), calHigh = distance plein (petite)\n'
        '  // Inverser: plus la distance est petite, plus le niveau est haut\n'
        '  int pct = map(distCm, calLow[idx], calHigh[idx], 0, 100);\n'
        '  return constrain(pct, 0, 100);\n'
        '}\n'
    ),

    # 2) Ajouter setup des pins ultrasoniques apres le setup du limit switch
    (
        '  pinMode(LIMIT_SW_PIN, INPUT_PULLUP);\n'
        '  attachInterrupt(digitalPinToInterrupt(LIMIT_SW_PIN), limitSwitchISR, CHANGE);\n',
        '  pinMode(LIMIT_SW_PIN, INPUT_PULLUP);\n'
        '  attachInterrupt(digitalPinToInterrupt(LIMIT_SW_PIN), limitSwitchISR, CHANGE);\n'
        '\n'
        '  // Ultrasonic sensors setup\n'
        '  pinMode(US1_TRIG, OUTPUT);\n'
        '  pinMode(US1_ECHO, INPUT);\n'
        '  // US2_PIN et US3_PIN: pinMode change dynamiquement dans readUltrasonic2Wire\n'
    ),

    # 3) Ajouter lecture periodique dans loop() avant le traitement du limit switch
    (
        '  // Process limit switch cycle\n',
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
        '  }\n'
        '\n'
        '  // Process limit switch cycle\n'
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
        print(f"  Cherche: {repr(old[:80])}")

with open(path, 'w', encoding='utf-8') as f:
    f.write(code)

print(f"\nTotal: {count}/3 remplacements")
