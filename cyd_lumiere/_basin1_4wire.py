"""
Bassin 1: passer de mode 2 fils a mode 4 fils (JSN-SR04T)
Trig = GPIO 22, Echo = GPIO 26
"""

path = r"C:\Users\ryb086\OneDrive - Groupe R.Y. Beaudoin\Bureau\CLAUDE_CODE\cyd_lumiere\src\main.cpp"

with open(path, "r", encoding="utf-8") as f:
    code = f.read()

replacements = [
    # 1. Pin definitions
    (
        '// JSN-SR04T ultrasonic sensor\n'
        '// Bassin 1: 2-wire on GPIO 22 (CN1/P3 connector)\n'
        '#define US1_PIN  22',
        '// JSN-SR04T ultrasonic sensor\n'
        '// Bassin 1: 4-wire on GPIO 22 (Trig) + GPIO 26 (Echo) - CN1/P3 connector\n'
        '#define US1_TRIG 22\n'
        '#define US1_ECHO 26'
    ),

    # 2. Replace 2-wire function with 4-wire function
    (
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
        '}',
        '// Lecture 4 fils: trig et echo sur pins separes\n'
        'long readUltrasonic4Wire(int trigPin, int echoPin) {\n'
        '  digitalWrite(trigPin, LOW);\n'
        '  delayMicroseconds(2);\n'
        '  digitalWrite(trigPin, HIGH);\n'
        '  delayMicroseconds(10);\n'
        '  digitalWrite(trigPin, LOW);\n'
        '  long duration = pulseIn(echoPin, HIGH, 30000); // timeout 30ms\n'
        '  if (duration == 0) return -1;\n'
        '  return duration / 58; // distance en cm\n'
        '}'
    ),

    # 3. Setup: add proper pinMode
    (
        '  // Ultrasonic sensor: US1_PIN mode change dans readUltrasonic2Wire()',
        '  // Ultrasonic sensor: bassin 1 (4 fils)\n'
        '  pinMode(US1_TRIG, OUTPUT);\n'
        '  pinMode(US1_ECHO, INPUT);'
    ),

    # 4. Loop: update function call
    (
        '    long d1 = readUltrasonic2Wire(US1_PIN);',
        '    long d1 = readUltrasonic4Wire(US1_TRIG, US1_ECHO);'
    ),
]

count = 0
for old, new in replacements:
    if old in code:
        code = code.replace(old, new, 1)
        count += 1
        print(f"[OK] Replacement {count}")
    else:
        print(f"[FAIL] Not found: {old[:80]}...")

with open(path, "w", encoding="utf-8") as f:
    f.write(code)

print(f"\nDone: {count}/{len(replacements)} replacements applied")
