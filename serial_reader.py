"""Reads COM5 + COM6 serial and writes live data to live/serial_data.json"""
import serial, threading, json, re, time

DATA_FILE = "live/serial_data.json"
data = {"us1": 0, "us2": 0, "us3": 0, "b2": 0, "b3": 0, "temp": 0, "hum": 0, "dompeur": "--:--", "lines": []}

def read_port(port):
    while True:
        try:
            ser = serial.Serial(port, 115200, timeout=1)
            print(f"Connected to {port}")
            while True:
                line = ser.readline().decode('utf-8', errors='replace').strip()
                if not line:
                    continue
                data["lines"] = (data["lines"] + [f"[{port}] {line}"])[-30:]
                m = re.search(r'US1[: ]+\s*(-?\d+)cm', line) or re.search(r'Bassin 1:\s*(-?\d+)cm', line)
                if m: data["us1"] = int(m.group(1))
                m = re.search(r'US2[: ]+\s*(-?\d+)cm', line) or re.search(r'Bassin 2:\s*(-?\d+)cm', line)
                if m: data["us2"] = int(m.group(1))
                m = re.search(r'US3[: ]+\s*(-?\d+)cm', line) or re.search(r'Bassin 3:\s*(-?\d+)cm', line)
                if m: data["us3"] = int(m.group(1))
                m = re.search(r'BLE CBM:.*B3=(\d+)cm', line)
                if m: data["b3"] = int(m.group(1))
                m = re.search(r'BLE CBM:.*B2=(\d+)cm', line)
                if m: data["b2"] = int(m.group(1))
                m = re.search(r'Temp:\s*([\d.]+)', line)
                if m: data["temp"] = float(m.group(1))
                m = re.search(r'Hum:\s*([\d.]+)', line)
                if m: data["hum"] = float(m.group(1))
                with open(DATA_FILE, 'w') as f:
                    json.dump(data, f)
        except Exception as e:
            print(f"{port}: {e} — retry in 3s")
            time.sleep(3)

threading.Thread(target=read_port, args=('COM5',), daemon=True).start()
threading.Thread(target=read_port, args=('COM6',), daemon=True).start()
print("Serial reader: COM5 + COM6")

while True:
    time.sleep(1)
