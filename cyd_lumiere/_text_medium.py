path = r"C:\Users\ryb086\OneDrive - Groupe R.Y. Beaudoin\Bureau\CLAUDE_CODE\cyd_lumiere\src\main.cpp"
with open(path, 'r', encoding='utf-8') as f:
    code = f.read()

# Use Font2 (16px proportional) instead of Font1 size 2 (blocky)
# Names
code = code.replace(
    '''  // Name label above tank
  tft.setTextFont(1); tft.setTextSize(2);
  tft.setTextDatum(TC_DATUM);
  tft.setTextColor(C_LABEL, C_CARD);
  tft.drawString(name, cx + tankW / 2, topY);''',
    '''  // Name label above tank
  tft.setTextFont(2); tft.setTextSize(1);
  tft.setTextDatum(TC_DATUM);
  tft.setTextColor(C_LABEL, C_CARD);
  tft.drawString(name, cx + tankW / 2, topY);'''
)

# Percentage
code = code.replace(
    '''  // Percentage below tank
  tft.setTextDatum(TC_DATUM);
  tft.setTextColor(C_TXT, C_CARD);
  tft.setTextSize(2);
  String pct = String(level) + "%";
  tft.drawString(pct.c_str(), cx + tankW / 2, ty + tankH + 4);''',
    '''  // Percentage below tank
  tft.setTextDatum(TC_DATUM);
  tft.setTextColor(C_TXT, C_CARD);
  tft.setTextFont(2); tft.setTextSize(1);
  String pct = String(level) + "%";
  tft.drawString(pct.c_str(), cx + tankW / 2, ty + tankH + 3);'''
)

# Restore tank height
code = code.replace(
    'int tankW = 70, tankH = 90;',
    'int tankW = 70, tankH = 95;'
)

code = code.replace(
    '  int ty = topY + 18;',
    '  int ty = topY + 16;'
)

with open(path, 'w', encoding='utf-8') as f:
    f.write(code)

print("Text changed to Font2 (medium 16px)")
