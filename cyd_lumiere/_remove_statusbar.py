f = r'C:\Users\ryb086\OneDrive - Groupe R.Y. Beaudoin\Bureau\CLAUDE_CODE\cyd_lumiere\src\main.cpp'
with open(f, 'r', encoding='utf-8') as fh:
    c = fh.read()

# 1. Agrandir drawBasinCards pour remplir jusqu'au bas (cy=88, ch=148 au lieu de 120)
old_basin = """void drawBasinCards() {
  int cy = 88, ch = 120;"""
new_basin = """void drawBasinCards() {
  int cy = 88, ch = 148;"""
c = c.replace(old_basin, new_basin)
print("1. BasinCards height:", "OK" if "ch = 148" in c else "NOT FOUND")

# 2. Retirer drawStatusBar() de drawMainScreen
old_main = """void drawMainScreen() {
  tft.fillScreen(C_BG);
  drawHeader();
  drawDompeurCard();
  drawBasinCards();
  drawStatusBar();
}"""
new_main = """void drawMainScreen() {
  tft.fillScreen(C_BG);
  drawHeader();
  drawDompeurCard();
  drawBasinCards();
}"""
c = c.replace(old_main, new_main)
print("2. Remove drawStatusBar call:", "OK" if new_main in c else "NOT FOUND")

with open(f, 'w', encoding='utf-8') as fh:
    fh.write(c)

import os
print(f"\nDone! Size: {os.path.getsize(f)} bytes")
