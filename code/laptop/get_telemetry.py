import serial
import json
import time

PORT = "COM15"
BAUD = 57600

ser = serial.Serial(PORT, BAUD, timeout=1)

def read_telemetry():
    if ser.in_waiting:
        line = ser.readline()  # reads until \n or timeout
        if not line:
            return None
        try:
            data_str = line.decode('utf-8').strip()
            if not data_str:
                return None
            return json.loads(data_str)
        except (UnicodeDecodeError, json.JSONDecodeError) as e:
            print(f"Bad telemetry frame: {e} -- raw: {line!r}")
            return None
    return None

while True:
    telem = read_telemetry()
    if telem:
        print(telem)
    time.sleep(0.05)