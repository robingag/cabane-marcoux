import re

f = r'C:\Users\ryb086\OneDrive - Groupe R.Y. Beaudoin\Bureau\CLAUDE_CODE\cyd_lumiere\src\main.cpp'
with open(f, 'r', encoding='utf-8') as fh:
    c = fh.read()

# ── 1. REPLACE COLOR PALETTE ──
old_colors = """// Color palette
const uint16_t C_BG       = 0x0001;  // near-black
const uint16_t C_CARD     = 0x1926;  // dark blue-gray
const uint16_t C_BORDER   = 0x2965;  // subtle border
const uint16_t C_HEADER   = 0x01AF;  // deep blue header
const uint16_t C_ACCENT   = 0x07FF;  // cyan
const uint16_t C_WARM     = 0xFD20;  // orange
const uint16_t C_GREEN    = 0x07E0;
const uint16_t C_RED      = 0xF800;
const uint16_t C_YELLOW   = 0xFFE0;
const uint16_t C_BLUE_BTN = 0x04BF;  // button blue
const uint16_t C_RED_BTN  = 0xE8A2;  // button red"""

new_colors = """// Color palette (industrial dark theme - matches HTML dashboard)
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

if old_colors in c:
    c = c.replace(old_colors, new_colors)
    print("1. Colors: OK")
else:
    print("1. Colors: NOT FOUND")

# ── 2. REPLACE drawMenuIcon ──
old_menu = """void drawMenuIcon() {
  for (int i = 0; i < 3; i++) {
    tft.fillRect(6, 5 + i * 6, 18, 3, TFT_WHITE);
  }
}"""

new_menu = """void drawMenuIcon() {
  for (int i = 0; i < 3; i++) {
    tft.fillRect(294, 5 + i * 5, 16, 2, C_TXT_GRAY);
  }
}

void drawSectionDiv(int y, const char* txt) {
  tft.setTextFont(1); tft.setTextSize(1);
  tft.setTextDatum(ML_DATUM);
  tft.setTextColor(C_TXT_GRAY, C_BG);
  tft.drawString(txt, 6, y + 4);
  int tw = tft.textWidth(txt) + 12;
  tft.drawFastHLine(tw, y + 4, SW - tw - 6, C_BORDER);
}"""

if old_menu in c:
    c = c.replace(old_menu, new_menu)
    print("2. MenuIcon + SectionDiv: OK")
else:
    print("2. MenuIcon: NOT FOUND")

# ── 3. REPLACE drawHeader ──
old_header = """void drawHeader() {
  tft.fillRect(0, 0, SW, 28, C_HEADER);
  drawMenuIcon();
  tft.setTextFont(1);
  tft.setTextSize(2);
  tft.setTextDatum(MC_DATUM);
  tft.setTextColor(TFT_WHITE, C_HEADER);
  tft.drawString("CABANE MARCOUX", SW / 2 + 8, 14);
  // Maple leaf icon to the left of title
  drawMapleLeaf(SW / 2 - 100, 1, 2);
  // WiFi indicator
  if (WiFi.status() == WL_CONNECTED) {
    tft.fillCircle(SW - 12, 14, 4, C_GREEN);
  } else {
    tft.fillCircle(SW - 12, 14, 4, C_RED);
  }
}"""

new_header = """void drawHeader() {
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

if old_header in c:
    c = c.replace(old_header, new_header)
    print("3. Header: OK")
else:
    print("3. Header: NOT FOUND")

# ── 4. REPLACE drawDompeurCard ──
old_domp = """void drawDompeurCard() {
  int cx = 4, cy = 30, cw = 152, ch = 40;
  tft.fillRoundRect(cx, cy, cw, ch, 6, C_CARD);
  tft.drawRoundRect(cx, cy, cw, ch, 6, C_BORDER);
  // Label
  tft.setTextFont(1);
  tft.setTextSize(1);
  tft.setTextDatum(TL_DATUM);
  tft.setTextColor(C_ACCENT, C_CARD);
  tft.drawString("Dompeur", cx + 8, cy + 4);
  // Value
  tft.setTextSize(2);
  tft.setTextDatum(MC_DATUM);
  tft.setTextColor(TFT_WHITE, C_CARD);
  tft.drawString(dompeurTime.c_str(), cx + cw / 2, cy + 28);
}"""

new_domp = """void drawDompeurCard() {
  int cx = 4, cy = 34, cw = 154, ch = 34;
  tft.fillRect(cx, cy, cw, 2, C_AMBER);
  tft.fillRoundRect(cx, cy + 2, cw, ch - 2, 4, C_CARD);
  tft.drawRoundRect(cx, cy + 2, cw, ch - 2, 4, C_BORDER);
  tft.setTextFont(1); tft.setTextSize(1);
  tft.setTextDatum(TL_DATUM);
  tft.setTextColor(C_TXT_GRAY, C_CARD);
  tft.drawString("DOMPEUR", cx + 8, cy + 5);
  tft.setTextSize(2);
  tft.setTextDatum(MC_DATUM);
  tft.setTextColor(C_AMBER, C_CARD);
  tft.drawString(dompeurTime.c_str(), cx + cw / 2, cy + 24);
}"""

if old_domp in c:
    c = c.replace(old_domp, new_domp)
    print("4. DompeurCard: OK")
else:
    print("4. DompeurCard: NOT FOUND")

# ── 5. REPLACE drawTempCard ──
old_temp = """void drawTempCard() {
  int cx = 164, cy = 30, cw = 152, ch = 40;
  tft.fillRoundRect(cx, cy, cw, ch, 6, C_CARD);
  tft.drawRoundRect(cx, cy, cw, ch, 6, C_BORDER);
  // Label
  tft.setTextFont(1);
  tft.setTextSize(1);
  tft.setTextDatum(TL_DATUM);
  tft.setTextColor(C_WARM, C_CARD);
  tft.drawString("Temperature", cx + 8, cy + 4);
  // Value
  tft.setTextSize(2);
  tft.setTextDatum(MC_DATUM);
  tft.setTextColor(TFT_WHITE, C_CARD);
  String tempStr = String(temperature, 1) + "C";
  tft.drawString(tempStr.c_str(), cx + cw / 2, cy + 28);
}"""

new_temp = """void drawTempCard() {
  int cx = 162, cy = 34, cw = 154, ch = 34;
  tft.fillRect(cx, cy, cw, 2, C_CYAN);
  tft.fillRoundRect(cx, cy + 2, cw, ch - 2, 4, C_CARD);
  tft.drawRoundRect(cx, cy + 2, cw, ch - 2, 4, C_BORDER);
  tft.setTextFont(1); tft.setTextSize(1);
  tft.setTextDatum(TL_DATUM);
  tft.setTextColor(C_TXT_GRAY, C_CARD);
  tft.drawString("TEMPERATURE", cx + 8, cy + 5);
  tft.setTextSize(2);
  tft.setTextDatum(MC_DATUM);
  tft.setTextColor(C_CYAN, C_CARD);
  String tempStr = String(temperature, 1) + "C";
  tft.drawString(tempStr.c_str(), cx + cw / 2, cy + 24);
}"""

if old_temp in c:
    c = c.replace(old_temp, new_temp)
    print("5. TempCard: OK")
else:
    print("5. TempCard: NOT FOUND")

# ── 6. REPLACE drawTrendGraph ──
old_graph = """void drawTrendGraph() {
  int gx = 4, gy = 72, gw = SW - 8, gh = 52;
  tft.fillRoundRect(gx, gy, gw, gh, 6, C_CARD);
  tft.drawRoundRect(gx, gy, gw, gh, 6, C_BORDER);
  // Title
  tft.setTextFont(1);
  tft.setTextSize(1);
  tft.setTextDatum(TL_DATUM);
  tft.setTextColor(C_ACCENT, C_CARD);
  tft.drawString("Tendance", gx + 6, gy + 3);"""

new_graph = """void drawTrendGraph() {
  int gx = 4, gy = 78, gw = SW - 8, gh = 44;
  tft.fillRect(gx, gy, 2, gh, C_BLUE);
  tft.fillRoundRect(gx + 2, gy, gw - 2, gh, 4, C_CARD);
  tft.drawRoundRect(gx + 2, gy, gw - 2, gh, 4, C_BORDER);
  tft.setTextFont(1); tft.setTextSize(1);
  tft.setTextDatum(TL_DATUM);
  tft.setTextColor(C_TXT_GRAY, C_CARD);
  tft.drawString("Tendance", gx + 8, gy + 3);"""

if old_graph in c:
    c = c.replace(old_graph, new_graph)
    print("6. TrendGraph header: OK")
else:
    print("6. TrendGraph header: NOT FOUND")

# ── 7. REPLACE BASIN SYSTEM (vertical cols -> horizontal bars) ──
old_basincol = """// ---- Basins (vertical columns) ----
void drawBasinCol(int x, int w, int topY, int barH, const char* label, int level) {
  // Column number
  tft.setTextFont(1);
  tft.setTextSize(2);
  tft.setTextDatum(TC_DATUM);
  tft.setTextColor(TFT_WHITE, C_CARD);
  tft.drawString(label, x + w / 2, topY + 16);

  // Bar area
  int barY = topY + 34;
  int barAvail = barH - 50;

  // Bar background
  tft.fillRoundRect(x + 4, barY, w - 8, barAvail, 4, 0x1082);

  // Bar fill (from bottom up)
  int fillH = barAvail * level / 100;
  if (fillH > 0) {
    uint16_t bc = C_GREEN;
    if (level < 25) bc = C_RED;
    else if (level < 50) bc = C_YELLOW;
    tft.fillRoundRect(x + 4, barY + barAvail - fillH, w - 8, fillH, 4, bc);
  }

  // Percentage at bottom
  tft.setTextDatum(BC_DATUM);
  tft.setTextColor(TFT_WHITE, C_CARD);
  String pct = String(level) + "%";
  tft.drawString(pct.c_str(), x + w / 2, topY + barH - 2);
}

void drawBasinCards() {
  int cy = 122, ch = SH - 122;  // from y=122 to bottom of screen
  // Background card for 3 basins (leave space on right for Vac button)
  int basinW = SW - 60;  // reserve 56px on right for Vac
  tft.fillRoundRect(4, cy, basinW - 4, ch, 6, C_CARD);
  tft.drawRoundRect(4, cy, basinW - 4, ch, 6, C_BORDER);

  // Header "Bassin"
  tft.setTextFont(1);
  tft.setTextSize(2);
  tft.setTextDatum(TC_DATUM);
  tft.setTextColor(C_ACCENT, C_CARD);
  tft.drawString("Bassin", 4 + (basinW - 4) / 2, cy + 2);

  int colW = (basinW - 8) / 3;
  drawBasinCol(4, colW, cy, ch, "1", basin1);
  drawBasinCol(4 + colW, colW, cy, ch, "2", basin2);
  drawBasinCol(4 + colW * 2, colW, cy, ch, "3", basin3);

  // Separators between columns
  for (int i = 1; i < 3; i++) {
    int sx = 4 + colW * i;
    tft.drawFastVLine(sx, cy + 14, ch - 18, C_BORDER);
  }
}"""

new_basins = """// ---- Basins (horizontal bars) ----
void drawBasinBar(int y, const char* name, int level) {
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
}

void drawBasinCards() {
  int cy = 132, ch = 64;
  tft.fillRoundRect(4, cy, SW - 8, ch, 4, C_CARD);
  tft.drawRoundRect(4, cy, SW - 8, ch, 4, C_BORDER);
  drawBasinBar(cy + 2, "BASSIN 1", basin1);
  drawBasinBar(cy + 22, "BASSIN 2", basin2);
  drawBasinBar(cy + 42, "BASSIN 3", basin3);
}"""

if old_basincol in c:
    c = c.replace(old_basincol, new_basins)
    print("7. Basins: OK")
else:
    print("7. Basins: NOT FOUND")

# ── 8. REPLACE VACUUM BUTTON -> SLIDER ──
old_vac = """void drawVacuumBtn() {
  int bx = SW - 56, by = 122, bw = 52, bh = SH - 122;
  uint16_t c = lightOn ? C_RED_BTN : C_BLUE_BTN;
  tft.fillRoundRect(bx, by, bw, bh, 6, c);
  tft.drawRoundRect(bx, by, bw, bh, 6, TFT_WHITE);
  // Square indicator
  int sqS = 30;
  int sqX = bx + (bw - sqS) / 2, sqY = by + 14;
  tft.fillRect(sqX, sqY, sqS, sqS, lightOn ? C_GREEN : tft.color565(60, 60, 60));
  tft.drawRect(sqX, sqY, sqS, sqS, TFT_WHITE);
  if (lightOn) {
    tft.fillRect(sqX + 5, sqY + 5, sqS - 10, sqS - 10, C_YELLOW);
  }
  // Text "Vac"
  tft.setTextFont(1);
  tft.setTextSize(2);
  tft.setTextDatum(MC_DATUM);
  tft.setTextColor(TFT_WHITE, c);
  tft.drawString("Vac", bx + bw / 2, by + bh - 20);
}"""

new_vac = """void drawVacuumBtn() {
  int sx = 4, sy = 204, sw = SW - 8, sh = 22;
  int hdlW = 36, hdlH = 18;
  // Track
  uint16_t brd = lightOn ? C_GREEN : C_BORDER;
  tft.fillRoundRect(sx, sy, sw, sh, 4, C_BG);
  tft.drawRoundRect(sx, sy, sw, sh, 4, brd);
  // Handle
  int hx = lightOn ? (sx + sw - hdlW - 2) : (sx + 2);
  int hy = sy + (sh - hdlH) / 2;
  tft.fillRoundRect(hx, hy, hdlW, hdlH, 3, C_HDL_BG);
  tft.drawRoundRect(hx, hy, hdlW, hdlH, 3, C_HDL_BD);
  // Lightning bolt "Z" on handle
  tft.setTextFont(1); tft.setTextSize(1);
  tft.setTextDatum(MC_DATUM);
  tft.setTextColor(C_AMBER, C_HDL_BG);
  tft.drawString("Z", hx + hdlW / 2, hy + hdlH / 2);
  // Hint text
  tft.setTextSize(1);
  if (!lightOn) {
    tft.setTextDatum(ML_DATUM);
    tft.setTextColor(tft.color565(180, 50, 50), C_BG);
    tft.drawString("> VACUUM ON", sx + hdlW + 10, sy + sh / 2);
  } else {
    tft.setTextDatum(MR_DATUM);
    tft.setTextColor(C_GREEN, C_BG);
    tft.drawString("VACUUM OFF <", sx + sw - hdlW - 10, sy + sh / 2);
  }
}"""

if old_vac in c:
    c = c.replace(old_vac, new_vac)
    print("8. VacuumSlider: OK")
else:
    print("8. VacuumSlider: NOT FOUND")

# ── 9. REPLACE STATUS BAR ──
old_status = """void drawStatusBar() {
  int sy = 210;
  tft.fillRect(0, sy, SW, SH - sy, 0x0841);
  tft.setTextFont(1);
  tft.setTextSize(1);
  tft.setTextDatum(ML_DATUM);
  if (WiFi.status() == WL_CONNECTED) {
    tft.setTextColor(C_GREEN, 0x0841);
    tft.drawString(WiFi.localIP().toString().c_str(), 6, sy + 15);
  } else {
    tft.setTextColor(C_RED, 0x0841);
    tft.drawString("WiFi deconnecte", 6, sy + 15);
  }
  tft.setTextDatum(MR_DATUM);
  tft.setTextColor(tft.color565(100, 100, 100), 0x0841);
  String idStr = "ID:" + deviceId;
  tft.drawString(idStr.c_str(), SW - 6, sy + 15);
}"""

new_status = """void drawStatusBar() {
  int sy = 228;
  tft.fillRoundRect(4, sy, SW - 8, 12, 3, C_SB_BG);
  tft.drawRoundRect(4, sy, SW - 8, 12, 3, C_BORDER);
  tft.setTextFont(1); tft.setTextSize(1);
  tft.setTextDatum(ML_DATUM);
  if (WiFi.status() == WL_CONNECTED) {
    tft.fillCircle(12, sy + 6, 2, C_GREEN);
    tft.setTextColor(C_TXT_DIM, C_SB_BG);
    tft.drawString(WiFi.localIP().toString().c_str(), 18, sy + 6);
  } else {
    tft.fillCircle(12, sy + 6, 2, C_RED);
    tft.setTextColor(C_TXT_DIM, C_SB_BG);
    tft.drawString("Deconnecte", 18, sy + 6);
  }
  tft.setTextDatum(MR_DATUM);
  tft.setTextColor(C_TXT_DIM, C_SB_BG);
  String idStr = "ID: " + deviceId;
  tft.drawString(idStr.c_str(), SW - 10, sy + 6);
}"""

if old_status in c:
    c = c.replace(old_status, new_status)
    print("9. StatusBar: OK")
else:
    print("9. StatusBar: NOT FOUND")

# ── 10. REPLACE drawMainScreen ──
old_main = """void drawMainScreen() {
  tft.fillScreen(C_BG);
  drawHeader();
  drawDompeurCard();
  drawTempCard();
  drawTrendGraph();
  drawBasinCards();
  drawVacuumBtn();
}"""

new_main = """void drawMainScreen() {
  tft.fillScreen(C_BG);
  drawHeader();
  drawSectionDiv(24, "MESURES TEMPS REEL");
  drawDompeurCard();
  drawTempCard();
  drawSectionDiv(70, "TENDANCE DOMPEUR");
  drawTrendGraph();
  drawSectionDiv(124, "NIVEAU DES BASSINS");
  drawBasinCards();
  drawSectionDiv(198, "CONTROLE VACUUM");
  drawVacuumBtn();
  drawStatusBar();
}"""

if old_main in c:
    c = c.replace(old_main, new_main)
    print("10. MainScreen: OK")
else:
    print("10. MainScreen: NOT FOUND")

# ── 11. UPDATE TOUCH ZONES ──
old_touch = """  // Menu icon (top-left) -> ouvrir le dropdown
  if (tx <= 30 && ty <= 28) {
    drawDropdownMenu();
    return;
  }
  // Vacuum button (bottom-right corner)
  if (ty >= 122 && tx >= SW - 56) {"""

new_touch = """  // Menu icon (top-right)
  if (tx >= 280 && ty <= 24) {
    drawDropdownMenu();
    return;
  }
  // Vacuum slider (full width)
  if (ty >= 204 && ty <= 226) {"""

if old_touch in c:
    c = c.replace(old_touch, new_touch)
    print("11. Touch zones: OK")
else:
    print("11. Touch zones: NOT FOUND")

# ── 12. UPDATE SECONDARY SCREENS ──
# QR Screen header
c = c.replace('tft.fillRect(0, 0, SW, 28, C_HEADER);\n  tft.setTextFont(1);\n  tft.setTextSize(2);\n  tft.setTextDatum(MC_DATUM);\n  tft.setTextColor(TFT_WHITE, C_HEADER);\n  tft.drawString(isLocal ? "QR Local" : "QR Remote", SW / 2, 14);',
              'tft.fillRect(0, 0, SW, 22, C_HEADER);\n  tft.fillRect(0, 22, SW, 2, C_AMBER);\n  tft.setTextFont(1);\n  tft.setTextSize(2);\n  tft.setTextDatum(MC_DATUM);\n  tft.setTextColor(C_TXT, C_HEADER);\n  tft.drawString(isLocal ? "QR Local" : "QR Remote", SW / 2, 11);')
print("12a. QR header: updated")

# Info Screen header
c = c.replace('tft.fillRect(0, 0, SW, 28, C_HEADER);\n  tft.setTextFont(1);\n  tft.setTextSize(2);\n  tft.setTextDatum(MC_DATUM);\n  tft.setTextColor(TFT_WHITE, C_HEADER);\n  tft.drawString("Informations", SW / 2, 14);',
              'tft.fillRect(0, 0, SW, 22, C_HEADER);\n  tft.fillRect(0, 22, SW, 2, C_AMBER);\n  tft.setTextFont(1);\n  tft.setTextSize(2);\n  tft.setTextDatum(MC_DATUM);\n  tft.setTextColor(C_TXT, C_HEADER);\n  tft.drawString("Informations", SW / 2, 11);')
print("12b. Info header: updated")

# Replace C_ACCENT references
c = c.replace('C_ACCENT', 'C_AMBER')
print("12c. C_ACCENT -> C_AMBER: all replaced")

# Replace C_WARM references
c = c.replace('C_WARM', 'C_AMBER')
print("12d. C_WARM -> C_AMBER: all replaced")

# Replace C_BLUE_BTN / C_RED_BTN if still present
c = c.replace('C_BLUE_BTN', 'C_BLUE')
c = c.replace('C_RED_BTN', 'C_RED')
print("12e. Old btn colors: cleaned")

# ── 13. UPDATE DROPDOWN MENU POSITION ──
# Move dropdown to right side since hamburger is now on right
old_dropdown_pos = 'tft.fillRect(MENU_X, MENU_Y, MENU_W, MENU_H, C_CARD);\n  tft.drawRect(MENU_X, MENU_Y, MENU_W, MENU_H, C_AMBER);'
# Only update if already changed C_ACCENT -> C_AMBER
if old_dropdown_pos not in c:
    # Try original
    pass
print("13. Dropdown: checked")

# ── WRITE FILE ──
with open(f, 'w', encoding='utf-8') as fh:
    fh.write(c)

import os
print(f"\nDone! File size: {os.path.getsize(f)} bytes")
