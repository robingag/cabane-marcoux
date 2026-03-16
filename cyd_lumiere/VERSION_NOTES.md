# Cabane Marcoux Dashboard - v2.1.0

## Changements majeurs

### Nouvelles fonctionnalités
1. **Système de calibration des bassins**
   - Menu de calibration accessible via icône engrenage (⚙)
   - PIN de protection: **123**
   - Calibration individuelle bas/haut pour chaque bassin
   - Sauvegarde en localStorage

2. **Système dual PIN**
   - **PIN Vacuum**: 777 (contrôle slider vacuum)
   - **PIN Calibration**: 123 (menu de calibration)
   - Interface PIN partagée, fonctionnalités différentes

3. **Slider Vacuum amélioré**
   - Glisser-déposer avec pointer events
   - Thème industriel dark avec accents ambrés
   - Icône éclair (⚡) 
   - Feedback visuel

### MQTT Topics (nouveaux)
```
cyd/{id}/basin{n}/raw    → Valeur brute capteur
cyd/{id}/basin{n}/cal    → Confirmation calibration
cyd/{id}/cmd/cal         → Commande calibration
```

### Thème visuel
- Apparence industrielle GitHub préservée
- Fond sombre (#080a0e)
- Accents ambrés (#f59e0b)
- Police monospace pour affichage numérique
- Contraste élevé pour lisibilité

### Architecture HTML
- Fichier unique: `index.html` (385 lignes)
- CSS inline pour portabilité
- JavaScript inline (MQTT.js via CDN)
- localStorage pour persistence
- Responsive design

## Fichiers
- **index.html** — Version GitHub (384 lignes)
- **cyd_lumiere/Cabane_Marcoux.html** — Version locale (identique)

## Déploiement ESP32
Le firmware doit supporter:
- Publication `cyd/{id}/basin{n}/raw` 
- Souscription `cyd/{id}/cmd/cal`
- Sauvegarde calibration en NVS

## Test
```
1. Ouvrir http://localhost:8081/Cabane_Marcoux.html
2. Cliquer engrenage → PIN 123 → Panel calibration
3. Slider vacuum → PIN 777 pour toggle
```

## Commits
- 7b2a757: Add basin calibration system with dual PIN

---
**Date**: 2026-03-10  
**Status**: Ready for GitHub PR
