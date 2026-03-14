"""
Ajouter compteur temps reel dans la case Dompeur
- Affiche le temps ecoule depuis le dernier front en vert sous le dernier cycle
- Rafraichit chaque seconde sur l'ecran TFT
"""

path = r"C:\Users\ryb086\OneDrive - Groupe R.Y. Beaudoin\Bureau\CLAUDE_CODE\cyd_lumiere\src\main.cpp"

with open(path, "r", encoding="utf-8") as f:
    code = f.read()

replacements = [
    # 1. Agrandir la carte dompeur (56 -> 72) et ajouter compteur temps reel
    (
        '''void drawDompeurCard() {
  int cx = 4, cy = 28, cw = SW - 8, ch = 56;
  tft.fillRoundRect(cx, cy, cw, ch, 6, C_CARD);
  tft.drawRoundRect(cx, cy, cw, ch, 6, C_BORDER);
  tft.setTextFont(1); tft.setTextSize(1);
  tft.setTextDatum(TL_DATUM);
  tft.setTextColor(C_TXT_GRAY, C_CARD);
  tft.drawString("DOMPEUR", cx + 10, cy + 6);
  tft.setTextSize(4);
  tft.setTextDatum(MC_DATUM);
  tft.setTextColor(C_CYAN, C_CARD);
  tft.drawString(dompeurTime.c_str(), cx + cw / 2, cy + 36);
}''',
        '''void drawDompeurCard() {
  int cx = 4, cy = 28, cw = SW - 8, ch = 72;
  tft.fillRoundRect(cx, cy, cw, ch, 6, C_CARD);
  tft.drawRoundRect(cx, cy, cw, ch, 6, C_BORDER);
  tft.setTextFont(1); tft.setTextSize(1);
  tft.setTextDatum(TL_DATUM);
  tft.setTextColor(C_TXT_GRAY, C_CARD);
  tft.drawString("DOMPEUR", cx + 10, cy + 6);
  tft.setTextSize(3);
  tft.setTextDatum(MC_DATUM);
  tft.setTextColor(C_CYAN, C_CARD);
  tft.drawString(dompeurTime.c_str(), cx + cw / 2, cy + 32);
  // Compteur temps reel depuis dernier front
  unsigned long elapsed = (lsLastEdge > 0) ? (millis() - lsLastEdge) / 1000 : 0;
  int eMin = elapsed / 60;
  int eSec = elapsed % 60;
  char eBuf[8];
  snprintf(eBuf, sizeof(eBuf), "%02d:%02d", eMin, eSec);
  tft.setTextSize(2);
  tft.setTextColor(C_GREEN, C_CARD);
  tft.drawString(eBuf, cx + cw / 2, cy + 58);
}'''
    ),

    # 2. Ajouter rafraichissement chaque seconde dans loop (avant LED bleue)
    (
        '  // LED bleue = etat du limit switch',
        '  // Rafraichir compteur dompeur chaque seconde\n'
        '  static unsigned long lastDompeurRefresh = 0;\n'
        '  if (currentScreen == SCREEN_MAIN && !menuOpen && millis() - lastDompeurRefresh > 1000) {\n'
        '    lastDompeurRefresh = millis();\n'
        '    drawDompeurCard();\n'
        '  }\n'
        '\n'
        '  // LED bleue = etat du limit switch'
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
