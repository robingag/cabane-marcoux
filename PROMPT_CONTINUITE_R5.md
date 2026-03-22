# Prompt de continuité — Projet Cabane Marcoux ESP32 (R5.2)

Colle ce prompt au début d'une nouvelle session Claude Code pour reprendre exactement où on est rendu.

---

## PROMPT À COLLER :

```
Je travaille sur le projet Cabane Marcoux — un système de monitoring d'une cabane à sucre avec des ESP32. Le repo GitHub est robingag/cabane-marcoux, branche main. Commit actuel: R5.2 (118fc76).

Le répertoire de travail est : C:\Users\ryb086\OneDrive - Groupe R.Y. Beaudoin\Bureau\CLAUDE_CODE\

### Architecture actuelle (R5.2) — 3 ESP32 :

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
   - Affiche : dompeur, 3 bassins, temp/hum
   - Features gardées : calibration 2 points, code QR, PIN vacuum, scan WiFi, dashboard web, graphique tendance
   - DeviceId : **5ea48c**
   - WiFi : Cabane_Marcoux (sauvé NVS)
   - COM port : COM6 (même que Hub, un seul branché à la fois)

3. **capteur_bassins** (`capteur_bassins/`) — INCHANGÉ
   - ESP32-WROOM-32 sur COM6
   - 2x JSN-SR04T : bassin 2 (GPIO 25/26) + bassin 3 (GPIO 27/33)
   - BLE advertise : "CBM" magic 0xCB

### MQTT Topics (tous publiés par le Hub, ID=5ea48c) :
- cyd/5ea48c/dompeur — dernier cycle MM:SS (retained)
- cyd/5ea48c/dompeur/live — compteur temps réel chaque seconde (retained)
- cyd/5ea48c/basin1, basin2, basin3 — niveaux %
- cyd/5ea48c/basin1/raw, basin2/raw, basin3/raw — distances brutes cm
- cyd/5ea48c/temp, humidity — température et humidité
- cyd/5ea48c/state — état vacuum (0/1)
- cyd/5ea48c/cmd — commandes vacuum
- cyd/5ea48c/cmd/cal — calibration JSON

### Problèmes à résoudre (prochaine session) :
1. **CYD écran ne se met pas à jour** — Les données MQTT arrivent (confirmé via serial) mais l'écran n'affiche pas les nouvelles valeurs. drawMainScreen() n'appelle pas drawTempCard() ni drawTrendGraph(). Les callbacks MQTT mettent à jour les variables mais possiblement currentScreen != SCREEN_MAIN au moment des premiers messages.
2. **Dashboard web : compteur vert reset au refresh** — Le dompeur/live retained fonctionne mais le compteur vert (id="dlv") revient à "--:--" au refresh quand le dompeur est inactif.
3. **Limit switch vibre** — Les vibrations mécaniques génèrent des faux fronts. Le debounce stable (500ms + 20s min) filtre la plupart mais à tester en conditions réelles.
4. **2 PCB JSN-SR04T morts** — Bassin 1 n'a pas de capteur fonctionnel.
5. **Fil ECHO GPIO 35 du CYD cassé** — Raison de la migration vers WROOM Hub.

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
- R5.2 sur GitHub (118fc76)
- Hub flashé et fonctionnel (WiFi OK, MQTT OK, BLE OK, temp 2.7°C correcte)
- CYD flashé display-only mais écran ne se met pas à jour visuellement
- Le CYD reçoit bien les données MQTT (confirmé par serial monitor)
- Priorité prochaine session : fixer l'affichage du CYD
