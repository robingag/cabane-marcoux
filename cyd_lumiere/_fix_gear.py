f = r'C:\Users\ryb086\OneDrive - Groupe R.Y. Beaudoin\Bureau\CLAUDE_CODE\cyd_lumiere\Cabane_Marcoux.html'
with open(f, 'r', encoding='utf-8') as fh:
    c = fh.read()

# 1. Grossir le gear icon CSS (16px -> 28px) et enlever position absolute
old_css = '.cal-gear{position:absolute;top:10px;right:12px;background:none;border:none;color:#475569;font-size:16px;cursor:pointer;padding:4px;transition:color .2s}'
new_css = '.cal-gear{background:none;border:none;color:#475569;font-size:28px;cursor:pointer;padding:2px 0;transition:color .2s;line-height:1}'
c = c.replace(old_css, new_css)
print("CSS gear: updated" if new_css in c else "CSS gear: NOT FOUND")

# 2. Remplacer les 3 barres verticales par le bouton gear dans le header
old_hd = '<div class="bc-hd"><span>&#201;tat de remplissage</span><span>&#9646;&#9646;&#9646;</span></div>'
new_hd = '<div class="bc-hd"><span>&#201;tat de remplissage</span><button class="cal-gear" onclick="showCalPin()">&#9881;</button></div>'
c = c.replace(old_hd, new_hd)
print("Header: updated" if new_hd in c else "Header: NOT FOUND")

# 3. Supprimer l'ancien bouton gear separé
old_btn = '    <button class="cal-gear" onclick="showCalPin()">&#9881;</button>\n  </div>'
new_btn = '  </div>'
c = c.replace(old_btn, new_btn)
print("Old button: removed" if old_btn not in c else "Old button: still present")

with open(f, 'w', encoding='utf-8') as fh:
    fh.write(c)

# Update index.html too
import shutil
idx = r'C:\Users\ryb086\OneDrive - Groupe R.Y. Beaudoin\Bureau\CLAUDE_CODE\index.html'
shutil.copy2(f, idx)

import os
print(f"\nDone! Size: {os.path.getsize(f)} bytes")
