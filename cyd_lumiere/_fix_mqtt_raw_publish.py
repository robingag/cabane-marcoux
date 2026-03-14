"""
Publier les valeurs brutes du capteur bassin via MQTT a chaque lecture.
Le dashboard MQTT en a besoin pour afficher "Brut: XX" dans la calibration.
"""

path = r"C:\Users\ryb086\OneDrive - Groupe R.Y. Beaudoin\Bureau\CLAUDE_CODE\cyd_lumiere\src\main.cpp"

with open(path, "r", encoding="utf-8") as f:
    code = f.read()

replacements = [
    # Ajouter publication raw + cal apres publication basin1 %
    (
        '''      if (mqtt.connected()) {
        mqtt.publish(mqttTopicBasin1.c_str(), String(basin1).c_str(), true);
      }
      Serial.printf("Bassin 1: %dcm = %d%%\\n", (int)d1, basin1);''',
        '''      if (mqtt.connected()) {
        mqtt.publish(mqttTopicBasin1.c_str(), String(basin1).c_str(), true);
        // Publier valeur brute pour dashboard calibration
        String rawTopic = "cyd/" + deviceId + "/basin1/raw";
        mqtt.publish(rawTopic.c_str(), String(rawBasin[0]).c_str(), true);
      }
      Serial.printf("Bassin 1: %dcm = %d%%\\n", (int)d1, basin1);'''
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
