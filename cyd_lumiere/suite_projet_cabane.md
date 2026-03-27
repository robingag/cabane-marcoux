# Prompt de continuité — Projet Cabane Marcoux ESP32 (R5.7)

Colle ce prompt au début d'une nouvelle session Claude Code pour reprendre exactement où on est rendu.

---

## PROMPT À COLLER :

```
Je travaille sur le projet Cabane Marcoux — un système de monitoring d'une cabane à sucre avec des ESP32. Le repo GitHub est robingag/cabane-marcoux, branche main.

Le répertoire de travail est : C:\Users\ryb086\OneDrive - Groupe R.Y. Beaudoin\Bureau\CLAUDE_CODE\cyd_lumiere
Le firmware Hub compilé est dans : C:\tmp\wh\ (chemin court pour NimBLE)

### Architecture actuelle (R5.7) — 3 ESP32 :

1. **USB Hub** (`wroom_hub/`) — LE CERVEAU (ancien USB 3, maintenant Hub principal)
   - ESP32-WROOM-32 DevKit CH340
   - GPIO 18 : bassin 1 JSN-SR04T TRIG
   - GPIO 19 : bassin 1 JSN-SR04T ECHO
   - GPIO 27/33 : US2 (pas branché, disponible)
   - GPIO 5 : dompeur limit switch (ISR CHANGE, filtre stable-state 80ms + min 20s entre cycles)
   - GPIO 4 : vacuum relay
   - GPIO 2 : LED bleue indicateur (lent=WiFi+MQTT OK, moyen=WiFi OK, rapide=pas de WiFi)
   - BLE scan toutes les 20s pendant 10s : reçoit "CBM" (B2+B3 de USB 2) + Inkbird IBS-TH2 (temp/hum)
   - BLE advertise : "CBM-HUB" magic 0xCA
   - WiFi : Cabane_Marcoux / Cabane2025
   - MQTT : broker.hivemq.com:1883, publie TOUS les topics cyd/{id}/...
   - Web server : dashboard sur http://192.168.1.163/ + API JSON sur /api
   - OTA : hostname cabane-hub, port 3232, password cabane2025
   - Calibration 1-point offset : refRaw/refInches + basinMax, sauvé NVS
   - publishAll() toutes les 2s (retained) + topic live (non-retained)
   - Serial commands : SSID:xxx, PASS:xxx, ID:xxx, STATUS, RESTART
   - DeviceId : **5ea48c**
   - COM port : **COM6**
   - MAC : b0:cb:d8:c1:95:08

2. **USB 2** (`capteur_bassins/`) — BASSINS 2+3 VIA BLE
   - ESP32 CP2102
   - GPIO 18/19 : bassin 2 JSN-SR04T (TRIG/ECHO)
   - GPIO 22/23 : bassin 3 JSN-SR04T (TRIG/ECHO)
   - BLE advertise : "CBM" magic 0xCB
   - Format manufacturer data : [0xFF, 0xFF, 0xCB, b2_lo, b2_hi, b3_lo, b3_hi]
   - COM port : **COM8**
   - NOTE COMPILATION : chemin OneDrive trop long pour NimBLE → compiler depuis C:\tmp\cb\

3. **CYD** (`cyd_lumiere/`) — AFFICHAGE TFT (pas utilisé en ce moment)
   - ESP32-2432S028R avec écran TFT 320x240 + touch XPT2046
   - QR code pointe vers GitHub Pages → redirect MQTT vers http://Hub_IP/

### Dashboard Web (intégré au Hub) :
- Servi directement par le Hub sur http://192.168.1.163/
- Polling HTTP /api toutes les 500ms — temps réel garanti
- Affiche : 3 bassins (%), temp, humidité, dompeur
- Dark theme ambre/bleu, PWA mobile
- Le QR code GitHub Pages (https://robingag.github.io/cabane-marcoux/index.html) se connecte à MQTT, lit le topic hubip, et redirige vers http://{hubip}/

### Dashboard GitHub Pages (gallant-morse/index.html) :
- Version complète avec calibration, alarmes, noms de bassins
- MQTT WebSocket vers broker.hivemq.com
- Auto-redirect vers Hub local si sur réseau local
- Auto-redirect via MQTT hubip si sur HTTPS (GitHub Pages)

### MQTT Topics (tous publiés par le Hub, ID=5ea48c) :
- cyd/5ea48c/dompeur — dernier cycle MM:SS (retained)
- cyd/5ea48c/dompeur/live — compteur temps réel chaque seconde
- cyd/5ea48c/basin1, basin2, basin3 — niveaux %
- cyd/5ea48c/basin1/raw, basin2/raw, basin3/raw — distances brutes cm
- cyd/5ea48c/basin1/cal, basin2/cal, basin3/cal — calibration JSON {refRaw, refInches}
- cyd/5ea48c/temp, humidity — température et humidité
- cyd/5ea48c/state — état vacuum (0/1)
- cyd/5ea48c/cmd — commandes vacuum
- cyd/5ea48c/settings/bmax — profondeur max pouces JSON
- cyd/5ea48c/hubip — IP du Hub (retained, pour redirect QR)
- cyd/5ea48c/live — données live non-retained (b1%|b2%|b3%|r1|r2|r3|temp|hum)

### Calibration 1-point offset :
- Format MQTT : {"refRaw":70,"refInches":16}
- Formule : pouces = refInches + (refRaw - currentRaw) / 2.54
- % = pouces / basinMax * 100
- Sauvé dans NVS (persistant au reboot)
- basinMax via topic settings/bmax : {"1":42,"2":25,"3":42}

### OTA (Over-The-Air) :
- Flasher via WiFi : pio run -e ota --target upload
- Hostname : cabane-hub, Port : 3232, Password : cabane2025
- IP actuelle : 192.168.1.163
- Nécessite d'être sur le réseau Cabane_Marcoux (ou via VPN Tailscale)

### Session du 27 mars 2026 — Ce qui a été fait :
1. USB 3 (CH340 COM6) devient le nouveau Hub (remplace ancien Hub COM5)
2. Firmware Hub flashé avec GPIO 18/19 pour JSN-SR04T bassin 1
3. Filtre stable-state 80ms remplace debounce 500ms pour limit switch
4. LED bleue indicateur d'état ajoutée (GPIO 2)
5. Calibration 1-point offset via MQTT + sauvegarde NVS
6. WiFi Cabane_Marcoux configuré, MQTT connecté, Device ID 5ea48c
7. Web server intégré au Hub : dashboard sur / + API JSON sur /api
8. publishAll() toutes les 2s avec retained + topic live non-retained
9. Dashboard GitHub Pages : auto-redirect vers Hub via MQTT hubip
10. OTA ajouté (ArduinoOTA, hostname cabane-hub, port 3232)
11. Tout poussé sur GitHub (main)

### Valeurs actuelles (27 mars 2026) :
- B1 : 70cm raw, calibré 16po @ 70cm, max 42po → ~38%
- B2 : 56cm raw (via BLE depuis USB 2)
- B3 : 112cm raw (via BLE depuis USB 2)
- Temp : -4°C, Hum : 40%
- Inkbird battery : 100%

### Problèmes connus :
1. Dashboard GitHub Pages : HTTPS ne peut pas fetch HTTP (mixed content) → redirect fonctionne via MQTT hubip
2. USB 2 (CP2102) reboot parfois — watchdog timer avec BLE
3. US2 (GPIO 27/33) pas branché sur le Hub — disponible pour un 2e capteur local
4. CYD écran TFT ne se met pas à jour visuellement (pas utilisé en ce moment)

### Prochaines étapes :
1. Configurer VPN Tailscale pour flash OTA à distance
2. Réserver IP fixe sur routeur Cabane_Marcoux pour le Hub
3. Tester le dashboard QR code sur téléphone
4. Calibrer les 3 bassins en conditions réelles
5. Configurer USB 3 pour bassin 4 si nécessaire
6. Fixer le reboot du CP2102 (USB 2)

### Compilation :
- PlatformIO : C:\Users\ryb086\AppData\Local\Programs\Python\Python312\Scripts\platformio
- Hub : compiler depuis C:\tmp\wh\ (chemin court)
- USB 2 : compiler depuis C:\tmp\cb\ (chemin court)
- Flash USB : pio run -e esp32dev --target upload
- Flash OTA : pio run -e ota --target upload
- Python 3.12, paho-mqtt installé
```

---

## Notes :
- R5.7 sur GitHub main (408982d)
- Hub flashé : WiFi OK (192.168.1.163), MQTT OK, BLE OK, OTA OK, Web server OK
- USB 2 flashé : BLE "CBM" OK, B2=56cm B3=112cm
- Dashboard intégré au Hub : polling /api 500ms, temps réel confirmé
- Sonde bassin 1 testée : détecte main (20-26cm) vs fond (70cm)
