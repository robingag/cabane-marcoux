filepath = r"C:\Users\ryb086\OneDrive - Groupe R.Y. Beaudoin\Bureau\CLAUDE_CODE\cyd_lumiere\src\main.cpp"

with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Remove drawVacuumBtn() from drawMainScreen
content = content.replace(
    """void drawMainScreen() {
  tft.fillScreen(C_BG);
  drawHeader();
  drawDompeurCard();
  drawBasinCards();
  drawVacuumBtn();
}""",
    """void drawMainScreen() {
  tft.fillScreen(C_BG);
  drawHeader();
  drawDompeurCard();
  drawBasinCards();
}""")

# 2. Remove vacuum touch zone from handleMainTouch
content = content.replace(
    """  // Vacuum toggle (bottom bar, y=214 to 236)
  if (ty >= 214 && ty <= 236) {
    lightOn = !lightOn;
    drawVacuumBtn();
    publishState();
    Serial.printf(">>> Touch: Vacuum %s\\n", lightOn ? "ON" : "OFF");
    return;
  }
}""",
    """}""")

# 3. Restore basin cards to full height (148px)
content = content.replace(
    """void drawBasinCards() {
  int cy = 88, ch = 124;
  tft.fillRoundRect(4, cy, SW - 8, ch, 6, C_CARD);
  tft.drawRoundRect(4, cy, SW - 8, ch, 6, C_BORDER);
  // Basin bars (espacement 38px, compact pour laisser place au vacuum)
  drawBasinBar(cy + 8, "Bassin 1", basin1);
  drawBasinBar(cy + 46, "Bassin 2", basin2);
  drawBasinBar(cy + 84, "Bassin 3", basin3);
}""",
    """void drawBasinCards() {
  int cy = 88, ch = 148;
  tft.fillRoundRect(4, cy, SW - 8, ch, 6, C_CARD);
  tft.drawRoundRect(4, cy, SW - 8, ch, 6, C_BORDER);
  drawBasinBar(cy + 20, "Bassin 1", basin1);
  drawBasinBar(cy + 68, "Bassin 2", basin2);
  drawBasinBar(cy + 116, "Bassin 3", basin3);
}""")

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)

print("OK - Vacuum slider retire, bassins restaures pleine hauteur")
