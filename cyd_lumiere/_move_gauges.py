f = r'C:\Users\ryb086\OneDrive - Groupe R.Y. Beaudoin\Bureau\CLAUDE_CODE\cyd_lumiere\src\main.cpp'
with open(f, 'r', encoding='utf-8') as fh:
    c = fh.read()

# 1. Gear icon: 16x16 -> 24x24
old_gear = """void drawGearIcon(int x, int y) {
  // 16x16 gear icon
  tft.fillCircle(x + 8, y + 8, 6, C_TXT_GRAY);
  tft.fillCircle(x + 8, y + 8, 3, C_CARD);
  // Teeth (4 cardinal + 4 diagonal)
  for (int a = 0; a < 4; a++) {
    int dx[] = {0, 8, 0, -8};
    int dy[] = {-8, 0, 8, 0};
    tft.fillRect(x + 8 + dx[a] - 1, y + 8 + dy[a] - 1, 3, 3, C_TXT_GRAY);
  }
}"""

new_gear = """void drawGearIcon(int x, int y) {
  // 24x24 gear icon
  tft.fillCircle(x + 12, y + 12, 9, C_TXT_GRAY);
  tft.fillCircle(x + 12, y + 12, 4, C_CARD);
  // Teeth (4 cardinal)
  for (int a = 0; a < 4; a++) {
    int dx[] = {0, 11, 0, -11};
    int dy[] = {-11, 0, 11, 0};
    tft.fillRect(x + 12 + dx[a] - 2, y + 12 + dy[a] - 2, 5, 5, C_TXT_GRAY);
  }
}"""

c = c.replace(old_gear, new_gear)
print("1. GearIcon 24px:", "OK" if "24x24" in c else "NOT FOUND")

# 2. drawBasinCards: gear plus grand + bars descendues (espacement 44px, debut a cy+28)
old_cards = """void drawBasinCards() {
  int cy = 88, ch = 148;
  tft.fillRoundRect(4, cy, SW - 8, ch, 6, C_CARD);
  tft.drawRoundRect(4, cy, SW - 8, ch, 6, C_BORDER);
  // Gear icon (top-right of card)
  drawGearIcon(SW - 28, cy + 4);
  // Basin bars (evenly spaced)
  drawBasinBar(cy + 12, "Bassin 1", basin1);
  drawBasinBar(cy + 48, "Bassin 2", basin2);
  drawBasinBar(cy + 84, "Bassin 3", basin3);
}"""

new_cards = """void drawBasinCards() {
  int cy = 88, ch = 148;
  tft.fillRoundRect(4, cy, SW - 8, ch, 6, C_CARD);
  tft.drawRoundRect(4, cy, SW - 8, ch, 6, C_BORDER);
  // Gear icon (top-right of card, 24x24)
  drawGearIcon(SW - 32, cy + 4);
  // Basin bars descendues (espacement 44px)
  drawBasinBar(cy + 28, "Bassin 1", basin1);
  drawBasinBar(cy + 72, "Bassin 2", basin2);
  drawBasinBar(cy + 116, "Bassin 3", basin3);
}"""

c = c.replace(old_cards, new_cards)
print("2. BasinCards bars:", "OK" if "cy + 116" in c else "NOT FOUND")

# 3. Touch zone gear: agrandir pour 24x24
old_touch = "  if (tx >= SW - 32 && tx <= SW - 4 && ty >= 86 && ty <= 110) {"
new_touch = "  if (tx >= SW - 36 && tx <= SW - 4 && ty >= 86 && ty <= 120) {"
c = c.replace(old_touch, new_touch)
print("3. GearTouch zone:", "OK" if new_touch in c else "NOT FOUND")

with open(f, 'w', encoding='utf-8') as fh:
    fh.write(c)

import os
print(f"\nDone! Size: {os.path.getsize(f)} bytes")
