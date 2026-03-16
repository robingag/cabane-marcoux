path = r"C:\Users\ryb086\OneDrive - Groupe R.Y. Beaudoin\Bureau\CLAUDE_CODE\cyd_lumiere\src\main.cpp"
with open(path, 'r', encoding='utf-8') as f:
    code = f.read()

code = code.replace(
    """      case 1: // QR WiFi
        menuOpen = false;
        currentScreen = SCREEN_QR_LOCAL;
        drawQRScreen(true);
        }
        break;""",
    """      case 1: // QR WiFi
        menuOpen = false;
        currentScreen = SCREEN_QR_LOCAL;
        drawQRScreen(true);
        break;"""
)

with open(path, 'w', encoding='utf-8') as f:
    f.write(code)

print("Fixed orphan brace")
