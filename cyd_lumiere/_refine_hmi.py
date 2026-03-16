f = r'C:\Users\ryb086\OneDrive - Groupe R.Y. Beaudoin\Bureau\CLAUDE_CODE\cyd_lumiere\src\main.cpp'
with open(f, 'r', encoding='utf-8') as fh:
    c = fh.read()

# 1. Compact drawBasinBar: barH 14->12, adjust y offsets
old_bar = """void drawBasinBar(int y, const char* name, int level) {
  int nameX = 10, barX = 62, barW = 210, barH = 14;
  // Name
  tft.setTextFont(1); tft.setTextSize(1);
  tft.setTextDatum(ML_DATUM);
  tft.setTextColor(C_LABEL, C_CARD);
  tft.drawString(name, nameX, y + 9);
  // Bar wrapper
  tft.fillRect(barX, y + 2, barW, barH, C_BG);
  tft.drawRect(barX, y + 2, barW, barH, C_BORDER);
  // Fill
  int fillW = (barW - 2) * level / 100;
  if (fillW > 0) {
    uint16_t bc = C_GREEN;
    if (level >= 50) bc = C_RED;
    else if (level >= 25) bc = C_AMBER;
    tft.fillRect(barX + 1, y + 3, fillW, barH - 2, bc);
  }
  // Percentage
  tft.setTextDatum(MR_DATUM);
  tft.setTextColor(C_TXT_DIM, C_CARD);
  String pct = String(level) + "%";
  tft.drawString(pct.c_str(), SW - 10, y + 9);
}"""

new_bar = """void drawBasinBar(int y, const char* name, int level) {
  int nameX = 10, barX = 62, barW = 210, barH = 12;
  // Name
  tft.setTextFont(1); tft.setTextSize(1);
  tft.setTextDatum(ML_DATUM);
  tft.setTextColor(C_LABEL, C_CARD);
  tft.drawString(name, nameX, y + 7);
  // Bar wrapper
  tft.fillRect(barX, y + 1, barW, barH, C_BG);
  tft.drawRect(barX, y + 1, barW, barH, C_BORDER);
  // Fill
  int fillW = (barW - 2) * level / 100;
  if (fillW > 0) {
    uint16_t bc = C_GREEN;
    if (level >= 50) bc = C_RED;
    else if (level >= 25) bc = C_AMBER;
    tft.fillRect(barX + 1, y + 2, fillW, barH - 2, bc);
  }
  // Percentage
  tft.setTextDatum(MR_DATUM);
  tft.setTextColor(C_TXT_DIM, C_CARD);
  String pct = String(level) + "%";
  tft.drawString(pct.c_str(), SW - 10, y + 7);
}"""

c = c.replace(old_bar, new_bar)
print("1. BasinBar compact:", "OK" if new_bar in c else "NOT FOUND")

# 2. Add header to drawBasinCards + compact spacing
old_cards = """void drawBasinCards() {
  int cy = 132, ch = 64;
  tft.fillRoundRect(4, cy, SW - 8, ch, 4, C_CARD);
  tft.drawRoundRect(4, cy, SW - 8, ch, 4, C_BORDER);
  drawBasinBar(cy + 2, "BASSIN 1", basin1);
  drawBasinBar(cy + 22, "BASSIN 2", basin2);
  drawBasinBar(cy + 42, "BASSIN 3", basin3);
}"""

new_cards = """void drawBasinCards() {
  int cy = 132, ch = 64;
  tft.fillRoundRect(4, cy, SW - 8, ch, 4, C_CARD);
  tft.drawRoundRect(4, cy, SW - 8, ch, 4, C_BORDER);
  // Header like HTML "Etat de remplissage"
  tft.setTextFont(1); tft.setTextSize(1);
  tft.setTextDatum(TL_DATUM);
  tft.setTextColor(C_TXT_GRAY, C_CARD);
  tft.drawString("ETAT DE REMPLISSAGE", 10, cy + 3);
  // Compact basin bars
  drawBasinBar(cy + 13, "BASSIN 1", basin1);
  drawBasinBar(cy + 29, "BASSIN 2", basin2);
  drawBasinBar(cy + 45, "BASSIN 3", basin3);
}"""

c = c.replace(old_cards, new_cards)
print("2. BasinCards header:", "OK" if new_cards in c else "NOT FOUND")

# 3. Trend graph label: "Tendance" -> "Historique"
old_trend_lbl = 'tft.drawString("Tendance", gx + 8, gy + 3);'
new_trend_lbl = 'tft.drawString("Historique - 30 pts", gx + 8, gy + 3);'
c = c.replace(old_trend_lbl, new_trend_lbl)
print("3. Trend label:", "OK" if new_trend_lbl in c else "NOT FOUND")

with open(f, 'w', encoding='utf-8') as fh:
    fh.write(c)

import os
print(f"\nDone! Size: {os.path.getsize(f)} bytes")
