"""
Fix NimBLE API - use correct class names from NimBLEScan.h:
- NimBLEAdvertisedDeviceCallbacks (not NimBLEScanCallbacks)
- setAdvertisedDeviceCallbacks (not setCallbacks)
- onResult(NimBLEAdvertisedDevice* device) no override keyword
"""

PATH = r"C:\Users\ryb086\OneDrive - Groupe R.Y. Beaudoin\Bureau\CLAUDE_CODE\cyd_lumiere\src\main.cpp"

with open(PATH, 'r', encoding='utf-8') as f:
    code = f.read()

code = code.replace(
    'class InkbirdScanCallback : public NimBLEScanCallbacks {',
    'class InkbirdScanCallback : public NimBLEAdvertisedDeviceCallbacks {'
)

code = code.replace(
    '  void onResult(NimBLEAdvertisedDevice* device) override {',
    '  void onResult(NimBLEAdvertisedDevice* device) {'
)

code = code.replace(
    'pScan->setCallbacks(&inkbirdCallback, false);',
    'pScan->setAdvertisedDeviceCallbacks(&inkbirdCallback, true);'
)

with open(PATH, 'w', encoding='utf-8') as f:
    f.write(code)

print("OK - NimBLE API corrigee v2")
print("- NimBLEAdvertisedDeviceCallbacks")
print("- setAdvertisedDeviceCallbacks(..., true=wantDuplicates)")
