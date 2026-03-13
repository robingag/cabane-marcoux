f = r'C:\Users\ryb086\OneDrive - Groupe R.Y. Beaudoin\Bureau\CLAUDE_CODE\cyd_lumiere\src\main.cpp'
with open(f, 'r', encoding='utf-8') as fh:
    c = fh.read()

# 1. Color palette: amber industrial -> interface1 blue/cyan
old_colors = """// Color palette (industrial dark theme - matches HTML dashboard)
const uint16_t C_BG       = 0x0841;  // #080a0e deep black
const uint16_t C_CARD     = 0x0883;  // #0c1018 dark card
const uint16_t C_BORDER   = 0x1986;  // #1a2332 border
const uint16_t C_HEADER   = 0x08A4;  // #0d1520 dark header
const uint16_t C_AMBER    = 0xF4E1;  // #f59e0b amber accent
const uint16_t C_CYAN     = 0x35FF;  // #38bdf8 temperature
const uint16_t C_GREEN    = 0x2629;  // #22c55e green
const uint16_t C_RED      = 0xEA28;  // #ef4444 red
const uint16_t C_YELLOW   = 0xF4E1;  // same as amber
const uint16_t C_BLUE     = 0x3C1E;  // #3b82f6 graph accent
const uint16_t C_TXT      = 0xF7BE;  // #f1f5f9 white text
const uint16_t C_TXT_GRAY = 0x63B1;  // #64748b labels
const uint16_t C_TXT_DIM  = 0x4B10;  // #4a6080 status
const uint16_t C_LABEL    = 0x9517;  // #94a3b8 basin names
const uint16_t C_SB_BG    = 0x0042;  // #060810 status bar bg
const uint16_t C_HDL_BG   = 0x1927;  // #1c2538 handle bg
const uint16_t C_HDL_BD   = 0x2A0A;  // #2a3a52 handle border"""

new_colors = """// Color palette (interface1 blue/cyan theme)
const uint16_t C_BG       = 0x0843;  // #0a0a1a deep dark
const uint16_t C_CARD     = 0x18C5;  // #1a1a2e dark card
const uint16_t C_BORDER   = 0x2949;  // #2a2a4e border
const uint16_t C_HEADER   = 0x09EF;  // #0a3d7a blue header
const uint16_t C_AMBER    = 0x07FF;  // #00ffff cyan (replaces amber)
const uint16_t C_CYAN     = 0x07FF;  // #00ffff cyan
const uint16_t C_GREEN    = 0x47E8;  // #44ff44 bright green
const uint16_t C_RED      = 0xFA28;  // #ff4444 bright red
const uint16_t C_YELLOW   = 0xFFE8;  // #ffff44 bright yellow
const uint16_t C_BLUE     = 0x65DF;  // #66bbff light blue
const uint16_t C_TXT      = 0xFFFF;  // #ffffff white text
const uint16_t C_TXT_GRAY = 0x8410;  // #808080 labels
const uint16_t C_TXT_DIM  = 0x632C;  // #666666 status
const uint16_t C_LABEL    = 0x65DF;  // #66bbff basin names (blue)
const uint16_t C_SB_BG    = 0x1082;  // #111111 status bar bg
const uint16_t C_HDL_BG   = 0x18C5;  // #1a1a2e handle bg
const uint16_t C_HDL_BD   = 0x2949;  // #2a2a4e handle border"""

c = c.replace(old_colors, new_colors)
print("1. Colors:", "OK" if new_colors in c else "NOT FOUND")

# 2. drawMenuIcon: white text, centered in 24px header
old_menu_icon = """void drawMenuIcon() {
  for (int i = 0; i < 3; i++) {
    tft.fillRect(294, 5 + i * 5, 16, 2, C_TXT_GRAY);
  }
}"""

new_menu_icon = """void drawMenuIcon() {
  for (int i = 0; i < 3; i++) {
    tft.fillRect(294, 7 + i * 5, 16, 2, C_TXT);
  }
}"""

c = c.replace(old_menu_icon, new_menu_icon)
print("2. MenuIcon:", "OK" if new_menu_icon in c else "NOT FOUND")

# 3. drawHeader: blue solid, no maple leaf, no amber line, 24px
old_header = """void drawHeader() {
  tft.fillRect(0, 0, SW, 22, C_HEADER);
  tft.fillRect(0, 22, SW, 2, C_AMBER);
  // Amber maple leaf box
  tft.fillRoundRect(4, 2, 18, 18, 3, C_AMBER);
  drawMapleLeaf(5, 3, 1);
  // Title
  tft.setTextFont(1); tft.setTextSize(1);
  tft.setTextDatum(TL_DATUM);
  tft.setTextColor(C_TXT, C_HEADER);
  tft.drawString("CABANE MARCOUX", 26, 3);
  tft.setTextColor(C_TXT_GRAY, C_HEADER);
  tft.drawString("SYSTEME DE CONTROLE", 26, 13);
  // Menu icon (right side)
  drawMenuIcon();
  // WiFi dot
  uint16_t wc = (WiFi.status() == WL_CONNECTED) ? C_GREEN : C_RED;
  tft.fillCircle(316, 11, 3, wc);
}"""

new_header = """void drawHeader() {
  tft.fillRect(0, 0, SW, 24, C_HEADER);
  // Title
  tft.setTextFont(1); tft.setTextSize(1);
  tft.setTextDatum(ML_DATUM);
  tft.setTextColor(C_TXT, C_HEADER);
  tft.drawString("CABANE MARCOUX", 10, 12);
  // Menu icon (right side)
  drawMenuIcon();
  // WiFi dot
  uint16_t wc = (WiFi.status() == WL_CONNECTED) ? C_GREEN : C_RED;
  tft.fillCircle(316, 12, 3, wc);
}"""

c = c.replace(old_header, new_header)
print("3. Header:", "OK" if new_header in c else "NOT FOUND")

# 4. drawDompeurCard: no accent bar, cyan text, moved up
old_domp = """void drawDompeurCard() {
  int cx = 4, cy = 40, cw = SW - 8, ch = 56;
  tft.fillRect(cx, cy, cw, 2, C_AMBER);
  tft.fillRoundRect(cx, cy + 2, cw, ch - 2, 4, C_CARD);
  tft.drawRoundRect(cx, cy + 2, cw, ch - 2, 4, C_BORDER);
  tft.setTextFont(1); tft.setTextSize(1);
  tft.setTextDatum(TL_DATUM);
  tft.setTextColor(C_TXT_GRAY, C_CARD);
  tft.drawString("TEMPS DOMPEUR", cx + 10, cy + 6);
  tft.setTextSize(4);
  tft.setTextDatum(MC_DATUM);
  tft.setTextColor(C_AMBER, C_CARD);
  tft.drawString(dompeurTime.c_str(), cx + cw / 2, cy + 36);
}"""

new_domp = """void drawDompeurCard() {
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
}"""

c = c.replace(old_domp, new_domp)
print("4. DompeurCard:", "OK" if new_domp in c else "NOT FOUND")

# 5. drawBasinBar: taller bars, dark bg, yellow medium, white pct
old_bar = """void drawBasinBar(int y, const char* name, int level) {
  int nameX = 10, barX = 68, barW = 200, barH = 20;
  // Name
  tft.setTextFont(1); tft.setTextSize(1);
  tft.setTextDatum(ML_DATUM);
  tft.setTextColor(C_LABEL, C_CARD);
  tft.drawString(name, nameX, y + 12);
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
  tft.drawString(pct.c_str(), SW - 10, y + 12);
}"""

new_bar = """void drawBasinBar(int y, const char* name, int level) {
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

c = c.replace(old_bar, new_bar)
print("5. BasinBar:", "OK" if new_bar in c else "NOT FOUND")

# 6. drawBasinCards: bigger, no header, title case names
old_cards = """void drawBasinCards() {
  int cy = 112, ch = 100;
  tft.fillRoundRect(4, cy, SW - 8, ch, 4, C_CARD);
  tft.drawRoundRect(4, cy, SW - 8, ch, 4, C_BORDER);
  // Header
  tft.setTextFont(1); tft.setTextSize(1);
  tft.setTextDatum(TL_DATUM);
  tft.setTextColor(C_TXT_GRAY, C_CARD);
  tft.drawString("ETAT DE REMPLISSAGE", 10, cy + 4);
  // Big basin bars
  drawBasinBar(cy + 16, "BASSIN 1", basin1);
  drawBasinBar(cy + 44, "BASSIN 2", basin2);
  drawBasinBar(cy + 72, "BASSIN 3", basin3);
}"""

new_cards = """void drawBasinCards() {
  int cy = 88, ch = 120;
  tft.fillRoundRect(4, cy, SW - 8, ch, 6, C_CARD);
  tft.drawRoundRect(4, cy, SW - 8, ch, 6, C_BORDER);
  // Basin bars (evenly spaced)
  drawBasinBar(cy + 12, "Bassin 1", basin1);
  drawBasinBar(cy + 48, "Bassin 2", basin2);
  drawBasinBar(cy + 84, "Bassin 3", basin3);
}"""

c = c.replace(old_cards, new_cards)
print("6. BasinCards:", "OK" if new_cards in c else "NOT FOUND")

# 7. drawMainScreen: remove section dividers
old_main = """void drawMainScreen() {
  tft.fillScreen(C_BG);
  drawHeader();
  drawSectionDiv(28, "DOMPEUR");
  drawDompeurCard();
  drawSectionDiv(100, "NIVEAU DES BASSINS");
  drawBasinCards();
  drawStatusBar();
}"""

new_main = """void drawMainScreen() {
  tft.fillScreen(C_BG);
  drawHeader();
  drawDompeurCard();
  drawBasinCards();
  drawStatusBar();
}"""

c = c.replace(old_main, new_main)
print("7. MainScreen:", "OK" if new_main in c else "NOT FOUND")

# 8. drawStatusBar: radius 3 -> 6
old_sb = """  int sy = 216, sh = 20;
  tft.fillRoundRect(4, sy, SW - 8, sh, 3, C_SB_BG);
  tft.drawRoundRect(4, sy, SW - 8, sh, 3, C_BORDER);"""

new_sb = """  int sy = 216, sh = 20;
  tft.fillRoundRect(4, sy, SW - 8, sh, 6, C_SB_BG);
  tft.drawRoundRect(4, sy, SW - 8, sh, 6, C_BORDER);"""

c = c.replace(old_sb, new_sb)
print("8. StatusBar:", "OK" if new_sb in c else "NOT FOUND")

with open(f, 'w', encoding='utf-8') as fh:
    fh.write(c)

import os
print(f"\nDone! Size: {os.path.getsize(f)} bytes")
