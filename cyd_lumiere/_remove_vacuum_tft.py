path = r"C:\Users\ryb086\OneDrive - Groupe R.Y. Beaudoin\Bureau\CLAUDE_CODE\cyd_lumiere\src\main.cpp"
with open(path, 'r', encoding='utf-8') as f:
    code = f.read()

# 1. Remove drawVacuumBtn() call from drawMainScreen
code = code.replace(
    "  drawDompeurCard();\n  drawBasinCards();\n  drawVacuumBtn();\n",
    "  drawDompeurCard();\n  drawBasinCards();\n"
)

# 2. Remove vacuum touch handler from handleMainTouch
code = code.replace(
    """  // Vacuum slider touch -> open PIN
  if (ty >= 214 && ty <= 236) {
    pinReason = 1;
    pinCode = "";
    currentScreen = SCREEN_PIN;
    drawPinScreen();
    return;
  }""",
    "  // Vacuum slider removed from TFT"
)

with open(path, 'w', encoding='utf-8') as f:
    f.write(code)

print("Vacuum slider removed from TFT screen")
