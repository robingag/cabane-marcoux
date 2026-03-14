path = r"C:\Users\ryb086\OneDrive - Groupe R.Y. Beaudoin\Bureau\CLAUDE_CODE\cyd_lumiere\src\main.cpp"
with open(path, 'r', encoding='utf-8') as f:
    code = f.read()

# Replace drawBasinBar with drawBasinTank (vertical)
old_bar = '''void drawBasinBar(int y, const char* name, int level) {
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
    if (level >= 91) bc = C_RED;
    else if (level >= 61) bc = C_YELLOW;
    tft.fillRect(barX + 1, y + 3, fillW, barH - 2, bc);
  }
  // Percentage (white, textSize 2)
  tft.setTextDatum(MR_DATUM);
  tft.setTextColor(C_TXT, C_CARD);
  String pct = String(level) + "%";
  tft.drawString(pct.c_str(), SW - 8, y + 17);
}'''

new_tank = '''void drawBasinTank(int cx, int tankW, int tankH, int topY, const char* name, int level) {
  // Name label above tank
  tft.setTextFont(1); tft.setTextSize(1);
  tft.setTextDatum(TC_DATUM);
  tft.setTextColor(C_LABEL, C_CARD);
  tft.drawString(name, cx + tankW / 2, topY);
  // Tank border
  int ty = topY + 12;
  tft.fillRect(cx, ty, tankW, tankH, C_SB_BG);
  tft.drawRect(cx, ty, tankW, tankH, C_BORDER);
  // Graduation lines (25%, 50%, 75%)
  for (int g = 1; g <= 3; g++) {
    int gy = ty + tankH - (tankH * g * 25 / 100);
    tft.drawFastHLine(cx + 1, gy, 4, C_BORDER);
    tft.drawFastHLine(cx + tankW - 5, gy, 4, C_BORDER);
  }
  // Fill from bottom
  int fillH = (tankH - 2) * level / 100;
  if (fillH > 0) {
    uint16_t bc = C_GREEN;
    if (level >= 91) bc = C_RED;
    else if (level >= 61) bc = C_YELLOW;
    tft.fillRect(cx + 1, ty + tankH - 1 - fillH, tankW - 2, fillH, bc);
  }
  // Percentage below tank
  tft.setTextDatum(TC_DATUM);
  tft.setTextColor(C_TXT, C_CARD);
  tft.setTextSize(1);
  String pct = String(level) + "%";
  tft.drawString(pct.c_str(), cx + tankW / 2, ty + tankH + 3);
}'''

code = code.replace(old_bar, new_tank)

# Replace drawBasinCards to use vertical tanks side by side
old_cards = '''void drawBasinCards() {
  int cy = 88, ch = 148;
  tft.fillRoundRect(4, cy, SW - 8, ch, 6, C_CARD);
  tft.drawRoundRect(4, cy, SW - 8, ch, 6, C_BORDER);
  drawBasinBar(cy + 20, "Bassin 1", basin1);
  drawBasinBar(cy + 68, "Bassin 2", basin2);
  drawBasinBar(cy + 116, "Bassin 3", basin3);
}'''

new_cards = '''void drawBasinCards() {
  int cy = 88, ch = 148;
  tft.fillRoundRect(4, cy, SW - 8, ch, 6, C_CARD);
  tft.drawRoundRect(4, cy, SW - 8, ch, 6, C_BORDER);
  // 3 vertical tanks side by side
  int tankW = 70, tankH = 105;
  int gap = (SW - 8 - 3 * tankW) / 4;
  int topY = cy + 8;
  drawBasinTank(4 + gap, tankW, tankH, topY, "B1", basin1);
  drawBasinTank(4 + gap * 2 + tankW, tankW, tankH, topY, "B2", basin2);
  drawBasinTank(4 + gap * 3 + tankW * 2, tankW, tankH, topY, "B3", basin3);
}'''

code = code.replace(old_cards, new_cards)

with open(path, 'w', encoding='utf-8') as f:
    f.write(code)

print("Basins changed to vertical tanks on TFT")
