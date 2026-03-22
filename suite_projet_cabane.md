# Prompt de continuité — Projet Cabane Marcoux ESP32 (R5.4d)

Colle ce prompt au début d'une nouvelle session Claude Code pour reprendre exactement où on est rendu.

---

## PROMPT À COLLER :

```
Je travaille sur le projet Cabane Marcoux — un système de monitoring d'une cabane à sucre avec des ESP32. Le repo GitHub est robingag/cabane-marcoux, branche main. Commit actuel: R5.4d (5a154e7).

Le répertoire de travail est : C:\Users\ryb086\OneDrive - Groupe R.Y. Beaudoin\Bureau\CLAUDE_CODE\cyd_lumiere

### Architecture actuelle (R5.4d) — 3 ESP32 :

1. **WROOM Hub** (`wroom_hub/`) — LE CERVEAU
   - ESP32-WROOM-32 DevKit
   - GPIO 5 : dompeur limit switch (ISR CHANGE, debounce stable 500ms + min 20s entre cycles)
   - GPIO 13/14 : bassin 1 JSN-SR04T (TRIG/ECHO)
   - GPIO 4 : vacuum relay
   - BLE scan : reçoit CBM (bassin 2+3) + Inkbird IBS-TH2 (temp/hum)
   - Inkbird parsing corrigé : temp at bytes [0-1], hum at [2-3] (NimBLE strips company ID)
   - BLE advertise : "CBM-HUB" magic 0xCA
   - WiFi : Cabane_Marcoux / Cabane2025 (NVS, configurable via Serial)
   - MQTT : broker.hivemq.com:1883, publie TOUS les topics cyd/{id}/...
   - Serial commands : SSID:xxx, PASS:xxx, ID:xxx, STATUS, RESTART
   - DeviceId synchronisé avec CYD : **5ea48c** (sauvé dans NVS)
   - COM port : COM6

2. **CYD** (`cyd_lumiere/`) — AFFICHAGE SEULEMENT
   - ESP32-2432S028R avec écran TFT 320x240 + touch XPT2046
   - NE LIT PLUS de capteurs directement (ISR/ultrasonic supprimés)
   - Reçoit données via MQTT subscribe + BLE scan "CBM-HUB"
   - Affiche : dompeur, 4 bassins, temp/hum
   - Features : calibration 1 point offset (pouces), code QR, PIN vacuum, scan WiFi, dashboard web
   - DeviceId : **5ea48c**
   - WiFi : Cabane_Marcoux (sauvé NVS)
   - COM port : COM6 (même que Hub, un seul branché à la fois)

3. **capteur_bassins** (`capteur_bassins/`) — INCHANGÉ
   - ESP32-WROOM-32 sur COM6
   - 2x JSN-SR04T : bassin 2 (GPIO 25/26) + bassin 3 (GPIO 27/33)
   - BLE advertise : "CBM" magic 0xCB

### Dashboard Web (`index.html` à la racine) — BONNE VERSION
- Dark theme ambre/bleu, PWA mobile
- 4 bassins verticaux (Eau Érable, Concentré, Permeat, B4)
- Temp en gros + humidité en petit (2e ligne, aligné droite)
- Dompeur : compteur vert elapsed (ne redémarre plus sur retained MQTT)
- Tendance dompeur : s'efface après 30 min inactivité → "En attente de la prochaine coulée!"
- Calibration 1 point offset : bouton Lecture + saisie manuelle en pouces
- Champ Max (pouces) par bassin : % calculé = pouces_actuels / max × 100
- Alarme persistante localStorage
- MQTT retained : protégé contre faux redémarrages (dompeur, dmpTs, hist ignorés si retained)

### MQTT Topics (tous publiés par le Hub, ID=5ea48c) :
- cyd/5ea48c/dompeur — dernier cycle MM:SS (retained)
- cyd/5ea48c/dompeur/live — compteur temps réel chaque seconde (retained)
- cyd/5ea48c/basin1, basin2, basin3, basin4 — niveaux %
- cyd/5ea48c/basin1/raw, basin2/raw, basin3/raw, basin4/raw — distances brutes cm
- cyd/5ea48c/basin1/cal ... basin4/cal — calibration JSON {refRaw, refInches}
- cyd/5ea48c/temp, humidity — température et humidité
- cyd/5ea48c/state — état vacuum (0/1)
- cyd/5ea48c/cmd — commandes vacuum
- cyd/5ea48c/settings/unit — "pct" ou "in"
- cyd/5ea48c/settings/bnames — noms bassins JSON
- cyd/5ea48c/settings/bmax — profondeur max pouces JSON

### Changements R5.3→R5.4d (cette session) :
- R5.3c : Fix timer dompeur qui redémarrait sur retained MQTT
- R5.3d : Humidité en petit, 2e ligne alignée droite
- R5.3e : Nettoyage retained dmpTs du broker à la connexion
- R5.4 : 4e bassin + calibration 1 point offset (remplace low/high)
- R5.4b : Courbe tendance s'efface après 30 min, texte orange
- R5.4c : Texte "En attente de la prochaine coulée!"
- R5.4d : Champ Max pouces, % calculé depuis pouces

### Problèmes restants :
1. **CYD écran ne se met pas à jour** — Les données MQTT arrivent (confirmé via serial) mais l'écran TFT ne rafraîchit pas. drawMainScreen() ne rappelle pas les fonctions d'affichage.
2. **Limit switch vibre** — Debounce stable (500ms + 20s min) filtre la plupart mais à tester en conditions réelles.
3. **2 PCB JSN-SR04T morts** — Bassin 1 n'a pas de capteur fonctionnel.

### À FAIRE à la prochaine connexion locale (Hub sur COM6) :
1. **Flasher le Hub R5.5** — `cd wroom_hub && pio run --target upload` — nouvelle calibration 1-point offset
2. **Migrer capteur_bassins de BLE vers WiFi/MQTT** — Le capteur_bassins publie directement sur MQTT au lieu de passer par BLE+Hub. Même volume de données (le Hub publiait déjà). Avantages : temps réel (pas de délai scan 20s), plus fiable.
3. **Ajouter un 3e ESP32 pour bassin 4** — Nouveau ESP32-WROOM avec 1x JSN-SR04T, WiFi/MQTT direct, publie sur cyd/5ea48c/basin4 et basin4/raw. Même firmware que capteur_bassins migré en WiFi.
4. **Chaque ESP32 capteur publie ses propres topics** :
   - capteur_bassins (existant) → basin2, basin3, basin2/raw, basin3/raw
   - nouveau ESP32 → basin4, basin4/raw
   - Hub garde → basin1, basin1/raw (capteur local GPIO 13/14)
5. **Retirer le scan BLE du Hub** — Plus nécessaire pour les bassins une fois WiFi en place (garder pour Inkbird temp/hum seulement)
6. **Toute calibration via MQTT** — Les calibrations (refRaw/refInches, basinMax) doivent pouvoir être envoyées depuis le dashboard web via MQTT et reçues par chaque ESP32 capteur. Chaque ESP32 s'abonne à ses topics basin{n}/cal et settings/bmax, sauvegarde en NVS, et applique la conversion pouces/% localement.

### Prochaines tâches possibles :
- Fixer l'affichage CYD (écran TFT ne se rafraîchit pas)
- Ajouter basin4 au firmware Hub quand câblé
- Tester calibration pouces en conditions réelles

### Outils :
- PlatformIO : C:\Users\ryb086\AppData\Local\Programs\Python\Python312\Scripts\pio.exe
- Python 3.12
- OneDrive bloque Edit/Write sur main.cpp → utiliser scripts Python
- Pas de Node.js
- GitHub token : (voir MEMORY.md local — ne pas inclure dans le repo)
- bleak installé (BLE scanner Python)
```

---

## Notes :
- R5.4d sur GitHub (5a154e7)
- Hub flashé et fonctionnel (WiFi OK, MQTT OK, BLE OK)
- Dashboard web complètement à jour avec toutes les features
- CYD flashé display-only mais écran TFT ne se met pas à jour visuellement
- L'ancienne version du dashboard est dans cyd_lumiere/Cabane_Marcoux.html (obsolète)
