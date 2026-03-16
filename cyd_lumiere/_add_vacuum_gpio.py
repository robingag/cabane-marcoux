"""
Raccorde le vacuum a GPIO 4:
- Define VACUUM_PIN
- pinMode dans setup()
- digitalWrite a chaque changement de lightOn
- Ajouter le slider sur l'ecran principal
"""

path = r"C:\Users\ryb086\OneDrive - Groupe R.Y. Beaudoin\Bureau\CLAUDE_CODE\cyd_lumiere\src\main.cpp"

with open(path, 'r', encoding='utf-8') as f:
    code = f.read()

replacements = [
    # 1) Definir VACUUM_PIN apres US3_PIN
    (
        '#define US3_PIN  26\n',
        '#define US3_PIN  26\n'
        '\n'
        '// Vacuum relay output\n'
        '#define VACUUM_PIN 4\n'
    ),

    # 2) pinMode dans setup() apres les ultrasonic setup
    (
        '  // US2_PIN et US3_PIN: pinMode change dynamiquement dans readUltrasonic2Wire\n',
        '  // US2_PIN et US3_PIN: pinMode change dynamiquement dans readUltrasonic2Wire\n'
        '\n'
        '  // Vacuum relay output (OFF au demarrage)\n'
        '  pinMode(VACUUM_PIN, OUTPUT);\n'
        '  digitalWrite(VACUUM_PIN, LOW);\n'
    ),

    # 3) MQTT callback toggle: ajouter digitalWrite
    (
        '    if (msg == "toggle") {\n'
        '      lightOn = !lightOn;\n'
        '      publishState();\n'
        '      Serial.printf(">>> MQTT: Vacuum %s\\n", lightOn ? "ON" : "OFF");\n',
        '    if (msg == "toggle") {\n'
        '      lightOn = !lightOn;\n'
        '      digitalWrite(VACUUM_PIN, lightOn ? HIGH : LOW);\n'
        '      publishState();\n'
        '      Serial.printf(">>> MQTT: Vacuum %s\\n", lightOn ? "ON" : "OFF");\n'
    ),

    # 4) MQTT callback on:
    (
        '    } else if (msg == "on") {\n'
        '      lightOn = true;\n'
        '      publishState();\n',
        '    } else if (msg == "on") {\n'
        '      lightOn = true;\n'
        '      digitalWrite(VACUUM_PIN, HIGH);\n'
        '      publishState();\n'
    ),

    # 5) MQTT callback off:
    (
        '    } else if (msg == "off") {\n'
        '      lightOn = false;\n'
        '      publishState();\n',
        '    } else if (msg == "off") {\n'
        '      lightOn = false;\n'
        '      digitalWrite(VACUUM_PIN, LOW);\n'
        '      publishState();\n'
    ),

    # 6) Web toggle handler: ajouter digitalWrite
    (
        '  lightOn = !lightOn;\n'
        '  if (currentScreen == SCREEN_MAIN) drawVacuumBtn();\n',
        '  lightOn = !lightOn;\n'
        '  digitalWrite(VACUUM_PIN, lightOn ? HIGH : LOW);\n'
        '  if (currentScreen == SCREEN_MAIN) drawVacuumBtn();\n'
    ),

    # 7) Ajouter le slider vacuum + touch sur l'ecran principal
    (
        'void drawMainScreen() {\n'
        '  tft.fillScreen(C_BG);\n'
        '  drawHeader();\n'
        '  drawDompeurCard();\n'
        '  drawBasinCards();\n'
        '}',
        'void drawMainScreen() {\n'
        '  tft.fillScreen(C_BG);\n'
        '  drawHeader();\n'
        '  drawDompeurCard();\n'
        '  drawBasinCards();\n'
        '  drawVacuumBtn();\n'
        '}'
    ),

    # 8) Ajouter touch vacuum dans handleMainTouch
    (
        '  // Menu icon (top-right)\n'
        '  if (tx >= 280 && ty <= 24) {\n'
        '    drawDropdownMenu();\n'
        '    return;\n'
        '  }\n'
        '}',
        '  // Menu icon (top-right)\n'
        '  if (tx >= 280 && ty <= 24) {\n'
        '    drawDropdownMenu();\n'
        '    return;\n'
        '  }\n'
        '  // Vacuum slider touch\n'
        '  if (ty >= 214 && ty <= 236) {\n'
        '    lightOn = !lightOn;\n'
        '    digitalWrite(VACUUM_PIN, lightOn ? HIGH : LOW);\n'
        '    drawVacuumBtn();\n'
        '    publishState();\n'
        '    Serial.printf(">>> Touch: Vacuum %s\\n", lightOn ? "ON" : "OFF");\n'
        '    return;\n'
        '  }\n'
        '}'
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

print(f"\nTotal: {count}/8 remplacements")
