f = r'C:\Users\ryb086\OneDrive - Groupe R.Y. Beaudoin\Bureau\CLAUDE_CODE\cyd_lumiere\src\main.cpp'
with open(f, 'r', encoding='utf-8') as fh:
    c = fh.read()

# 1. drawBasinBar: barres plus grosses + police textSize(2)
#    barH 22->30, barX 68->110 (label plus large), barW 200->155
#    textSize 1->2 pour label et pourcentage
old_bar = """void drawBasinBar(int y, const char* name, int level) {
  int nameX = 10, barX = 68, barW = 200, barH = 22;
  // Name (blue like interface1)
  tft.setTextFont(1); tft.setTextSize(1);
  tft.setTextDatum(ML_DATUM);
  tft.setTextColor(C_LABEL, C_CARD);
  tft.drawString(name, nameX, y + 13);
  // Bar wrapper (dark bg like interface1)
  tft.fillRect(barX, y + 2, barW, barH, C_SB_BG);
  tft.drawRect(barX, y + 2, barW, barH, C_BORDER);
  // Fill
  int fillW = (barW - 2) * level / 100;
  if (fillW > 0) {
    uint16_t bc = C_GREEN;
    if (level >= 50) bc = C_RED;
    else if (level >= 25) bc = C_YELLOW;
    tft.fillRect(barX + 1, y + 3, fillW, barH - 2, bc);
  }
  // Percentage (white bold)
  tft.setTextDatum(MR_DATUM);
  tft.setTextColor(C_TXT, C_CARD);
  String pct = String(level) + "%";
  tft.drawString(pct.c_str(), SW - 10, y + 13);
}"""

new_bar = """void drawBasinBar(int y, const char* name, int level) {
  int nameX = 10, barX = 110, barW = 155, barH = 30;
  // Name (blue, textSize 2)
  tft.setTextFont(1); tft.setTextSize(2);
  tft.setTextDatum(ML_DATUM);
  tft.setTextColor(C_LABEL, C_CARD);
  tft.drawString(name, nameX, y + 17);
  // Bar wrapper
  tft.fillRect(barX, y + 2, barW, barH, C_SB_BG);
  tft.drawRect(barX, y + 2, barW, barH, C_BORDER);
  // Fill
  int fillW = (barW - 2) * level / 100;
  if (fillW > 0) {
    uint16_t bc = C_GREEN;
    if (level >= 50) bc = C_RED;
    else if (level >= 25) bc = C_YELLOW;
    tft.fillRect(barX + 1, y + 3, fillW, barH - 2, bc);
  }
  // Percentage (white, textSize 2)
  tft.setTextDatum(MR_DATUM);
  tft.setTextColor(C_TXT, C_CARD);
  String pct = String(level) + "%";
  tft.drawString(pct.c_str(), SW - 8, y + 17);
}"""

c = c.replace(old_bar, new_bar)
print("1. BasinBar bigger:", "OK" if "barH = 30" in c else "NOT FOUND")

# 2. drawBasinCards: ajuster l'espacement pour barres de 32px
#    espacement 48px: cy+20, cy+68, cy+116 -> bar 3 se termine a cy+116+30+2=cy+148 pile
old_cards_bars = """  // Basin bars descendues (espacement 44px)
  drawBasinBar(cy + 28, "Bassin 1", basin1);
  drawBasinBar(cy + 72, "Bassin 2", basin2);
  drawBasinBar(cy + 116, "Bassin 3", basin3);"""

new_cards_bars = """  // Basin bars (espacement 48px, remplit toute la carte)
  drawBasinBar(cy + 20, "Bassin 1", basin1);
  drawBasinBar(cy + 68, "Bassin 2", basin2);
  drawBasinBar(cy + 116, "Bassin 3", basin3);"""

c = c.replace(old_cards_bars, new_cards_bars)
print("2. BasinCards spacing:", "OK" if "cy + 20" in c else "NOT FOUND")

with open(f, 'w', encoding='utf-8') as fh:
    fh.write(c)

import os
print(f"\nDone! Size: {os.path.getsize(f)} bytes")
