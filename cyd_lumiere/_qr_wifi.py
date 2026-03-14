path = r"C:\Users\ryb086\OneDrive - Groupe R.Y. Beaudoin\Bureau\CLAUDE_CODE\cyd_lumiere\src\main.cpp"
with open(path, 'r', encoding='utf-8') as f:
    code = f.read()

# 1. Replace QR Local with QR WiFi in menu label
code = code.replace(
    '"WiFi", "QR Local", "QR Remote"',
    '"WiFi", "QR WiFi", "QR Remote"'
)

# 2. Replace the QR Local screen title and URL
code = code.replace(
    'tft.drawString(isLocal ? "QR Local" : "QR Remote", SW / 2, 11);',
    'tft.drawString(isLocal ? "QR WiFi" : "QR Remote", SW / 2, 11);'
)

# 3. Replace the local URL with WiFi QR format
code = code.replace(
    'url = "http://" + WiFi.localIP().toString() + "/remote";',
    'url = "WIFI:T:WPA;S:Cabane Marcoux;P:Cabane2025;;";'
)

# 4. Remove the WiFi connected check for QR Local (WiFi QR doesn't need connection)
code = code.replace(
    """      case 1: // QR Local
        if (WiFi.status() == WL_CONNECTED) {
          menuOpen = false;
          currentScreen = SCREEN_QR_LOCAL;
          drawQRScreen(true);""",
    """      case 1: // QR WiFi
        menuOpen = false;
        currentScreen = SCREEN_QR_LOCAL;
        drawQRScreen(true);"""
)

# Find and fix the closing brace issue - remove the extra condition close
# Need to check what comes after the old block
with open(path, 'w', encoding='utf-8') as f:
    f.write(code)

print("QR WiFi Cabane Marcoux applied")
