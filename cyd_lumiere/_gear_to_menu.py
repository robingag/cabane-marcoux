f = r'C:\Users\ryb086\OneDrive - Groupe R.Y. Beaudoin\Bureau\CLAUDE_CODE\cyd_lumiere\src\main.cpp'
with open(f, 'r', encoding='utf-8') as fh:
    c = fh.read()

# 1. Menu: 4 -> 5 items, ajouter Calibration
old_menu_def = """#define MENU_ITEMS   4
"""
new_menu_def = """#define MENU_ITEMS   5
"""
c = c.replace(old_menu_def, new_menu_def)
print("1. MENU_ITEMS 5:", "OK" if "#define MENU_ITEMS   5" in c else "NOT FOUND")

old_labels = 'const char* menuLabels[MENU_ITEMS] = { "WiFi", "QR Local", "QR Remote", "Infos" };'
new_labels = 'const char* menuLabels[MENU_ITEMS] = { "WiFi", "QR Local", "QR Remote", "Infos", "Calibration" };'
c = c.replace(old_labels, new_labels)
print("2. menuLabels:", "OK" if '"Calibration"' in c else "NOT FOUND")

# 3. handleDropdownTouch: ajouter case 4 Calibration
old_case3 = """      case 3: // Infos
        menuOpen = false;
        currentScreen = SCREEN_INFO;
        drawInfoScreen();
        break;
    }"""
new_case3 = """      case 3: // Infos
        menuOpen = false;
        currentScreen = SCREEN_INFO;
        drawInfoScreen();
        break;
      case 4: // Calibration
        menuOpen = false;
        pinCode = "";
        currentScreen = SCREEN_PIN;
        drawPinScreen();
        break;
    }"""
c = c.replace(old_case3, new_case3)
print("3. case 4 Calibration:", "OK" if "case 4: // Calibration" in c else "NOT FOUND")

# 4. Retirer drawGearIcon() de drawBasinCards
old_basin_gear = """  // Gear icon (top-right of card, 24x24)
  drawGearIcon(SW - 32, cy + 4);
  // Basin bars descendues (espacement 44px)"""
new_basin_no_gear = """  // Basin bars descendues (espacement 44px)"""
c = c.replace(old_basin_gear, new_basin_no_gear)
print("4. Remove gear from card:", "OK" if "drawGearIcon(SW" not in c else "NOT FOUND")

# 5. Retirer touch zone gear dans handleMainTouch
old_gear_touch = """  // Gear icon on basin card -> PIN screen
  if (tx >= SW - 36 && tx <= SW - 4 && ty >= 86 && ty <= 120) {
    pinCode = "";
    currentScreen = SCREEN_PIN;
    drawPinScreen();
    return;
  }
}"""
new_no_gear_touch = """}"""
c = c.replace(old_gear_touch, new_no_gear_touch)
print("5. Remove gear touch:", "OK" if "Gear icon on basin" not in c else "NOT FOUND")

with open(f, 'w', encoding='utf-8') as fh:
    fh.write(c)

import os
print(f"\nDone! Size: {os.path.getsize(f)} bytes")
