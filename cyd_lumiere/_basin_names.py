path = r"C:\Users\ryb086\OneDrive - Groupe R.Y. Beaudoin\Bureau\CLAUDE_CODE\cyd_lumiere\src\main.cpp"
with open(path, 'r', encoding='utf-8') as f:
    code = f.read()

code = code.replace(
    'drawBasinTank(4 + gap, tankW, tankH, topY, "B1", basin1);',
    'drawBasinTank(4 + gap, tankW, tankH, topY, "Eau erable", basin1);'
)
code = code.replace(
    'drawBasinTank(4 + gap * 2 + tankW, tankW, tankH, topY, "B2", basin2);',
    'drawBasinTank(4 + gap * 2 + tankW, tankW, tankH, topY, "Concentre", basin2);'
)
code = code.replace(
    'drawBasinTank(4 + gap * 3 + tankW * 2, tankW, tankH, topY, "B3", basin3);',
    'drawBasinTank(4 + gap * 3 + tankW * 2, tankW, tankH, topY, "Permeat", basin3);'
)

with open(path, 'w', encoding='utf-8') as f:
    f.write(code)

print("Basin names updated: Eau erable, Concentre, Permeat")
