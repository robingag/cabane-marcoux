"""
Deplacer les fonctions ultrasoniques apres les declarations de calLow/calHigh/rawBasin.
Le probleme: les fonctions sont inserees trop tot dans le fichier.
Solution: retirer les fonctions de leur position actuelle et les inserer apres addDompeurPoint().
"""

path = r"C:\Users\ryb086\OneDrive - Groupe R.Y. Beaudoin\Bureau\CLAUDE_CODE\cyd_lumiere\src\main.cpp"

with open(path, 'r', encoding='utf-8') as f:
    code = f.read()

# Bloc des fonctions a deplacer (entre les pin defines et les variables volatile du limit switch)
old_funcs = (
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
)

# Retirer de la position actuelle
if old_funcs in code:
    code = code.replace(old_funcs, '', 1)
    print("OK 1: fonctions retirees de la position actuelle")
else:
    print("ERREUR 1: bloc de fonctions non trouve")
    exit(1)

# Inserer apres addDompeurPoint (qui est apres calLow/calHigh)
insert_after = (
    'void addDompeurPoint(int seconds) {\n'
    '  if (graphCount < GRAPH_MAX) {\n'
    '    dompeurHist[graphCount++] = seconds;\n'
    '  } else {\n'
    '    memmove(dompeurHist, dompeurHist + 1, (GRAPH_MAX - 1) * sizeof(int));\n'
    '    dompeurHist[GRAPH_MAX - 1] = seconds;\n'
    '  }\n'
    '}\n'
)

if insert_after in code:
    code = code.replace(insert_after, insert_after + '\n' + old_funcs, 1)
    print("OK 2: fonctions inserees apres addDompeurPoint")
else:
    print("ERREUR 2: addDompeurPoint non trouve")
    exit(1)

with open(path, 'w', encoding='utf-8') as f:
    f.write(code)

print("\nTermine: fonctions deplacees avec succes")
