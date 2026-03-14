path = r"C:\Users\ryb086\OneDrive - Groupe R.Y. Beaudoin\Bureau\CLAUDE_CODE\cyd_lumiere\src\main.cpp"
with open(path, 'r', encoding='utf-8') as f:
    code = f.read()

# Name label - change from textSize 1 to 2
code = code.replace(
    '''  // Name label above tank
  tft.setTextFont(1); tft.setTextSize(1);
  tft.setTextDatum(TC_DATUM);
  tft.setTextColor(C_LABEL, C_CARD);
  tft.drawString(name, cx + tankW / 2, topY);''',
    '''  // Name label above tank
  tft.setTextFont(1); tft.setTextSize(2);
  tft.setTextDatum(TC_DATUM);
  tft.setTextColor(C_LABEL, C_CARD);
  tft.drawString(name, cx + tankW / 2, topY);'''
)

# Percentage below tank - change from textSize 1 to 2
code = code.replace(
    '''  // Percentage below tank
  tft.setTextDatum(TC_DATUM);
  tft.setTextColor(C_TXT, C_CARD);
  tft.setTextSize(1);
  String pct = String(level) + "%";
  tft.drawString(pct.c_str(), cx + tankW / 2, ty + tankH + 3);''',
    '''  // Percentage below tank
  tft.setTextDatum(TC_DATUM);
  tft.setTextColor(C_TXT, C_CARD);
  tft.setTextSize(2);
  String pct = String(level) + "%";
  tft.drawString(pct.c_str(), cx + tankW / 2, ty + tankH + 4);'''
)

# Adjust tank height to make room for bigger text
code = code.replace(
    'int tankW = 70, tankH = 105;',
    'int tankW = 70, tankH = 90;'
)

# Move tank start lower for bigger name text
code = code.replace(
    '  int ty = topY + 12;',
    '  int ty = topY + 18;'
)

with open(path, 'w', encoding='utf-8') as f:
    f.write(code)

print("Text size increased to 2 for names and percentages")
