path = r"C:\Users\ryb086\OneDrive - Groupe R.Y. Beaudoin\Bureau\CLAUDE_CODE\cyd_lumiere\src\main.cpp"
with open(path, 'r', encoding='utf-8') as f:
    code = f.read()

# 1. Move BLE init AFTER WiFi connection in setup, and add debug prints
old = '''  // BLE Inkbird init
  bleInitInkbird();

  // Web server routes'''

new = '''  // BLE init deferred — will start after WiFi connected
  // bleInitInkbird() called later in loop when WiFi is up

  // Web server routes'''

code = code.replace(old, new)

# 2. Add BLE lazy init in loop — init once when WiFi is connected
old = '''    bleScanInkbird();'''
new = '''    if (!bleInitDone) {
      Serial.println("BLE: init NimBLE...");
      bleInitInkbird();
      Serial.println("BLE: init done, first scan");
    }
    bleScanInkbird();'''

code = code.replace(old, new)

# 3. Add more serial debug in setup
old = '''  Serial.printf("Device ID: %s\n", deviceId.c_str());
  Serial.printf("MQTT topics: %s, %s\n", mqttTopicState.c_str(), mqttTopicCmd.c_str());'''

new = '''  Serial.printf("Device ID: %s\n", deviceId.c_str());
  Serial.flush();
  Serial.printf("MQTT topics: %s, %s\n", mqttTopicState.c_str(), mqttTopicCmd.c_str());
  Serial.flush();'''

code = code.replace(old, new)

with open(path, 'w', encoding='utf-8') as f:
    f.write(code)

print("BLE init deferred to after WiFi — serial debug added")
